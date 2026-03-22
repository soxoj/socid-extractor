# Testing and CI

## End-to-end tests

[`tests/test_e2e.py`](../tests/test_e2e.py) is the main test suite. Tests typically call `parse(url, ...)` to fetch a live page, then `extract(text)` and assert on keys in the returned dict. Some tests pass custom `headers` or cookies.

Cookie-based scenarios may use files under [`tests/`](../tests/) (e.g. `*.cookies`); the default CI run **excludes** tests whose names match `cookies` (see below).

## Pytest markers

Defined in [`pytest.ini`](../pytest.ini):

| Marker | Meaning |
| ------ | ------- |
| `github_failed` | Request or site behavior often fails from GitHub Actions runners (blocks, geo, etc.). Excluded in CI. |
| `rate_limited` | Anti-bot, captcha, or rate limits. Excluded in CI. |
| `requires_cookies` | Needs authenticated cookies. Documented for selective runs. |

Use `@pytest.mark.skip` for temporarily broken tests; reasons appear in `revision.py` output when regenerating `METHODS.md`.

## Local commands

From the [root README](../README.md):

```sh
python3 -m pytest tests/test_e2e.py -n 10 -k 'not cookies' -m 'not github_failed and not rate_limited'
```

- **`-n 10`** — Requires **pytest-xdist** (listed in [`test-requirements.txt`](../test-requirements.txt)) for parallel workers. Omit `-n 10` if you did not install xdist.
- Filters match what CI runs, plus optional parallelism for speed.

Minimal dependency set for tests is in `test-requirements.txt` (pytest, rerun plugin, xdist). Runtime library deps remain in [`requirements.txt`](../requirements.txt).

## `tests/reformat.sh`

Helper script that turns lines of the form `key: value` into `assert info.get("key") == "value"` patterns in `test_e2e.py` (macOS `sed` syntax). Use after pasting CLI output into the test file as documented in [CONTRIBUTING.md](../CONTRIBUTING.md).

## GitHub Actions

[`.github/workflows/python-package.yml`](../.github/workflows/python-package.yml) runs on pushes and pull requests to `master`:

- Python **3.10, 3.11, 3.12**
- **flake8** — syntax/undefined-name checks; complexity/length as warnings (`setup.cfg` ignores `E501` for line length)
- **pytest** — `pytest -k 'not cookies' -m 'not github_failed and not rate_limited' --reruns 3 --reruns-delay 30` (pytest-rerunfailures for flaky network tests)

Publishing to PyPI on release is handled by [`.github/workflows/python-publish.yml`](../.github/workflows/python-publish.yml).

## `revision.py`

Run from the repository root:

```sh
python revision.py
```

It:

- Reads pytest marker descriptions from `pytest.ini`
- Loads tests from `tests/test_e2e.py` and schemes from `socid_extractor/schemes.py`
- Associates tests with scheme names via docstrings (method name per line) or heuristic name matching
- **Overwrites [`METHODS.md`](../METHODS.md)** with a table of methods, test links, and notes (markers, skip reasons)
- Prints how many methods have no matching test

Keep docstrings in tests aligned with scheme names in `schemes` when you want accurate coverage reporting.

## Flake8

[`setup.cfg`](../setup.cfg) configures flake8 with `ignore = E501` (line length). CI still runs additional flake8 passes as defined in the workflow file.
