.. _adding-a-scheme:

Adding a scheme
===============

Adding a new site is intentionally low-friction: most schemes are 5–15 lines of
declarative config plus one end-to-end test. A scheme declares which response
bodies it recognises (``flags``), how to pull structured data out of them
(``regex`` or ``extract_json``), and how to name the values it produces
(``fields``). Nothing is compiled or registered by hand — you add a dict entry
and a test, and the extractor picks it up.

If you would rather ship your scheme outside the main repository, see
:doc:`plugins`. For the surrounding pipeline (how ``parse``, ``mutate_url`` and
``extract`` fit together), see :doc:`how-extraction-works`.

TL;DR
-----

1. Add a scheme to ``socid_extractor/schemes.py`` (regex- or JSON-based).
2. Use field names from the ontology (see :doc:`ontology`) — do not invent new
   ones if a standard exists.
3. Write a real-URL e2e test in ``tests/test_e2e.py``.
4. Run ``./revision.py`` to regenerate ``METHODS.md``.
5. Open a PR.

Add a scheme
------------

Schemes live in ``socid_extractor/schemes.py`` as entries in the ``schemes``
dict. Each entry has at minimum:

.. list-table::
   :header-rows: 1
   :widths: 20 12 68

   * - Key
     - Required
     - Purpose
   * - ``flags``
     - yes
     - Substrings that **all** must appear in the response body for this scheme
       to match. The only gate — there is no URL check at extraction time.
   * - ``regex`` **or** ``extract_json``
     - yes
     - How to pull data from the matched body.
   * - ``fields``
     - yes
     - Mapping of output field names → lambdas that compute the value.
   * - ``url_hints``
     - recommended
     - Tuple of URL substrings. Used by the CLI flag
       ``--skip-fetch-if-no-url-hint`` so batch users don't pay the HTTP cost on
       URLs that obviously can't match. Add this for any scheme whose target
       domain isn't already obvious from the scheme name.

Look at neighbouring schemes (GitHub, GitLab, Facebook group) for concrete
templates.

A full annotated scheme
~~~~~~~~~~~~~~~~~~~~~~~~~

The GitHub API scheme is a compact, complete example. It fetches
``https://api.github.com/users/{username}``, treats the body as JSON, and maps
the JSON keys onto ontology field names:

.. code-block:: python

   # https://api.github.com/users/torvalds
   'GitHub API': {
       # CLI-only: lets --skip-fetch-if-no-url-hint avoid HTTP on
       # URLs that can't belong to this site.
       'url_hints': ('api.github.com', 'github.com'),

       # Both substrings must be present in the body for the scheme to
       # match. These are structural keys the GitHub user API always
       # returns — see "Writing robust flags" below.
       'flags': ['gists_url', 'received_events_url'],

       # Applied to the body first. With extract_json, the captured group
       # is the JSON string that gets parsed.
       'regex': r'^({[\S\s]+?})$',
       'extract_json': True,

       # Rewrites a human profile URL into the API endpoint before the
       # request is made (CLI only — see the caveat below).
       'url_mutations': [
           {
               'from': r'^https?://(?:www\.)?github\.com/(?P<username>[^/?#]+)/?$',
               'to': 'https://api.github.com/users/{username}',
           }
       ],

       # Each lambda receives the parsed JSON object (x) and returns a
       # value. Keys use ontology names (see :doc:`ontology`).
       'fields': {
           'uid': lambda x: x.get('id'),
           'image': lambda x: x.get('avatar_url'),
           'created_at': lambda x: x.get('created_at'),
           'location': lambda x: x.get('location'),
           'follower_count': lambda x: x.get('followers'),
           'following_count': lambda x: x.get('following'),
           'fullname': lambda x: x.get('name'),
           'public_gists_count': lambda x: x.get('public_gists'),
           'public_repos_count': lambda x: x.get('public_repos'),
           'twitter_username': lambda x: x.get('twitter_username'),
           'is_looking_for_job': lambda x: x.get('hireable'),
           'gravatar_id': lambda x: x.get('gravatar_id'),
           'bio': lambda x: x['bio'].strip() if x.get('bio', '') else None,
           'company': lambda x: x.get('company'),
           'blog_url': lambda x: x.get('blog'),
       }
   }

