.. _maigret-integration:

Maigret integration
===================

`Maigret <https://github.com/soxoj/maigret>`_ is a username reconnaissance tool
that checks a single username across thousands of sites. ``socid_extractor`` is
the extraction engine it uses: whenever Maigret confirms an account exists, it
hands the fetched HTML to :func:`socid_extractor.extract` to pull structured
profile fields out of the page.

This page documents that seam — which Maigret function calls ``extract()``, how
it is gated, and where the extracted data lands — so you can enable and consume
it from Maigret's own API. All references below are to the current Maigret
source.

How the two projects fit together
----------------------------------

Maigret owns the *breadth*: the site database, the async checker, proxy/Tor
routing, and the found/not-found decision for each site. ``socid_extractor``
owns the *depth*: given the HTML of one confirmed profile page, it matches a
site scheme and returns a flat dict of normalized fields (bio, uid, linked
accounts, timestamps, and so on).

The division of labour is strict:

- Maigret decides *whether* an account exists and fetches its page.
- ``socid_extractor`` decides *what can be read* from that page.

Because the field names ``socid_extractor`` emits are shared and normalized
(see :doc:`ontology`), Maigret can line up the same person's data across many
different sites.

The integration seam
--------------------

Maigret imports the extractor at the top of ``maigret/checking.py``:

.. code-block:: python

   from socid_extractor import extract, mutate_url

The call itself is wrapped in a small, never-raising helper,
``extract_ids_data`` (``maigret/checking.py``):

.. code-block:: python

   def extract_ids_data(html_text, logger, site) -> Dict:
       try:
           return extract(html_text)
       except Exception as e:
           logger.warning(f"Error while parsing {site.name}: {e}", exc_info=True)
           return {}

Note that it calls ``extract(html_text)`` with the page HTML as the only
argument — extraction failures are logged and swallowed so a bad scheme can
never sink an otherwise valid result.

The helper is invoked from the per-site check flow, gated on two conditions:

.. code-block:: python

   extracted_ids_data = {}

   if is_parsing_enabled and result.status == MaigretCheckStatus.CLAIMED:
       extracted_ids_data = extract_ids_data(html_text, logger, site)
       if extracted_ids_data:
           new_usernames = parse_usernames(extracted_ids_data, logger)
           results_info = update_results_info(
               results_info, extracted_ids_data, new_usernames
           )
           result.ids_data = extracted_ids_data

So extraction runs only when both gates are open:

.. list-table::
   :header-rows: 1

   * - Gate
     - Meaning
   * - ``is_parsing_enabled``
     - Parsing is turned on for this run (off by default).
   * - ``result.status == MaigretCheckStatus.CLAIMED``
     - Maigret confirmed the account exists on this site.

When both hold, the returned dict is stored on the result object as
``result.ids_data``. Maigret also runs the extracted fields through
``parse_usernames`` to discover further usernames to check, and merges those
back into the running results. In Maigret's library API the same data is
surfaced under the ``ids_data`` key of each site's result (for example,
``result["ids_data"]``).

Enabling extraction from Maigret's library API
----------------------------------------------

Extraction is opt-in. From Maigret's Python API you turn it on by passing
``is_parsing_enabled=True`` to the search entry point:

.. code-block:: python

   results = asyncio.run(
       maigret_search(
           username="soxoj",
           site_dict=sites,
           logger=logging.getLogger("maigret"),
           timeout=30,
           is_parsing_enabled=True,
       )
   )

   for site_name, result in results.items():
       if result["status"].is_found():
           print(site_name, result["ids_data"])

For the full pattern — loading the site database, filtering sites, and running
inside an existing event loop — see Maigret's own
:external+maigret:doc:`library-usage` page. The ``is_parsing_enabled`` flag
documented there is exactly the gate described above.

Why the shared ontology matters
--------------------------------

The value of a normalized field vocabulary shows up precisely at this seam.
Maigret does not treat the extracted dict as opaque — it reads specific keys out
of it. It derives new usernames to pivot on (via ``parse_usernames`` /
``extract_usernames``), pulls links and websites into the result graph, and
renders fields such as ``image``, ``created_at``, and ``website`` in its
reports.

That only works because every scheme in ``socid_extractor`` emits the *same*
name for the *same* concept. When a GitHub scheme and a VK scheme both call a
registration timestamp ``created_at``, Maigret can correlate them without
per-site special-casing. Keeping to the shared vocabulary in :doc:`ontology`
is therefore what makes cross-site correlation possible on Maigret's side.

What Maigret does and does not use
----------------------------------

Two behaviours are worth calling out precisely, because they are easy to assume
wrong:

**The AI fallback stays off in this path.** ``extract_ids_data`` calls
``extract(html_text)`` with no ``use_ai_fallback`` argument, so it takes the
default (``use_ai_fallback=False``). The opt-in :doc:`ai-fallback` is never
engaged by Maigret's parsing seam.

**``mutate_url`` is a separate, opt-in enrichment path — not part of the core
seam.** The ``extract_ids_data`` seam described above uses ``extract()`` only.
Maigret does also import ``socid_extractor``'s ``mutate_url``, but it is used by
a distinct code path, ``run_url_mutations``, which fetches secondary
URLs derived from a profile and merges their fields in. That path is gated on a
separate ``--enrich`` flag (off by default) *and* a ``CLAIMED`` status, and it
is independent of the ``is_parsing_enabled`` extraction described here. If you
only enable ``is_parsing_enabled``, no URL mutations are performed.

Cross-project documentation
---------------------------

These two projects cross-reference each other through Sphinx intersphinx, so
links resolve in both directions. From here you can jump straight into Maigret's
documentation — start at its :external+maigret:doc:`index`, or go directly to
:external+maigret:doc:`library-usage`, :external+maigret:doc:`quick-start`, or
:external+maigret:doc:`command-line-options`. For the extractor side of the
seam, see :doc:`how-extraction-works` and :doc:`ontology`.
