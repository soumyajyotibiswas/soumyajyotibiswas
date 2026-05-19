#!/usr/bin/env python3
"""Refresh the generated project block in the profile README."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

START_MARKER = "<!-- profile-projects:start -->"
END_MARKER = "<!-- profile-projects:end -->"
GITHUB_API = "https://api.github.com"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update README.md featured projects from GitHub repository metadata."
    )
    parser.add_argument("--readme", default="README.md", help="README file to update.")
    parser.add_argument(
        "--config",
        default=".github/profile-readme.config.json",
        help="JSON config with repo ordering, exclusions, and copy overrides.",
    )
    parser.add_argument("--username", help="GitHub username to scan.")
    parser.add_argument(
        "--repos-json",
        help="Optional local JSON file containing repo metadata, useful for tests.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use configured featured repos only; do not call the GitHub API.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated project block without writing README.md.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def github_request(url: str) -> tuple[list[dict[str, Any]], str | None]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "profile-readme-refresh",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload, response.headers.get("Link")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"GitHub API request failed: {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"GitHub API request failed: {exc.reason}") from exc


def has_next_page(link_header: str | None) -> bool:
    if not link_header:
        return False
    return any('rel="next"' in part for part in link_header.split(","))


def fetch_repos(username: str) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    page = 1
    while True:
        url = (
            f"{GITHUB_API}/users/{username}/repos"
            f"?type=owner&sort=updated&per_page=100&page={page}"
        )
        payload, link_header = github_request(url)
        repos.extend(payload)
        if not has_next_page(link_header):
            return repos
        page += 1


def topic_names(raw: dict[str, Any]) -> list[str]:
    topics = raw.get("topics") or raw.get("repositoryTopics") or []
    names: list[str] = []
    for topic in topics:
        if isinstance(topic, str):
            names.append(topic)
        elif isinstance(topic, dict) and topic.get("name"):
            names.append(str(topic["name"]))
    return names


def primary_language(raw: dict[str, Any]) -> str:
    language = raw.get("language") or raw.get("primaryLanguage")
    if isinstance(language, dict):
        return str(language.get("name") or "")
    return str(language or "")


def normalize_repo(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": raw.get("name", ""),
        "description": raw.get("description") or "",
        "url": raw.get("html_url") or raw.get("url") or "",
        "language": primary_language(raw),
        "topics": topic_names(raw),
        "fork": bool(raw.get("fork") or raw.get("isFork")),
        "archived": bool(raw.get("archived") or raw.get("isArchived")),
        "updated_at": raw.get("updated_at") or raw.get("updatedAt") or "",
        "pushed_at": raw.get("pushed_at") or raw.get("pushedAt") or "",
    }


def configured_repos(config: dict[str, Any]) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    username = config.get("username", "")
    for entry in config.get("featured_repos", []):
        name = entry.get("name", "")
        repos.append(
            {
                "name": name,
                "description": entry.get("summary", ""),
                "url": f"https://github.com/{username}/{name}" if username and name else "",
                "language": "",
                "topics": [],
                "fork": False,
                "archived": False,
                "updated_at": "",
                "pushed_at": "",
            }
        )
    return repos


def load_repos(args: argparse.Namespace, config: dict[str, Any], username: str) -> list[dict[str, Any]]:
    if args.repos_json:
        payload = json.loads(Path(args.repos_json).read_text(encoding="utf-8"))
        return [normalize_repo(repo) for repo in payload]
    if args.offline:
        return configured_repos(config)
    return [normalize_repo(repo) for repo in fetch_repos(username)]


def overrides_by_name(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["name"]: entry for entry in config.get("featured_repos", []) if entry.get("name")}


def project_score(repo: dict[str, Any], overrides: dict[str, dict[str, Any]]) -> tuple[int, str]:
    if repo["name"] in overrides:
        names = list(overrides.keys())
        return (0, f"{names.index(repo['name']):03d}")
    pushed = repo.get("pushed_at") or repo.get("updated_at") or ""
    return (1, "".join(chr(255 - ord(char)) for char in pushed))


def select_projects(
    repos: list[dict[str, Any]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    exclude = {name.lower() for name in config.get("exclude_repos", [])}
    overrides = overrides_by_name(config)
    candidates = [
        repo
        for repo in repos
        if repo["name"]
        and repo["name"].lower() not in exclude
        and not repo["fork"]
        and not repo["archived"]
        and (repo["description"] or repo["name"] in overrides)
    ]
    candidates.sort(key=lambda repo: project_score(repo, overrides))
    return candidates[: int(config.get("max_projects", 4))]


def link(label: str, url: str) -> str:
    escaped_label = table_cell(label)
    return f"[{escaped_label}]({url})" if url else escaped_label


def table_cell(value: str) -> str:
    return " ".join(str(value).split()).replace("|", "\\|")


def summary_for(repo: dict[str, Any], override: dict[str, Any] | None) -> str:
    return str((override or {}).get("summary") or repo["description"]).strip()


def signals_for(
    repo: dict[str, Any], override: dict[str, Any] | None, config: dict[str, Any]
) -> list[str]:
    if override and override.get("signals"):
        return [str(signal) for signal in override["signals"]]

    signals: list[str] = []
    if repo.get("language"):
        signals.append(f"{repo['language']} implementation")

    text = " ".join(
        [
            repo.get("name", ""),
            repo.get("description", ""),
            " ".join(repo.get("topics", [])),
        ]
    ).lower()
    for keyword, signal in config.get("signal_keywords", {}).items():
        if keyword.lower() in text and signal not in signals:
            signals.append(signal)

    if repo.get("topics"):
        signals.extend(repo["topics"][:2])

    return signals[:6] or ["documented project workflow"]


def links_for(repo: dict[str, Any], override: dict[str, Any] | None) -> str:
    configured = (override or {}).get("links") or []
    links = [link(item.get("label", "Link"), item.get("url", "")) for item in configured]
    if not links and repo.get("url"):
        links.append(link("Repo", repo["url"]))
    return "<br>".join(links)


def render_projects(projects: list[dict[str, Any]], config: dict[str, Any]) -> str:
    overrides = overrides_by_name(config)
    lines = [
        START_MARKER,
        "| Project | What It Is | Engineering Signals | Write-up |",
        "| ------- | ---------- | ------------------- | -------- |",
    ]
    for repo in projects:
        override = overrides.get(repo["name"])
        project_link = link(repo["name"], repo.get("url", ""))
        summary = table_cell(summary_for(repo, override))
        signals = table_cell(", ".join(signals_for(repo, override, config)))
        writeup = links_for(repo, override)
        lines.append(f"| {project_link} | {summary} | {signals}. | {writeup} |")
    lines.append(END_MARKER)
    return "\n".join(lines)


def replace_block(readme: str, block: str) -> str:
    if START_MARKER not in readme or END_MARKER not in readme:
        raise SystemExit(
            f"README is missing {START_MARKER} / {END_MARKER}; add markers before running."
        )
    before, rest = readme.split(START_MARKER, 1)
    _, after = rest.split(END_MARKER, 1)
    return before.rstrip() + "\n\n" + block + after


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_json(config_path)
    username = args.username or config.get("username")
    if not username:
        raise SystemExit("Set username in config or pass --username.")

    repos = load_repos(args, config, username)
    projects = select_projects(repos, config)
    block = render_projects(projects, config)

    readme_path = Path(args.readme)
    current = readme_path.read_text(encoding="utf-8")
    updated = replace_block(current, block)

    if args.dry_run:
        print(block)
        if current == updated:
            print("\nREADME.md is already up to date.", file=sys.stderr)
        else:
            print("\nREADME.md would change.", file=sys.stderr)
        return 0

    if current == updated:
        print("README.md is already up to date.")
        return 0

    readme_path.write_text(updated, encoding="utf-8")
    print(f"Updated {readme_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
