# Releasing tokcodec

Releases are cut by pushing a tag. The workflow in `.github/workflows/release.yml`
checks versions, runs tests, publishes to PyPI, then npm, then creates the
GitHub Release with notes from `CHANGELOG.md`. No tokens are stored anywhere:
both registries use trusted publishing (OIDC).

## One-time setup

### PyPI

1. Go to https://pypi.org/manage/account/publishing/ and add a **pending
   publisher** (the project does not exist yet, so it must be "pending"):
   - PyPI project name: `tokcodec`
   - Owner: `lnxinc`
   - Repository: `tokcodec`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
2. In the GitHub repo: Settings → Environments → New environment → `pypi`.
   Optionally add yourself as a required reviewer so a tag push waits for a click.

### npm

(Done for 0.1.0 on 2026-09-02; trusted publishing is configured. Kept for reference.)

1. Create the package once by hand so trusted publishing can be attached to it:
   ```bash
   cd npm && npm login && npm publish --access public
   ```
   (Or skip this and publish the first version from the workflow with a
   granular automation token in `NPM_TOKEN`; then switch to trusted publishing.)
2. On https://www.npmjs.com/package/tokcodec/access → **Trusted publisher**:
   - Publisher: GitHub Actions
   - Organization or user: `lnxinc`
   - Repository: `tokcodec`
   - Workflow filename: `release.yml`
   - Environment name: `npm`
3. In the GitHub repo: Settings → Environments → New environment → `npm`.
4. Require 2FA and disallow tokens for publishing on the package settings page
   once trusted publishing works, so nothing but this workflow can publish.

### GitHub

Settings → Actions → General → Workflow permissions: "Read and write" is not
needed globally; the release job requests `contents: write` itself.

## Cutting a release

1. Bump the version in all four places (CI fails if they disagree):
   `pyproject.toml`, `npm/package.json`, `tokcodec/__init__.py`,
   `.claude-plugin/plugin.json`. `uv run python scripts/check_versions.py`.
2. Move the `[Unreleased]` items in `CHANGELOG.md` under a new
   `## [X.Y.Z] - YYYY-MM-DD` heading. The release notes are extracted from that
   section verbatim.
3. Commit, then:
   ```bash
   git tag vX.Y.Z && git push origin main vX.Y.Z
   ```
4. Watch the Release workflow. PyPI must succeed before npm runs, because the
   npm launcher pins `tokcodec@X.Y.Z` on PyPI. The npm step skips itself if that
   version is already on the registry.
5. `scripts/cold-test.sh --published`. Always test the npm path *through `npx`*,
   not by running `bin/tokcodec.js` directly: 0.1.0 shipped a launcher that recursed
   into its own npx shim, and only the real `npx` path reproduces that.

## Verifying from cold

After the tag ships, from machines that have nothing installed:

```bash
docker run --rm python:3.12-slim bash -lc "pip install -q uv && uvx tokcodec why /etc/hosts"
docker run --rm node:22-slim bash -lc "npx -y tokcodec why /etc/hosts"      # no Python in this image
docker run --rm node:22-slim bash -lc "npx -y tokcodec install --dry-run"
```

`scripts/cold-test.sh` runs these three against the *local* source tree before
publishing, using the launcher's `TOKCODEC_PYTHON_SPEC` override.