When ``extract_json`` is set, the ``regex`` captures the JSON text, it is parsed
once, and every ``fields`` lambda receives the resulting object. When it is
**not** set, the body is matched with a named-group regex and each lambda
receives the ``re.Match`` group dict instead. The neighbouring *Facebook group*
scheme is the regex-with-named-groups variant — it has no ``extract_json`` and
pulls ``username`` and ``uid`` straight out of the pattern:

.. code-block:: python

   'Facebook group': {
       'url_hints': ('facebook.com', 'fb.com'),
       'flags': ['com.facebook.katana', 'XPagesProfileHomeController'],
       'regex': r'{"imp_id":".+?","ef_page":.+?,"uri":".+?\/(?P<username>[^\/]+?)","entity_id":"(?P<uid>\d+)"}',
   }

.. note::

   ``url_mutations`` (URL rewriting) is a CLI convenience only. Library and
   Maigret callers pass an already-fetched page straight to ``extract()`` and
   never trigger the rewrite. Do not rely on it in a scheme that must work when
   called as a library.

Writing robust flags
---------------------

``flags`` are the only thing standing between your scheme and false positives on
unrelated sites. ``extract()`` returns on the **first** matching scheme, so a
too-generic flag can shadow the correct one and produce garbage output.

**Rules:**

1. **At least one flag must be unique to the platform.**
   Good: ``'OK.startupData'``, ``'canonicalPeriscopeUrl'``,
   ``'data-initial-data='``.
   Bad: ``'"data"'``, ``'"user"'``, ``'"username"'`` — match any JSON API.
2. **Prefer structural API field names** that only this site returns:
   ``'"allowCrawler"'`` (Wattpad), ``'"dateJoined"'`` + ``'"socialMediaLinks"'``
   (Hashnode), ``'"creatorTraders"'`` (Manifold). These survive redesigns.
3. **Never use a single short JSON key as the only flag.** ``'{"username":"'``
   alone matches dozens of APIs — always pair it with a second
   platform-specific flag.
4. **For HTML pages, use CSS class names or page-specific markers** instead of
   generic tags: ``'osu-layout'``, ``'ProfileHeader_lblMemberName'``,
   ``'Aedu.User.set_viewed('``.
5. **For RSC / escaped JSON**, remember flags check the raw response body.
   Strings appear as ``\"field_name\"``, not ``"field_name"``. Prefer
   unescaped markers from the surrounding HTML (``'op.gg/lol/summoners/'``).
6. **Flags must not depend on user data.** Don't use the username, display name,
   or any value that varies between accounts — use structural API keys / HTML
   markers instead.
7. **Test against 5–10 unrelated sites' responses** before submitting. Run
   ``maigret USER --site "YourSite" -vvv`` and check ``debug.log`` for false
   triggers. A scheme that fires once for its target and zero times for others
   is correct.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Good flag
     - Why
   * - ``'data-initial-data='``
     - HTML attribute unique to osu!
   * - ``'"profilesData.profileUser"'``
     - JS variable unique to GOG
   * - ``'"allowCrawler"'``
     - JSON field unique to Wattpad
   * - ``'"dateJoined"', '"socialMediaLinks"'``
     - Two fields unique to Hashnode
   * - ``'Music Profile | Last.fm</title>'``
     - Title tag with site name

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Bad flag
     - Problem
   * - ``'"data"'``
     - Matches any JSON
   * - ``'"user"'``
     - Matches any user API
   * - ``'{"username":"'``
     - Matches any JSON with username
   * - ``'__NEXT_DATA__'`` (alone)
     - Matches any Next.js site

Field naming
------------

Field names come from the project's field ontology — the standard names
(``username``, ``fullname``, ``created_at``, ``is_verified``,
``follower_count``, …) used across all schemes so downstream pipelines don't
need one mapping per site. Read :doc:`ontology` before naming fields.

- Use the existing standard name when one fits — do **not** invent variants.
  Common mistakes: ``verified`` → use ``is_verified``; ``joined`` /
  ``registration`` → use ``created_at``; ``followers_count`` → use
  ``follower_count`` (singular noun + ``_count``).
