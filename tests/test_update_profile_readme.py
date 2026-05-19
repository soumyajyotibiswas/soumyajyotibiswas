from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "update_profile_readme.py"


def load_updater():
    spec = importlib.util.spec_from_file_location("update_profile_readme", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ProfileReadmeUpdaterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.updater = load_updater()

    def test_replaces_only_marked_project_block(self) -> None:
        readme = "\n".join(
            [
                "# Profile",
                "",
                "Before",
                self.updater.START_MARKER,
                "old table",
                self.updater.END_MARKER,
                "After",
            ]
        )
        block = "\n".join(
            [
                self.updater.START_MARKER,
                "new table",
                self.updater.END_MARKER,
            ]
        )

        updated = self.updater.replace_block(readme, block)

        self.assertIn("Before", updated)
        self.assertIn("new table", updated)
        self.assertIn("After", updated)
        self.assertNotIn("old table", updated)

    def test_requires_generated_block_markers(self) -> None:
        with self.assertRaises(SystemExit):
            self.updater.replace_block("# Profile\n", "replacement")

    def test_project_selection_skips_excluded_forks_and_archives(self) -> None:
        config = {
            "max_projects": 4,
            "exclude_repos": ["profile"],
            "featured_repos": [{"name": "featured"}],
        }
        repos = [
            {"name": "profile", "description": "skip", "fork": False, "archived": False},
            {"name": "forked", "description": "skip", "fork": True, "archived": False},
            {"name": "old", "description": "skip", "fork": False, "archived": True},
            {"name": "featured", "description": "", "fork": False, "archived": False},
            {"name": "normal", "description": "include", "fork": False, "archived": False},
        ]

        selected = self.updater.select_projects(repos, config)

        self.assertEqual(["featured", "normal"], [repo["name"] for repo in selected])

    def test_rendered_table_escapes_untrusted_markdown_cells(self) -> None:
        config = {
            "featured_repos": [
                {
                    "name": "demo",
                    "summary": "safe | summary\nnext line",
                    "signals": ["one | two", "three\nfour"],
                    "links": [{"label": "Docs | notes", "url": "https://example.test/docs"}],
                }
            ]
        }
        repos = [
            {
                "name": "demo",
                "description": "fallback",
                "url": "https://example.test/demo",
                "language": "Python",
                "topics": [],
                "fork": False,
                "archived": False,
            }
        ]

        rendered = self.updater.render_projects(repos, config)

        self.assertIn("safe \\| summary next line", rendered)
        self.assertIn("one \\| two, three four.", rendered)
        self.assertIn("[Docs \\| notes](https://example.test/docs)", rendered)

    def test_offline_cli_updates_readme_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            readme = tmp / "README.md"
            config = tmp / "config.json"
            readme.write_text(
                "\n".join(
                    [
                        "# Profile",
                        "",
                        self.updater.START_MARKER,
                        "old",
                        self.updater.END_MARKER,
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            config.write_text(
                json.dumps(
                    {
                        "username": "example",
                        "featured_repos": [
                            {
                                "name": "demo",
                                "summary": "Demo project",
                                "signals": ["tested automation"],
                                "links": [{"label": "Repo", "url": "https://example.test/demo"}],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            first = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--readme",
                    str(readme),
                    "--config",
                    str(config),
                    "--offline",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            second = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--readme",
                    str(readme),
                    "--config",
                    str(config),
                    "--offline",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("Updated", first.stdout)
            self.assertIn("already up to date", second.stdout)


class WorkflowSecurityTests(unittest.TestCase):
    def test_ci_workflow_is_read_only(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("contents: write", workflow)

    def test_refresh_workflow_tests_before_commit(self) -> None:
        workflow = (
            REPO_ROOT / ".github" / "workflows" / "profile-readme-refresh.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("permissions:\n  contents: write", workflow)
        self.assertLess(workflow.index("Run tests"), workflow.index("Commit README changes"))


if __name__ == "__main__":
    unittest.main()
