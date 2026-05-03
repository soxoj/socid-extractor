# How to contribute

You can easily add any site or platform to socid_extractor.

Take a look at [wiki page with instructions](https://github.com/soxoj/socid-extractor/wiki/How-to-add-site) (WIP)
and study [naming convention for fields](https://github.com/soxoj/socid-extractor/wiki/List-of-main-fields).

It will be better to make test in the same commit. You can do it the following way:
1. Add extraction rule to `socid_extractor/schemes.py`. For sites whose domain does not appear in the scheme name, add optional `url_hints` (tuple of substrings) so CLI users can use `--skip-fetch-if-no-url-hint` without missing your method.
2. Run `./run.py --url URL` and copy output (lines of format `fields: value`).
3. Add new test function to `tests/test_e2e.py`, paste your output there and save file.
4. Run `cd tests && reformat.sh` to prepare assertions, and check that the test is running successfully.

**End-to-end coverage:** each scheme (site/method) in `schemes.py` should have **at least one** e2e test in `tests/test_e2e.py` against a real URL or API response. Put the scheme name(s) in the test docstring (one per line) for `revision.py`. If the site is unreliable from CI, use `@pytest.mark.github_failed` or `rate_limited` (see [`docs/testing-and-ci.md`](docs/testing-and-ci.md)).

And don't forget to update the table with methods by the script `./revision.py`!

## Writing robust `flags`

`flags` are substrings that **all** must appear in the response body for a scheme to
match. They are the only gate — there is no URL check at extraction time.
If flags are too generic, the scheme will fire on responses from unrelated sites
and either produce garbage output or shadow the correct scheme (since `extract()`
returns on the **first** match).

### Rules

1. **At least one flag must be unique to the platform.** Good examples:
   `'OK.startupData'`, `'canonicalPeriscopeUrl'`, `'data-initial-data='`.
   Bad: `'"data"'`, `'"user"'`, `'"username"'` — these match any JSON API.

2. **Prefer structural API field names** that only this site returns:
   `'"allowCrawler"'` (Wattpad), `'"dateJoined"'` + `'"socialMediaLinks"'` (hashnode),
   `'"creatorTraders"'` (Manifold). These survive redesigns.

3. **Never use a single short JSON key as the only flag.**
   `'{"username":"'` alone matches dozens of APIs. Add a second flag that is
   specific to the platform.

4. **For HTML pages, use CSS class names or page-specific markers** instead of
   generic tags: `'osu-layout'`, `'ProfileHeader_lblMemberName'`,
   `'Aedu.User.set_viewed('`.

5. **For RSC / escaped JSON**, remember that flags check the raw response body.
   Strings appear as `\"field_name\"`, not `"field_name"`. Prefer unescaped
   markers from the surrounding HTML (`'op.gg/lol/summoners/'`).

6. **Test your flags against 5–10 other sites' responses** (run
   `maigret USER --site "YourSite" -vvv` and check `debug.log` for false
   triggers). A scheme that fires once for its target and zero times for
   others is correct.

### Quick checklist

| Good flag | Why |
|-----------|-----|
| `'data-initial-data='` | HTML attribute unique to osu! |
| `'"profilesData.profileUser"'` | JS variable unique to GOG |
| `'"allowCrawler"'` | JSON field unique to Wattpad API |
| `'"dateJoined"', '"socialMediaLinks"'` | Two fields unique to hashnode |
| `'Music Profile \| Last.fm</title>'` | Title tag with site name |

| Bad flag | Problem |
|----------|---------|
| `'"data"'` | Matches any JSON |
| `'"user"'` | Matches any user API |
| `'{"username":"'` | Matches any JSON with username |
| `'__NEXT_DATA__'` (alone) | Matches any Next.js site |

### Field naming

Use standard names from [`FIELDS.md`](FIELDS.md). Platform-specific fields get
a platform prefix (`osu_pp`, `gog_games_owned`). See FIELDS.md for the complete
ontology.
