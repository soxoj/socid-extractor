.. _development:

Development and internals
=========================

This page describes how ``socid_extractor`` is laid out on disk, how the test
suite is organised, and what the continuous-integration pipeline enforces. If
you are here to contribute a new extraction rule, start with
:doc:`adding-a-scheme` and use this page as the reference for testing and CI.

Package layout
--------------

All library code lives under ``socid_extractor/``. The repository root also
carries ``run.py``, a thin entry point that calls ``cli.run()`` so you can run
the tool without installing it.

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Module
     - Responsibility
   * - ``__init__.py``
     - Package version metadata; re-exports ``extract``, ``parse``,
       ``mutate_url`` and ``parse_cookies`` from ``main`` (``parse_cookies``
       ultimately comes from ``utils``).
   * - ``main.py``
     - ``HEADERS``, ``parse()``, ``mutate_url()``, ``extract()`` and the shared
       helpers ``transform()`` / ``map_fields()``. The central extraction
       pipeline.
   * - ``schemes.py``
     - Defines ``schemes`` — one dict entry per extraction method (site / API
       shape). Imports the shared helpers from ``utils`` (``from .utils import
       *``) so scheme lambdas can use them. This is the main place to add or
       change extraction rules.
   * - ``cli.py``
     - Argument parsing, logging setup, cookie loading, optional activation, and
       orchestration of ``parse`` / ``mutate_url`` / ``extract`` for ``--url``
       or ``--file``. The optional ``--skip-fetch-if-no-url-hint`` flag uses
       ``url_relevance``.
   * - ``url_relevance.py``
     - ``check_url_relevance(url)`` — substring hints from each scheme's optional
       ``url_hints`` plus tokens derived from the scheme name; used only by the
       CLI to skip HTTP when no hint matches.
   * - ``utils.py``
     - Cookie parsing and Netscape cookie-jar import, datetime helpers, URL
       enrichment, Facebook UID from graph URLs, Yandex avatar URLs, and string
       utilities used by schemes.
   * - ``activation.py``
     - Functions referenced by ``--activation`` that obtain tokens or headers
       (for example Twitter guest activation, Vimeo JWT) before the main
       request.
   * - ``postprocessor.py``
     - Classes such as ``Gravatar``, ``EmailToUsername`` and
       ``YandexUsernameToEmail``; listed in ``POSTPROCESSORS`` and run on every
       successful field dict after scheme extraction.
   * - ``__main__.py``
     - Delegates to ``cli.run()`` so ``python -m socid_extractor`` works.

Testing
-------

``tests/test_e2e.py`` is the main test suite. A test typically calls
``parse(url, ...)`` to fetch a live page, then ``extract(text)`` and asserts on
keys in the returned dict. Some tests pass custom ``headers`` or cookies.

**One end-to-end test per scheme.** Every extraction method — each named entry
in ``schemes`` in ``socid_extractor/schemes.py`` — should have at least one
end-to-end test in ``tests/test_e2e.py`` that exercises a real URL (or the
public JSON endpoint Maigret uses) and asserts on extracted fields.

- Add the test in the same commit as a new or changed scheme when possible.
- Name the test function ``test_<something>_e2e`` or follow the existing
  ``test_<site>`` pattern.
- In the test **docstring**, put the exact scheme name(s) from ``schemes.py``,
  one per line. ``revision.py`` uses this docstring-to-scheme-name link to
  associate tests with methods when it regenerates ``METHODS.md``.

Where a live call is too flaky, add a fast offline check in a small module test
(for example ``tests/test_socid_improvements.py`` with a saved HTML/JSON
snippet) *in addition* to the e2e policy, not as a substitute for it.

Cookie-based scenarios may use files under ``tests/`` (for example
``*.cookies``). The default CI run excludes tests whose names match ``cookies``
via ``-k 'not cookies'``.

Pytest markers
~~~~~~~~~~~~~~

