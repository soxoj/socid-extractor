# Architecture

## Overview

`socid_extractor` turns a page body (HTML or JSON-in-text) into a flat dictionary of string fields (IDs, usernames, links, etc.). Matching is driven by a large dict named `schemes` in [`socid_extractor/schemes.py`](../socid_extractor/schemes.py). The core loop lives in [`socid_extractor/main.py`](../socid_extractor/main.py).

## Data flow

1. **`parse(url, ...)`** — Performs an HTTP GET with default browser-like headers (see `HEADERS` in `main.py`), optional cookie string, optional extra headers, and configurable timeout. Returns `(page_text, status_code)`.

2. **`mutate_url(url)`** (optional, used by the CLI) — Scans every scheme’s optional `url_mutations` list. Each mutation has a `from` regex (with named groups) and a `to` format string. If the URL matches, additional request URLs are produced (e.g. Twitter web URL → GraphQL API URL). The CLI may issue several requests: the original URL plus each mutation, merging activation headers per request.

3. **`extract(page)`** — Pure function over the response body string. It does not fetch URLs. It walks `schemes` **in dict iteration order**. If `flags` match but regexp/JSON extraction fails, that scheme is skipped and the next one is tried. The first scheme that matches `flags` and completes its extraction path returns a dict (possibly empty after filtering). If nothing matches, it returns `{}`.

## Scheme matching

Each scheme entry is a Python dict. Typical keys:

| Key | Role |
| --- | ---- |
| `flags` | **Required.** Substrings that must all appear in `page` for this scheme to be considered. |
| `regex` | Optional. If present, `re.search(..., page, re.MULTILINE)` is used. |
| `extract_json` | If true, the first capture group is parsed as JSON (after optional `transforms`), then `fields` lambdas receive the parsed object. |
| `transforms` | Optional list of callables applied in order to the string capture before `json.loads` or `map_fields` (depending on branch). |
| `fields` | Dict mapping output field names to callables. For JSON path: `lambda obj: ...`. For BeautifulSoup: `lambda soup: ...`. |
| `bs` | If present with `fields`, BeautifulSoup is used (`parser_type` defaults to `html.parser`). |
| `url_mutations` | Not used inside `extract`; only consumed by `mutate_url`. |
| `message` | Optional log line when the scheme is detected. |

**Regexp branch**

- If the regex has **named groups** (`groupdict` non-empty), those names and values populate `values` (stringified where needed).
- Otherwise capture **group 1** is passed through `transform` then `map_fields` when `fields` is defined.
- With **`extract_json`**, group 1 is transformed, then `json.loads`, then `map_fields(scheme_data, json_data)`.

**HTML branch**

- If `bs` is set, `BeautifulSoup(page, parser_type)` is built and each `fields[name](soup)` runs. This can run **after** the regexp branch in the same scheme, so both may contribute to `values`.

## Post-processing

After building `values`, every class in [`POSTPROCESSORS`](../socid_extractor/postprocessor.py) is instantiated with `values` and `process()` is called; returned dicts are merged into `values` (e.g. Gravatar enrichment, email-derived usernames). Errors in transforms, field extraction, or post-processors are caught (`AttributeError`, `KeyError`, `IndexError`, `TypeError`), logged at debug, and skipped.

The final return value drops entries whose values are “empty” unless the value is a `bool`:  
`{k: v for k, v in values.items() if v or type(v) == bool}`.

## CLI ([`cli.py`](../socid_extractor/cli.py))

- **`--url`** — Fetches with `parse` (timeout 10 in CLI), optionally after `mutate_url`.
- **`--cookies` / `--cookie-jar`** — Merged into a cookie string for `parse`.
- **`--file`** — Reads a local file and passes its contents to `extract` only (no HTTP).
- **`--activation`** — Calls a named function from [`activation.py`](../socid_extractor/activation.py) (e.g. guest token flows) to adjust cookies/headers before the request.

## Public API ([`__init__.py`](../socid_extractor/__init__.py))

Exports `extract`, `parse`, `mutate_url`, and `parse_cookies` (cookie string → dict, implemented in [`utils.py`](../socid_extractor/utils.py) and re-exported via `main`).

## Debug behavior

With logging at `DEBUG`, successful JSON extraction may write `debug_extracted.json` to the current working directory.
