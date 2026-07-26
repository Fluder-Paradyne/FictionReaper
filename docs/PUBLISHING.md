# Publishing FictionReaper to PyPI

Package name: **`fictionreaper`** (checked free as of setup).  
Version: see `pyproject.toml` / `fictionreaper.__version__`.

## Recommended: Trusted Publishing (no API token in CI)

### 1. Create a PyPI account

1. Sign up: https://pypi.org/account/register/
2. Verify email, enable **2FA** (required for publishing).

### 2. Register a Trusted Publisher (pending project)

1. Open: https://pypi.org/manage/account/publishing/
2. Under **Add a new pending publisher**, fill in:

   | Field | Value |
   |-------|--------|
   | PyPI Project Name | `fictionreaper` |
   | Owner | `Fluder-Paradyne` |
   | Repository name | `FictionReaper` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

3. Submit.

Optional TestPyPI: https://test.pypi.org/manage/account/publishing/ with the same fields (separate account/login is fine; many people use the same GitHub identity).

### 3. GitHub Environment

Repo → **Settings → Environments → `pypi`**  
(Already created if you used the setup script; otherwise create it named exactly `pypi`.)

No secrets needed for Trusted Publishing.

### 4. Publish a version

**Option A — GitHub Release (production)**

```bash
git tag -a v0.1.0 -m "v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0" --generate-notes
```

That triggers `.github/workflows/publish.yml` → `uv publish`.

**Option B — Manual workflow**

GitHub → **Actions → Publish to PyPI → Run workflow** → choose `pypi` or `testpypi`.

### 5. Verify

```bash
pip index versions fictionreaper
uvx fictionreaper --version
# or
pipx install fictionreaper
fictionreaper --version
```

## Alternative: API token (local machine)

1. PyPI → Account → **API tokens** → create token (scope: entire account or project).
2. Publish:

```bash
cd FictionReaper
uv build
uv publish --token pypi-AgEIcHlwaS5vcmc...
```

Prefer env var (never commit the token):

```bash
export UV_PUBLISH_TOKEN='pypi-...'
uv publish
```

## Version bumps

1. Update version in `pyproject.toml` and `src/fictionreaper/__init__.py`
2. Commit, tag `vX.Y.Z`, push tag, create Release
3. CI publishes

## Users install after publish

```bash
pip install fictionreaper
uv tool install fictionreaper
pipx install fictionreaper
```
