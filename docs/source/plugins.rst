.. _plugins:

Plugins
=======

socid_extractor can load additional extraction schemes from plugins. A plugin
scheme uses the **exact same format** as the built-in schemes — the same
``flags``, ``regex``, ``fields`` and other keys documented in
:doc:`adding-a-scheme`. Once loaded, plugin schemes are merged into the same
scheme dictionary the library iterates over, so ``extract()`` treats them
identically to the built-ins (see :doc:`how-extraction-works`).

There are two ways to ship a plugin:

- **Directory-based** — drop ``.py`` files into ``~/.socid_extractor/plugins/``.
- **Pip-installable** — publish a package that registers an entry point.

Both mechanisms simply contribute a ``schemes`` dict; nothing else about the
extraction pipeline changes.

Directory-based plugins
-----------------------

Place ``.py`` files in ``~/.socid_extractor/plugins/``::

   ~/.socid_extractor/plugins/
       my_private_sites.py
       company_internal.py

Each file must export a module-level ``schemes`` dict:

.. code-block:: python

   import json

   schemes = {
       'My Private API': {
           'flags': ['"my_unique_key":'],
           'regex': r'^(\{[\s\S]+\})$',
           'extract_json': True,
           'fields': {
               'uid': lambda x: x.get('user_id'),
               'username': lambda x: x.get('login'),
           },
       },
   }

The scheme structure is identical to the built-ins; see :doc:`adding-a-scheme`
for the full set of supported keys, and ``examples/example_plugin.py`` in the
repository for a complete template.

Priority
~~~~~~~~

Plugin schemes are inserted **before** the built-in schemes. Because
``extract()`` returns the first matching scheme, this has three consequences:

.. list-table::
   :header-rows: 1

   * - Rule
     - Behaviour
   * - Plugins first
     - Plugin schemes are checked before built-ins, so a plugin match wins over
       a built-in match on the same page.
   * - Same-name override
     - If a plugin defines a scheme with the same name as a built-in, the plugin
       version replaces the built-in one (a warning is logged).
   * - Alphabetical load order
     - Directory files are loaded in sorted filename order, so ``00_high.py``
       loads before ``50_normal.py``. Use numeric prefixes to control which
       plugin wins when two of them define the same scheme name.

Available imports
~~~~~~~~~~~~~~~~~

A plugin file is an ordinary Python module, so it can import any installed
package. Common imports include the standard library and socid_extractor's own
helpers:

.. code-block:: python

   import json, re
   from socid_extractor.utils import parse_datetime, safe_deep_get

Error handling
~~~~~~~~~~~~~~

Plugin loading never aborts the run — a broken plugin is skipped and the rest
continue:

.. list-table::
   :header-rows: 1

   * - Situation
     - Result
   * - ``~/.socid_extractor/plugins/`` does not exist
     - Silently skipped.
   * - Syntax error or exception while importing a file
     - Warning logged, that file skipped.
   * - File does not export a ``schemes`` dict
     - Warning logged, that file skipped.

To see which plugins were loaded and which were skipped, enable debug logging:

.. code-block:: python

   import logging
   logging.basicConfig(level=logging.DEBUG)

Pip-installable plugins
-----------------------

A third-party package can register schemes through the
``socid_extractor.plugins`` entry point group. Point the entry point at a
module attribute that is a ``schemes`` dict:

.. code-block:: toml

   [project.entry-points."socid_extractor.plugins"]
   my_plugin = "my_package.extractors:schemes"

Here ``my_package/extractors.py`` exports a ``schemes`` dict in the same format
as a directory-based plugin. Once the package is installed, its schemes are
discovered and loaded automatically — no configuration or directory setup
required:

.. code-block:: console

   $ pip install my-socid-plugin

Entry-point schemes follow the same priority rules as directory plugins: they
are inserted before the built-ins, and a same-name scheme overrides the
built-in one.
