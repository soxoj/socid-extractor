.. _installation:

Installation
============

Requirements
------------

- **Python 3.10+** (CI tests 3.10 – 3.14).
- No API keys and no headless browser for the core library. The optional
  :doc:`AI fallback <ai-fallback>` needs an OpenAI API key.

From PyPI
---------

.. code-block:: bash

   pip install socid-extractor

For a clean CLI install on a workstation (isolated virtualenv, ``socid_extractor`` on
your ``PATH``):

.. code-block:: bash

   pipx install socid-extractor

Latest development version
--------------------------

.. code-block:: bash

   pip install -U git+https://github.com/soxoj/socid-extractor.git

Optional extras
---------------

The extras are declared in ``pyproject.toml`` under ``[project.optional-dependencies]``
and installed with the ``package[extra]`` syntax:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Extra
     - Contents / when to use
   * - ``ai``
     - ``openai`` — required only for the opt-in :doc:`AI fallback <ai-fallback>`.
       ``pip install 'socid-extractor[ai]'``. The import is lazy, so the core library
       never needs it.
   * - ``test``
     - ``pytest`` + ``pytest-rerunfailures`` + ``pytest-xdist``.
       ``pip install '.[test]'``.
   * - ``dev``
     - Everything in ``test`` plus ``flake8`` / ``mypy`` / ``black`` — the full set CI
       uses. ``pip install '.[dev]'``.

Verifying the install
---------------------

.. code-block:: console

   $ socid_extractor --url https://github.com/torvalds
   ...

   $ python -c "import socid_extractor; print(socid_extractor.__version__)"
   0.1.1

Running without installing
--------------------------

From a checkout of the repository, ``run.py`` calls the CLI directly:

.. code-block:: bash

   ./run.py --url https://github.com/torvalds

Next: the :doc:`quick-start` for first calls, or :doc:`library-usage` for the full API.