- The ``name`` API field is ambiguous — map it to ``fullname`` if it's a display
  name, or ``username`` if it's a handle.
- Only create a platform-specific field (with a prefix like ``osu_pp``,
  ``gog_games_owned``) when the data genuinely doesn't fit any standard
  category.
- Boolean flags use the ``is_*`` prefix and are stringified (``'True'`` /
  ``'False'``).

If you think a new standard field is warranted, propose adding it to the
ontology in the same PR.

Write the e2e test
------------------

Every new scheme requires at least one e2e test in ``tests/test_e2e.py`` against
a real URL or API response. Unit tests with inline fixtures (in
``tests/test_socid_improvements.py``) are also welcome but do not replace e2e
coverage.

Workflow
~~~~~~~~

1. Run the extractor against the target URL and capture its output. The output
   is one ``field: value`` per line:

   .. code-block:: console

      ./run.py --url https://example.com/users/alice

2. Add a new test function to ``tests/test_e2e.py`` and paste those lines into
   its body:

   .. code-block:: python

      def test_example():
          """Example scheme name"""
          info = extract(parse('https://example.com/users/alice')[0])
          # paste the field: value lines from step 1 here, then run reformat.sh

3. Convert the pasted lines into assertions. ``reformat.sh`` rewrites each
   ``field: value`` line into ``assert info.get("field") == "value"``:

   .. code-block:: console

      cd tests && ./reformat.sh

4. Run the test:

   .. code-block:: console

      python3 -m pytest tests/test_e2e.py -k test_example -v

Test docstring — used by ``revision.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Put the **scheme name(s)** from ``schemes.py`` in the test docstring, one per
line. ``revision.py`` matches tests to schemes via this docstring to generate
``METHODS.md``. If a single test covers two schemes (e.g. an HTML page plus the
JSON API for the same site), list both:

.. code-block:: python

   def test_stack_overflow():
       """
       Stack Overflow
       Stack Overflow API
       """
       ...

Test fixtures with HTML
~~~~~~~~~~~~~~~~~~~~~~~~

If your test asserts against parsed HTML (display names, bios containing
punctuation), copy the **exact** characters from the real response — including
HTML entities like ``&#064;`` instead of ``@``. Tests that silently "fix"
entities pass against fixtures and fail against the live site.

Flaky / blocked sites
~~~~~~~~~~~~~~~~~~~~~~~

If the site is unreliable from CI, mark the test:

- ``@pytest.mark.github_failed`` — GitHub Actions IPs are blocked by the site.
- ``@pytest.mark.rate_limited`` — anti-bot / captcha / rate limiting.
- ``@pytest.mark.requires_cookies`` — cookies are required to get content.

Running the suite
~~~~~~~~~~~~~~~~~~

First install the test extras (or ``[dev]`` for the full set used by CI):

.. code-block:: console

   pip install '.[test]'   # or '.[dev]'

Then:

.. code-block:: console

   python3 -m pytest tests/test_e2e.py -n 10 -k 'not cookies' -m 'not github_failed and not rate_limited'

Update METHODS.md
-----------------

After your scheme and test are in, regenerate the public methods table and
commit the result in the same PR:

.. code-block:: console

   ./revision.py

PR checklist
------------

- [ ] Scheme added to ``socid_extractor/schemes.py`` with ``url_hints`` if
  applicable.
- [ ] Flags are platform-specific (passes the false-positive test against
  unrelated sites).
- [ ] Field names follow the ontology; platform-specific fields use a prefix.
- [ ] e2e test added to ``tests/test_e2e.py`` hitting a real URL/API.
- [ ] Test docstring lists the scheme name(s).
- [ ] ``./revision.py`` re-run and ``METHODS.md`` updated.
- [ ] Test passes locally: ``pytest tests/test_e2e.py -k <your_test>``.

See also
--------

- :doc:`ontology` — standard field names; read before naming fields.
- :doc:`how-extraction-works` — the pipeline your scheme plugs into.
- :doc:`plugins` — shipping schemes via the external plugins repo.
- :doc:`development` — environment setup, tests, and CI.
