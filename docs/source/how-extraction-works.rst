.. _how-extraction-works:

How extraction works
====================

This page explains the extractor principle: how a raw page body is turned into
a flat dictionary of fields, and how the core loop in ``socid_extractor/main.py``
decides which scheme to apply.

Overview
--------

``socid_extractor`` takes a page body — HTML, or JSON embedded in text — and
turns it into a flat dictionary of string fields (IDs, usernames, links, dates,
and so on). All matching is driven by a single large dictionary named
``schemes`` in ``socid_extractor/schemes.py``. Each entry describes one site (or
one response shape for a site): what substrings prove the page belongs to it,
and how to pull fields out of it.

The core loop lives in ``socid_extractor/main.py``. It walks ``schemes``, finds
the first entry that fits the page, runs that entry's extraction path, applies a
few post-processors, and returns the resulting dict. If no scheme fits, it
returns ``{}``.

To add your own site, see :doc:`adding-a-scheme`. For the naming rules the
output fields follow, see :doc:`ontology`.

Data flow
---------

There are three top-level functions, and only one of them touches the network:

.. list-table::
   :header-rows: 1

   * - Function
     - Role
   * - ``parse(url, cookies_str='', timeout=3, headers={})``
     - Performs an HTTP GET with browser-like ``HEADERS``, optional cookies,
       optional extra headers, and a timeout. Returns ``(page_text,
       status_code)``. This is the only network step.
   * - ``mutate_url(url)``
     - Optional, CLI-only. Scans every scheme's ``url_mutations`` list; for each
       mutation whose ``from`` regex matches the URL, produces a new request URL
       from the ``to`` format string, together with any per-mutation headers.
       Returns a list of ``(url, headers)`` pairs.
   * - ``extract(page, use_ai_fallback=False)``
     - Pure over the page string — it does no HTTP fetch of its own. It runs the
       scheme matching loop against the in-memory body and returns the field
       dict.

A typical call sequence is ``parse()`` to fetch the body, optionally
``mutate_url()`` to derive additional request URLs, then ``extract()`` on each
fetched body. Library callers that already have a page body can call
``extract()`` directly. See :doc:`library-usage` for examples.

Scheme anatomy
--------------

Each scheme is a Python dict. Only ``flags`` is always required; the remaining
keys select and configure the extraction path.

.. list-table::
   :header-rows: 1

   * - Key
     - Role
   * - ``flags``
     - **Required.** A list of substrings that must *all* appear in the page for
       the scheme to be considered. Acts as a cheap detection gate.
   * - ``regex``
     - Optional. A pattern searched with ``re.search(..., page, re.MULTILINE)``.
       Selects the regexp extraction branch.
   * - ``extract_json``
     - Optional flag. When true, the regex's first capture group is treated as a
       JSON string: it is transformed, then ``json.loads``-ed, and the parsed
       object is fed to the ``fields`` callables.
   * - ``transforms``
     - Optional list of callables applied in order to the captured string,
       before ``json.loads`` (JSON path) or before ``fields`` (plain path).
   * - ``fields``
     - Dict mapping output field names to callables. On the JSON path each
       callable receives the parsed object (``lambda obj: ...``); on the HTML
       path each receives the parsed soup (``lambda soup: ...``).
   * - ``bs`` / ``parser_type``
     - When ``bs`` is present, the page is parsed with BeautifulSoup and each
       ``fields`` callable runs against the soup. ``parser_type`` picks the
       parser and defaults to ``html.parser``.
   * - ``url_mutations``
     - Consumed only by ``mutate_url`` (CLI). Ignored inside ``extract``.
   * - ``url_hints``
     - Optional substrings used only by the CLI's ``check_url_relevance`` URL
       pre-check (see ``url_relevance.py``). Ignored inside ``extract``. Useful
       when the site's domain is not obvious from the scheme name.
   * - ``message``
     - Optional line logged when the scheme is detected.

The matching loop
-----------------

``_extract_by_schemes(page)`` walks ``schemes`` in **dict iteration order** and
applies this logic to each entry:

1. **Flags are a substring gate.** ``all(flag in page for flag in flags)`` must
   be true. If any flag is missing, the scheme is skipped immediately.
