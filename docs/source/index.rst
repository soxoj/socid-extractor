.. _index:

Welcome to the socid_extractor docs!
====================================

**socid_extractor** turns any public profile page into a structured account record —
usernames, display names, bios, avatars, locations, joined-at dates, follower counts,
external links, and the **stable internal identifiers** that uniquely pin an account
across renames, redesigns, and deletions.

It parses HTML pages and API responses from 130+ platforms and returns a flat,
machine-readable dictionary of account fields. No API keys required, no headless
browser — just a single :func:`~socid_extractor.extract` call on response text.

socid_extractor powers `Maigret <https://github.com/soxoj/maigret>`_ and a number of
other OSINT tools. If you are looking for a ready-to-use username checker, start with
the :external+maigret:doc:`Maigret docs <index>`; this project is the extraction engine
underneath it.

.. warning::
   **This tool is intended for educational and lawful purposes only.**
   The developers do not endorse or encourage any illegal activities or misuse of this tool.
   Regulations regarding the collection and use of personal data vary by country and region,
   including but not limited to GDPR in the EU, CCPA in the USA, and similar laws worldwide.

   It is your sole responsibility to ensure that your use of this tool complies with all
   applicable laws and regulations in your jurisdiction. Any illegal use of this tool is
   strictly prohibited, and you are fully accountable for your actions.

   The authors and developers of this tool bear no responsibility for any misuse
   or unlawful activities conducted by its users.

You may be interested in:
-------------------------
- :doc:`Quick start <quick-start>`
- :doc:`Library usage <library-usage>`
- :doc:`Field ontology <ontology>`
- :doc:`How extraction works <how-extraction-works>`
- :doc:`AI fallback <ai-fallback>`
- :doc:`Maigret integration <maigret-integration>`
- :doc:`Adding a scheme <adding-a-scheme>`

.. toctree::
   :hidden:
   :caption: Getting started

   quick-start
   installation
   library-usage
   supported-sites

.. toctree::
   :hidden:
   :caption: How it works

   how-extraction-works
   ontology
   ai-fallback
   maigret-integration

.. toctree::
   :hidden:
   :caption: Contributing

   adding-a-scheme
   plugins
   development
