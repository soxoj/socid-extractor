# How to contribute

You can easily add any site or platform to socid_extractor.

Take a look at [wiki page with instructions](https://github.com/soxoj/socid-extractor/wiki/How-to-add-site) (WIP)
and study [naming convention for fields](https://github.com/soxoj/socid-extractor/wiki/List-of-main-fields).

It will be better to make test in the same commit. You can do it the following way:
1. Add extraction rule to `socid_extractor/schemes.py`.
2. Run `./run.py --url URL` and copy output (lines of format `fields: value`).
3. Add new test function to `tests/test_e2e.py`, paste your output there and save file.
4. Run `cd tests && reformat.sh` to prepare assertions, and check that the test is running successfully.

And don't forget to update the table with methods by the script `./revision.py`!
