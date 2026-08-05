.. _quick-start:

Quick start
===========

Install
-------

Python 3.10+ is required.

.. code-block:: bash

   pip install socid-extractor

See :doc:`installation` for ``pipx``, the development version, and optional extras
(the AI fallback, test, and dev tool sets).

As a CLI
--------

Point ``socid_extractor`` at a profile URL and it fetches the page and prints one
``field: value`` per line:

.. code-block:: console

   $ socid_extractor --url https://www.deviantart.com/muse1908
   country: France
   created_at: 2005-06-16 18:17:41
   gender: female
   username: Muse1908
   website: www.patreon.com/musemercier
   links: ['https://www.facebook.com/musemercier', 'https://www.instagram.com/muse.mercier/', 'https://www.patreon.com/musemercier']
   tagline: Nothing worth having is easy...

**Batch tip.** Pass ``--skip-fetch-if-no-url-hint`` to skip the HTTP request when the
URL doesn't match any known site hint (faster for large batches, but may skip generic
engines such as forum templates):

.. code-block:: bash

   socid_extractor --url https://example.com/foo --skip-fetch-if-no-url-hint

As a Python library
-------------------

Fetch the page yourself, then hand the response text to :func:`~socid_extractor.extract`:

.. code-block:: python

   import requests
   import socid_extractor

   r = requests.get('https://www.patreon.com/annetlovart')
   print(socid_extractor.extract(r.text))
   # {'patreon_id': '33913189', 'patreon_username': 'annetlovart',
   #  'fullname': 'Annet Lovart',
   #  'links': "['https://www.facebook.com/322598031832479', ...]",
   #  '_extractor': 'Patreon'}

``extract()`` is a pure function over the response body — it never makes network
requests itself. The returned dict uses the normalized field names from the
:doc:`ontology`, plus an ``_extractor`` key naming the scheme that matched. If no scheme
matches it returns ``{}``.

Where to go next
----------------

- :doc:`library-usage` — the full ``extract`` / ``parse`` / ``mutate_url`` API.
- :doc:`how-extraction-works` — how a page is matched to a scheme and reduced to fields.
- :doc:`ontology` — the standard field names every scheme uses.
- :doc:`ai-fallback` — the opt-in LLM fallback for pages no scheme covers.
- :doc:`adding-a-scheme` — add support for a new site.
