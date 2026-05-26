# Contributing to socid_extractor

Thanks for your interest! Adding a new site is intentionally low-friction: most schemes are 5–15 lines of declarative config plus an e2e test.

---

## TL;DR

1. Add a scheme to `socid_extractor/schemes.py` (regex- or JSON-based).
2. Use field names from [**FIELDS.md**](FIELDS.md) — do not invent new ones if a standard exists.
3. Write a real-URL e2e test in `tests/test_e2e.py`.
4. Run `./revision.py` to regenerate `METHODS.md`.
5. Open a PR.

---

## 1. Add a scheme

Schemes live in [`socid_extractor/schemes.py`](socid_extractor/schemes.py) as entries in the `schemes` dict. Each entry has at minimum:

| Key | Required | Purpose |
|-----|----------|---------|
| `flags` | yes | Substrings that **all** must appear in the response body for this scheme to match. The only gate — there is no URL check at extraction time. |
| `regex` **or** `extract_json` | yes | How to pull data from the matched body. |
| `fields` | yes | Mapping of output field names → lambdas that compute the value. |
| `url_hints` | recommended | Tuple of URL substrings. Used by the CLI flag `--skip-fetch-if-no-url-hint` so batch users don't pay the HTTP cost on URLs that obviously can't match. **Add this for any scheme whose target domain isn't already obvious from the scheme name.** |

Look at neighbouring schemes (GitHub, Patreon, Hashnode) for concrete templates.

### Writing robust `flags`

`flags` are the only thing standing between your scheme and false positives on unrelated sites. `extract()` returns on the **first** matching scheme, so a too-generic flag can shadow the correct one and produce garbage output.

**Rules:**

1. **At least one flag must be unique to the platform.**
   Good: `'OK.startupData'`, `'canonicalPeriscopeUrl'`, `'data-initial-data='`.
   Bad: `'"data"'`, `'"user"'`, `'"username"'` — match any JSON API.
2. **Prefer structural API field names** that only this site returns:
   `'"allowCrawler"'` (Wattpad), `'"dateJoined"'` + `'"socialMediaLinks"'` (Hashnode), `'"creatorTraders"'` (Manifold). These survive redesigns.
3. **Never use a single short JSON key as the only flag.** `'{"username":"'` alone matches dozens of APIs — always pair it with a second platform-specific flag.
4. **For HTML pages, use CSS class names or page-specific markers** instead of generic tags: `'osu-layout'`, `'ProfileHeader_lblMemberName'`, `'Aedu.User.set_viewed('`.
5. **For RSC / escaped JSON**, remember flags check the raw response body. Strings appear as `\"field_name\"`, not `"field_name"`. Prefer unescaped markers from the surrounding HTML (`'op.gg/lol/summoners/'`).
6. **Flags must not depend on user data.** Don't use the username, display name, or any value that varies between accounts — use structural API keys / HTML markers instead.
7. **Test against 5–10 unrelated sites' responses** before submitting. Run `maigret USER --site "YourSite" -vvv` and check `debug.log` for false triggers. A scheme that fires once for its target and zero times for others is correct.

| ✅ Good flag | Why |
|-------------|-----|
| `'data-initial-data='` | HTML attribute unique to osu! |
| `'"profilesData.profileUser"'` | JS variable unique to GOG |
| `'"allowCrawler"'` | JSON field unique to Wattpad |
| `'"dateJoined"', '"socialMediaLinks"'` | Two fields unique to Hashnode |
| `'Music Profile \| Last.fm</title>'` | Title tag with site name |

| ❌ Bad flag | Problem |
|------------|---------|
| `'"data"'` | Matches any JSON |
| `'"user"'` | Matches any user API |
| `'{"username":"'` | Matches any JSON with username |
| `'__NEXT_DATA__'` (alone) | Matches any Next.js site |

### Field naming — use [FIELDS.md](FIELDS.md)

`FIELDS.md` is the field ontology: standard names (`username`, `fullname`, `created_at`, `is_verified`, `follower_count`, …) used across all schemes so downstream pipelines don't need 130 mappings.

**Rules:**