2. **First complete match wins.** When the flags match, the scheme's extraction
   path runs. The **first** scheme whose flags match *and* whose extraction
   completes is returned.
3. **Failed extraction skips the scheme.** If the flags match but the regex
   fails to find anything (or JSON parsing yields ``{}``), that scheme is
   abandoned and the loop moves on to the next one — a flag match alone is not
   enough to stop the search.
4. **Nothing matches → ``{}``.** If the loop reaches the end without a scheme
   completing, ``extract`` returns an empty dict.

Because matching is ordered and first-wins, more specific schemes should appear
before more generic ones in ``schemes.py``.

The regexp branch
~~~~~~~~~~~~~~~~~~

Selected when the scheme has a ``regex`` key. The pattern is searched with
``re.MULTILINE``. If there is no match, the scheme is skipped.

**Named groups.** If the match has named groups (a non-empty ``groupdict``),
those names and values populate the ``values`` dict directly — no ``fields``
mapping is used. A named group ending in ``_raw`` is written to the field with
the suffix stripped (group ``foo_raw`` populates field ``foo``). Existing values
are not overwritten, so an already-set field keeps its first value.

**Single group + fields.** If there are no named groups, capture ``group(1)`` is
passed through ``transforms`` and then ``map_fields`` maps it onto ``fields``.

**JSON.** With ``extract_json`` set, ``group(1)`` is transformed, parsed with
``json.loads``, and the resulting object is passed to ``map_fields``. A parse
result of ``{}`` causes the scheme to be skipped.

The HTML branch
~~~~~~~~~~~~~~~~

Selected when the scheme has a ``bs`` key. The page is parsed once with
``BeautifulSoup(page, parser_type)`` and each ``fields[name](soup)`` callable
runs against the soup, writing its return value into ``values``.

The HTML branch runs **after** the regexp branch within the same scheme, so a
scheme that declares both a ``regex`` and ``bs`` can have both branches
contribute to the same ``values`` dict.

Post-processing
---------------

After ``values`` is built, every class in ``POSTPROCESSORS`` (from
``socid_extractor/postprocessor.py``) is instantiated with ``values`` and its
``process()`` method is called; the returned dict is merged back into
``values``. The processors run in list order:

.. list-table::
   :header-rows: 1

   * - Post-processor
     - What it adds or fixes
   * - ``StripInvalidGravatarUrls``
     - Blanks bare ``gravatar.com`` homepage URLs mistaken for avatars.
   * - ``Gravatar``
     - Derives ``gravatar_url``, ``gravatar_username`` and
       ``gravatar_email_md5_hash`` from an ``image`` field.
   * - ``EmailToUsername``
     - For any ``*email*`` field containing ``@``, adds a ``*_username`` field
       from the local part.
   * - ``YandexUsernameToEmail``
     - When a Yandex id and a ``username`` are present, derives an ``email``.
   * - ``NormalizeDates``
     - Converts human-readable date fields to ``YYYY-MM-DD HH:MM:SS UTC``.

Errors raised inside transforms, field callables, or post-processors are caught
against ``PROCESS_ERRORS`` (``AttributeError``, ``KeyError``, ``IndexError``,
``TypeError``), logged at debug level, and skipped — a single failing field does
not abort the whole extraction.

Final shaping
-------------

Before returning, the ``values`` dict is filtered and cleaned:

.. code-block:: python

   {k: html.unescape(v) if isinstance(v, str) else v
    for k, v in values.items() if v or type(v) == bool}

- Empty values are dropped, **unless** the value is a ``bool`` (so ``False`` is
  preserved).
- String values are ``html.unescape``-d, so ``&#064;`` becomes ``@``.
- If anything survives, a ``_extractor`` key is added carrying the name of the
  scheme that produced the result.

Debug output
------------

With the root logger at ``DEBUG`` level, successful JSON extraction writes the
pretty-printed parsed object to ``debug_extracted.json`` in the current working
directory. Field failures, transform errors, and post-processor errors are also
emitted at debug level, which is the fastest way to see why a matching scheme
produced fewer fields than expected.

When ``extract(page, use_ai_fallback=True)`` is used and no scheme produces a
result, extraction falls back to an LLM-based extractor. See :doc:`ai-fallback`.
