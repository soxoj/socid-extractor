# Package modules

Layout under [`socid_extractor/`](../socid_extractor/):

| Module | Responsibility |
| ------ | ---------------- |
| [`__init__.py`](../socid_extractor/__init__.py) | Package version metadata; re-exports `extract`, `parse`, `mutate_url`, `parse_cookies` from `main` (and `parse_cookies` ultimately comes from `utils`). |
| [`main.py`](../socid_extractor/main.py) | `HEADERS`, `parse()`, `mutate_url()`, `extract()`, shared helpers `transform()` / `map_fields()`. Central extraction pipeline. |
| [`schemes.py`](../socid_extractor/schemes.py) | Defines `schemes` — one dict entry per extraction method (site/API shape). Imports shared helpers from `utils` (`from .utils import *`) so scheme lambdas can use them. This file is the main place to add or change extraction rules. |
| [`cli.py`](../socid_extractor/cli.py) | Argument parsing, logging setup, cookie loading, optional activation, orchestration of `parse` / `mutate_url` / `extract` for `--url` or `--file`; optional `--skip-fetch-if-no-url-hint` uses `url_relevance`. |
| [`url_relevance.py`](../socid_extractor/url_relevance.py) | `check_url_relevance(url)` — substring hints from each scheme’s optional `url_hints` plus tokens derived from the scheme name; used only by the CLI to skip HTTP when no hint matches. |
| [`utils.py`](../socid_extractor/utils.py) | Cookie parsing and Netscape cookie jar import, datetime helpers, URL enrichment, Facebook UID from graph URLs, Yandex avatar URLs, string utilities used by schemes. |
| [`activation.py`](../socid_extractor/activation.py) | Functions referenced by `--activation` that obtain tokens or headers (e.g. Twitter guest activation, Vimeo JWT) before the main request. |
| [`postprocessor.py`](../socid_extractor/postprocessor.py) | Classes such as `Gravatar`, `EmailToUsername`, `YandexUsernameToEmail`; listed in `POSTPROCESSORS` and run on every successful field dict after scheme extraction. |
| [`__main__.py`](../socid_extractor/__main__.py) | Delegates to `cli.run()` so `python -m socid_extractor` works. |

Repository root also has [`run.py`](../run.py), which calls `cli.run()` for running without installation.

## Adding a new site or method

1. Add or extend an entry in `schemes` in [`schemes.py`](../socid_extractor/schemes.py) (`flags`, and either `regex`/`fields` or `bs`/`fields`, plus optional `transforms`, `extract_json`, `url_mutations`).
2. Add an end-to-end test in [`tests/test_e2e.py`](../tests/test_e2e.py) and use pytest markers when needed (see [testing-and-ci.md](testing-and-ci.md)).
3. Regenerate the methods table with [`revision.py`](../revision.py) (updates [`METHODS.md`](../METHODS.md)).

Field naming and workflow details are in [CONTRIBUTING.md](../CONTRIBUTING.md) and the [project wiki](https://github.com/soxoj/socid-extractor/wiki).