- Use the existing standard name when one fits — do **not** invent variants. Common mistakes: `verified` → use `is_verified`; `joined`/`registration` → use `created_at`; `followers_count` → use `follower_count` (singular noun + `_count`).
- The `name` API field is ambiguous — map it to `fullname` if it's a display name, or `username` if it's a handle.
- Only create a platform-specific field (with a prefix like `osu_pp`, `gog_games_owned`) when the data genuinely doesn't fit any standard category.
- Boolean flags use the `is_*` prefix and are stringified (`'True'` / `'False'`).

If you think a new standard field is warranted, propose adding it to `FIELDS.md` in the same PR.

---

## 2. Write the e2e test

**Every new scheme requires at least one e2e test in `tests/test_e2e.py` against a real URL or API response.** Unit tests with inline fixtures (in `tests/test_socid_improvements.py`) are also welcome but do not replace e2e coverage.

### Workflow

1. Run the extractor against the target URL and capture its output:
   ```sh
   ./run.py --url https://example.com/users/alice
   ```
   The output is one `field: value` per line.

2. Add a new test function to `tests/test_e2e.py`:
   ```python
   def test_example():
       """Example scheme name"""
       info = extract(parse('https://example.com/users/alice')[0])
       # paste the field: value lines from step 1 here, then run reformat.sh
   ```

3. Convert the pasted lines into assertions:
   ```sh
   cd tests && ./reformat.sh
   ```
   This rewrites `field: value` lines into `assert info.get("field") == "value"`.

4. Run the test:
   ```sh
   python3 -m pytest tests/test_e2e.py -k test_example -v
   ```

### Test docstring — used by `revision.py`

Put the **scheme name(s)** from `schemes.py` in the test docstring, one per line. `revision.py` matches tests to schemes via this docstring to generate `METHODS.md`. If a single test covers two schemes (e.g. HTML page + JSON API for the same site), list both:

```python
def test_stack_overflow():
    """
    Stack Overflow
    Stack Overflow API
    """
    ...
```

### Test fixtures with HTML

If your test asserts against parsed HTML (display names, bios containing punctuation), copy the **exact** characters from the real response — including HTML entities like `&#064;` instead of `@`. Tests that silently "fix" entities pass against fixtures and fail against the live site.

### Flaky / blocked sites

If the site is unreliable from CI, mark the test:

- `@pytest.mark.github_failed` — GitHub Actions IPs are blocked by the site.
- `@pytest.mark.rate_limited` — anti-bot / captcha / rate limiting.
- `@pytest.mark.requires_cookies` — cookies are required to get content.

See [`docs/testing-and-ci.md`](docs/testing-and-ci.md) for details.

### Running the suite

First, install the test extras (pytest + pytest-rerunfailures + pytest-xdist) — or `[dev]` for the full set used by CI (adds flake8 / mypy / black):

```sh
pip install '.[test]'   # or '.[dev]'
```

Then:

```sh
python3 -m pytest tests/test_e2e.py -n 10 -k 'not cookies' -m 'not github_failed and not rate_limited'
```

---

## 3. Update `METHODS.md`

After your scheme + test are in, regenerate the public methods table:

```sh
./revision.py
```

Commit the resulting `METHODS.md` change in the same PR.

---

## 4. Open the PR

Checklist before submitting:

- [ ] Scheme added to `socid_extractor/schemes.py` with `url_hints` if applicable
- [ ] Flags are platform-specific (passes the false-positive test against unrelated sites)
- [ ] Field names follow [FIELDS.md](FIELDS.md); platform-specific fields use a prefix
- [ ] e2e test added to `tests/test_e2e.py` hitting a real URL/API
- [ ] Test docstring lists the scheme name(s)
- [ ] `./revision.py` re-run and `METHODS.md` updated
- [ ] Test passes locally: `pytest tests/test_e2e.py -k <your_test>`

---

## Further reading

- [FIELDS.md](FIELDS.md) — field ontology (read this before naming fields).
- [docs/architecture.md](docs/architecture.md) — high-level design.
- [docs/modules.md](docs/modules.md) — package layout.
- [docs/testing-and-ci.md](docs/testing-and-ci.md) — markers, cookies, CI quirks.
- [docs/plugins.md](docs/plugins.md) — adding schemes via the external plugins repo.
