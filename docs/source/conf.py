# Configuration file for the Sphinx documentation builder.

import os
import re

# -- Project information

project = 'socid_extractor'
copyright = '2025, soxoj'
author = 'soxoj'

# Read out of socid_extractor/__init__.py rather than kept in step by hand.
# Deliberately a text read and not an import: the docs build should not need
# the package's runtime dependencies installed.
_init = os.path.join(os.path.dirname(__file__), '..', '..', 'socid_extractor', '__init__.py')
with open(_init) as f:
    release = re.search(r"__version__\s*=\s*'([^']+)'", f.read()).group(1)
version = '.'.join(release.split('.')[:2])

# -- Internationalization
#
# Default to English. Translation projects on Read the Docs set the
# ``READTHEDOCS_LANGUAGE`` env var (e.g. ``zh_CN``); locally the language
# can be overridden via ``sphinx-build -D language=zh_CN``. Mirrors the
# sibling Maigret docs so a translation pipeline can be added later.
language = os.environ.get('READTHEDOCS_LANGUAGE', 'en')
locale_dirs = ['locale/']
gettext_compact = False
gettext_uuid = True

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx_copybutton',
]

# Cross-project references. Maigret embeds socid_extractor, so its docs are
# the natural sibling to link to (``:external+maigret:doc:`library-usage```).
# Reciprocal linking from Maigret needs a matching ``'socid_extractor'`` entry
# in maigret/docs/source/conf.py's intersphinx_mapping.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'maigret': ('https://maigret.readthedocs.io/en/latest/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'