Markers are defined in ``pyproject.toml`` under ``[tool.pytest.ini_options]``.

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Marker
     - Meaning
   * - ``github_failed``
     - Requests from GitHub Actions CI servers are blocked (blocks, geo, and
       similar). Excluded in CI.
   * - ``rate_limited``
     - Anti-bot, captcha, or rate limiting from the site. Excluded in CI.
   * - ``requires_cookies``
     - Cookies are required to get content. Documented for selective runs.

If a site blocks GitHub Actions, mark the test ``@pytest.mark.github_failed`` or
``@pytest.mark.rate_limited`` and document why — the test still counts locally
and for coverage intent, and CI simply excludes it with
``-m 'not github_failed and not rate_limited'``.

Installing test/dev extras
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All test, lint, type-check and format tools are declared in ``pyproject.toml``
under ``[project.optional-dependencies]``.

.. code-block:: bash

   # minimal: pytest + pytest-rerunfailures + pytest-xdist
   pip install '.[test]'

   # everything above + flake8 + mypy + black
   pip install '.[dev]'

CI installs the ``[dev]`` extra.

Running the suite locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python3 -m pytest tests/test_e2e.py -n 10 -k 'not cookies' -m 'not github_failed and not rate_limited'

- ``-n 10`` runs the suite across parallel workers using **pytest-xdist**
  (shipped in the ``[test]`` / ``[dev]`` extra). Omit ``-n 10`` if you did not
  install xdist.
- The ``-k`` and ``-m`` filters match what CI runs, with the added parallelism
  for speed.

``tests/reformat.sh`` is a helper script that turns lines of the form
``key: value`` into ``assert info.get("key") == "value"`` patterns in
``test_e2e.py`` (macOS ``sed`` syntax). Use it after pasting CLI output into the
test file.

revision.py
-----------

Run ``revision.py`` from the repository root:

.. code-block:: bash

   python revision.py

It regenerates ``METHODS.md`` from the tests and schemes. Specifically, it:

- reads the pytest marker descriptions from ``pyproject.toml``;
- loads the tests from ``tests/test_e2e.py`` and the schemes from
  ``socid_extractor/schemes.py``;
- associates tests with scheme names via the test docstrings (one method name
  per line) or heuristic name matching;
- overwrites ``METHODS.md`` with a table of methods, test links, and notes
  (markers, skip reasons); and
- prints how many methods have no matching test.

Keep the docstrings in your tests aligned with the scheme names in ``schemes``
when you want accurate coverage reporting.

Continuous integration
----------------------

``.github/workflows/python-package.yml`` runs on pushes and pull requests to
``master``. It installs the ``[dev]`` extra and runs across Python **3.10,
3.11, 3.12, 3.13 and 3.14**.

- **flake8** is the only hard gate. CI runs ``flake8 --select=E9,F63,F7,F82``,
  so only real syntax errors and undefined names fail the build; a separate
  warning-only pass reports complexity and line length.
- **mypy** runs as ``mypy socid_extractor/`` (with stub overrides in
  ``[[tool.mypy.overrides]]``).
- **pytest** runs ``pytest -k 'not cookies' -m 'not github_failed and not
  rate_limited' --reruns 3 --reruns-delay 30``, using pytest-rerunfailures to
  absorb flaky network tests.

Publishing to PyPI on release is handled separately by
``.github/workflows/python-publish.yml`` using ``python -m build``.

Code style
----------

``pyproject.toml`` configures three tools. All three live in the ``[dev]``
extra so contributors can run them locally, but none is a hard CI gate except
flake8's error set (``E9,F63,F7,F82``).

.. list-table::
   :header-rows: 1
   :widths: 14 30 56

   * - Tool
     - Config
     - What it does
   * - **flake8**
     - ``[tool.flake8]`` (``ignore = E501``)
     - Style plus obvious bugs. Line length (``E501``) is ignored project-wide;
       CI gates only on ``--select=E9,F63,F7,F82``.
   * - **mypy**
     - ``[tool.mypy]``
     - Static typing, applied gradually (``disallow_untyped_defs = false``).
   * - **black**
     - ``[tool.black]`` (``line-length = 127``)
     - Optional formatter; matches the 127-character line length used elsewhere.
