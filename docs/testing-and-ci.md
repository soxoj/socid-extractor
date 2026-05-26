# Testing and CI

## End-to-end tests

[`tests/test_e2e.py`](../tests/test_e2e.py) is the main test suite. Tests typically call `parse(url, ...)` to fetch a live page, then `extract(text)` and assert on keys in the returned dict. Some tests pass custom `headers` or cookies.

### Policy: one e2e test per site / scheme

Every **extraction method** (each named entry in `schemes` in [`schemes.py`](../socid_extractor/schemes.py)) should have **at least one** end-to-end test in `tests/test_e2e.py` that exercises a real URL (or the public JSON endpoint Maigret uses) and asserts on extracted fields.

- Add the test in the **same commit** as a new or changed scheme when possible (see [CONTRIBUTING.md](../CONTRIBUTING.md)).
- Name the test function `test_<something>_e2e` or follow the existing `test_<site>` pattern.
- In the **docstring**, put the **exact scheme name(s)** from `schemes.py` (one per line) so [`revision.py`](../revision.py) can link tests to methods in [`METHODS.md`](../METHODS.md).
- If a site blocks GitHub Actions (captchas, geo, bot walls), mark the test `@pytest.mark.github_failed` or `@pytest.mark.rate_limited` and document why — the test still counts for local runs and for coverage intent; CI uses `-m 'not github_failed and not rate_limited'`.

Where a live call is too flaky, add a **fast offline check** in a small module test (e.g. [`tests/test_socid_improvements.py`](../tests/test_socid_improvements.py) with a saved HTML/JSON snippet) *in addition* to the e2e policy above, not as a full substitute.

Cookie-based scenarios may use files under [`tests/`](../tests/) (e.g. `*.cookies`); the default CI run **excludes** tests whose names match `cookies` (see below).

## Pytest markers

Defined in [`pyproject.toml`](../pyproject.toml) (`[tool.pytest.ini_options]`):

| Marker | Meaning |
| ------ | ------- |
| `github_failed` | Request or site behavior often fails from GitHub Actions runners (blocks, geo, etc.). Excluded in CI. |
| `rate_limited` | Anti-bot, captcha, or rate limits. Excluded in CI. |
| `requires_cookies` | Needs authenticated cookies. Documented for selective runs. |

Use `@pytest.mark.skip` for temporarily broken tests; reasons appear in `revision.py` output when regenerating `METHODS.md`.

## Installing the test/dev dependencies

All test, lint, type-check and format tools are declared in [`pyproject.toml`](../pyproject.toml) under `[project.optional-dependencies]`:

```sh
# minimal: pytest + pytest-rerunfailures + pytest-xdist
pip install '.[test]'

# everything above + flake8 + mypy + black
pip install '.[dev]'
```

CI uses `pip install '.[dev]'` — see [`.github/workflows/python-package.yml`](../.github/workflows/python-package.yml).

## Local commands

From the [root README](../README.md):

```sh
python3 -m pytest tests/test_e2e.py -n 10 -k 'not cookies' -m 'not github_failed and not rate_limited'
```

- **`-n 10`** — parallel workers via **pytest-xdist** (shipped in the `[test]` / `[dev]` extra). Omit `-n 10` if you did not install xdist.
- Filters match what CI runs, plus optional parallelism for speed.

## `tests/reformat.sh`

Helper script that turns lines of the form `key: value` into `assert info.get("key") == "value"` patterns in `test_e2e.py` (macOS `sed` syntax). Use after pasting CLI output into the test file as documented in [CONTRIBUTING.md](../CONTRIBUTING.md).

## GitHub Actions

[`.github/workflows/python-package.yml`](../.github/workflows/python-package.yml) runs on pushes and pull requests to `master`:

- Python **3.10, 3.11, 3.12, 3.13, 3.14**
- **flake8** — syntax/undefined-name checks; complexity/length as warnings. Config in `pyproject.toml` (`[tool.flake8]`) ignores `E501` (line length).
- **mypy** — type checking with `mypy socid_extractor/` (stub overrides in `[[tool.mypy.overrides]]`)
- **pytest** — `pytest -k 'not cookies' -m 'not github_failed and not rate_limited' --reruns 3 --reruns-delay 30` (pytest-rerunfailures for flaky network tests)

Publishing to PyPI on release is handled by [`.github/workflows/python-publish.yml`](../.github/workflows/python-publish.yml) using `python -m build`.

## `revision.py`

Run from the repository root:

```sh
python revision.py
```

It:

- Reads pytest marker descriptions from `pyproject.toml`
- Loads tests from `tests/test_e2e.py` and schemes from `socid_extractor/schemes.py`
- Associates tests with scheme names via docstrings (method name per line) or heuristic name matching
- **Overwrites [`METHODS.md`](../METHODS.md)** with a table of methods, test links, and notes (markers, skip reasons)
- Prints how many methods have no matching test

Keep docstrings in tests aligned with scheme names in `schemes` when you want accurate coverage reporting.

## Code style

[`pyproject.toml`](../pyproject.toml) configures three tools; none of them is enforced as a CI gate (flake8 is the only one that can fail the build, and only on syntax / undefined-name errors), but they're all in the `[dev]` extra so contributors can run them locally:

| Tool | Config | What it does |
| ---- | ------ | ------------ |
| **flake8** | `[tool.flake8]` (`ignore = E501`) | Style + obvious bugs. CI runs `flake8 --select=E9,F63,F7,F82` as a build gate. |
| **mypy** | `[tool.mypy]` | Static typing. `disallow_untyped_defs = false` — gradual. |
| **black** | `[tool.black]` (`line-length = 127`) | Optional formatter; matches CI's `--max-line-length=127`. |
