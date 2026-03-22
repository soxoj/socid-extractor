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
