.. _library-usage:

Python library API
==================

``socid_extractor`` is a plain Python library: you hand it the text of a
profile page or API response and it hands back a flat dictionary of
:doc:`ontology` fields. Nothing in the parsing path touches the network, so
you stay in full control of how pages are fetched.

Install and import
------------------

.. code-block:: bash

   pip install socid-extractor

.. code-block:: python

   import socid_extractor

The package exports four public names:
:func:`extract`, :func:`parse`, :func:`parse_cookies`, and
:func:`mutate_url`.

extract
-------

.. code-block:: python

   extract(page, use_ai_fallback=False)

``extract`` is a **pure function over a response body string** — it never
fetches anything. You pass in already-downloaded page text (HTML or an API
response), and it tries each built-in scheme in turn until one matches.

- On a match it returns a **flat dict of** :doc:`ontology` **fields** (for
  example ``username``, ``fullname``, ``created_at``, ``is_verified``), plus
  an ``_extractor`` key naming the scheme that matched.
- When nothing matches it returns ``{}``.

.. code-block:: python

   import requests
   import socid_extractor

   r = requests.get('https://www.patreon.com/annetlovart')
   print(socid_extractor.extract(r.text))
   # {'patreon_id': '33913189', 'patreon_username': 'annetlovart',
   #  'fullname': 'Annet Lovart',
   #  'links': "['https://www.facebook.com/322598031832479', ...]",
   #  '_extractor': 'Patreon user profile'}

Because the input is just a string, you can feed ``extract`` a page from any
source — a live request, a saved fixture, an archive snapshot, or a proxy.

Set ``use_ai_fallback=True`` to opt into the LLM-based fallback when no scheme
matches. This is off by default and requires the optional ``[ai]`` extra; see
:doc:`ai-fallback` for details.

.. code-block:: python

   socid_extractor.extract(page, use_ai_fallback=True)

parse
-----

.. code-block:: python

   parse(url, cookies_str='', timeout=3, headers={}) -> (page_text, status_code)

``parse`` is the convenience fetcher bundled with the library. It issues a
GET request with browser-like default headers, follows redirects, and applies
any cookies you supply, then returns a ``(page_text, status_code)`` tuple.

.. list-table::
   :header-rows: 1

   * - Argument
     - Default
     - Meaning
   * - ``url``
     - *(required)*
     - The URL to fetch.
   * - ``cookies_str``
     - ``''``
     - Raw cookie header string, parsed via :func:`parse_cookies`.
   * - ``timeout``
     - ``3``
     - Seconds, applied to both connect and read timeouts.
   * - ``headers``
     - ``{}``
     - Extra headers merged on top of the built-in browser-like defaults.

The common pattern is to take the page text (element ``0`` of the tuple) and
pipe it straight into :func:`extract`:

.. code-block:: python

   from socid_extractor import parse, extract

   info = extract(parse('https://www.patreon.com/annetlovart')[0])
   print(info)

If you need cookies (for example on Google endpoints), pass them as a string:

.. code-block:: python

   page, status = parse(url, cookies_str='SID=...; HSID=...; SSID=...')
   info = extract(page)

**Bring your own requests.** ``parse`` is a convenience, not a requirement.
Since :func:`extract` only needs a string, you can fetch pages however you
like — with your own ``requests`` session, custom headers, a retry policy, or
a proxy — and pass the resulting text in directly:

.. code-block:: python

   import requests
   from socid_extractor import extract

   session = requests.Session()
   session.headers.update({'User-Agent': 'my-tool/1.0'})

   resp = session.get('https://github.com/torvalds')
   info = extract(resp.text)

parse_cookies
-------------

.. code-block:: python

   parse_cookies(cookies_str) -> dict

Turns a raw cookie header string into a ``{name: value}`` dict. ``parse``
uses it internally, but you can call it directly when building a request
yourself:

.. code-block:: python

   from socid_extractor import parse_cookies

   cookies = parse_cookies('SID=abc; HSID=def')
   # {'SID': 'abc', 'HSID': 'def'}

mutate_url
----------

.. code-block:: python

   mutate_url(url) -> [(mutated_url, headers), ...]

Some schemes register ``url_mutations`` that rewrite a human-facing profile
URL into the API endpoint that actually carries the data — for example
``github.com/{username}`` into ``api.github.com/users/{username}``.
``mutate_url`` walks every scheme, matches the input URL against those
mutation rules, and returns a list of ``(mutated_url, headers)`` pairs, where
``headers`` is any extra headers the mutation requires (an empty set when it
declares none).

.. code-block:: python

   from socid_extractor import mutate_url

   for api_url, headers in mutate_url('https://github.com/torvalds'):
       print(api_url, headers)

This is a **CLI-oriented helper**: it is used to expand a profile URL into the
richer API URLs worth fetching. :func:`extract` itself does **not** call
``mutate_url`` — it only parses whatever string you give it. If you want to
follow a mutation, fetch the mutated URL yourself and pass its response to
``extract``.

Used by other tools
-------------------

Because the parsing surface is a single pure function, ``socid_extractor`` is
easy to embed. It powers `Maigret <https://github.com/soxoj/maigret>`_ and a
number of other OSINT tools. See :doc:`maigret-integration` for how Maigret
consumes the library.
