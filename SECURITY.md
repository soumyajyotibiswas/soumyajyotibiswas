# Security

This profile repository should stay safe to publish.

## Boundaries

- Do not commit secrets, tokens, private keys, `.env` files, browser data, credential stores, or production credentials.
- Keep automation metadata-only. The README refresher reads public GitHub repository metadata and local configuration only.
- Keep GitHub Actions permissions minimal. The CI workflow is read-only; the README refresh workflow requests `contents: write` only so it can commit README changes.
- Run tests before changing generated README behavior.

## Local Checks

```bash
python3 -m json.tool .github/profile-readme.config.json
python3 -m py_compile scripts/update_profile_readme.py
python3 -m unittest discover -v
python3 scripts/update_profile_readme.py --offline --dry-run
```

The online refresh path uses the GitHub API and may use `GITHUB_TOKEN` for rate limits. The script must not print or persist that token.
