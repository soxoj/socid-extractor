"""Plugin loading for socid_extractor.

Two mechanisms for extending the built-in schemes dict:

1. Directory-based: Python files in ~/.socid_extractor/plugins/
2. Entry-point-based: installed packages declaring the
   'socid_extractor.plugins' entry point group

Plugin schemes are inserted BEFORE built-in schemes so they take
priority in extract() (which returns the first match).
"""
import importlib.metadata
import importlib.util
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PLUGIN_DIR = Path.home() / '.socid_extractor' / 'plugins'


def _load_directory_plugins(plugin_dir=None):
    """Load .py files from plugin_dir, return merged schemes dict."""
    dirpath = plugin_dir or PLUGIN_DIR
    if not dirpath.is_dir():
        return {}

    result = {}
    for filepath in sorted(dirpath.glob('*.py')):
        module_name = f'socid_extractor_plugin_{filepath.stem}'
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                logger.warning('Could not create module spec for plugin %s', filepath)
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception:
            logger.warning('Failed to load plugin %s', filepath, exc_info=True)
            continue

        plugin_schemes = getattr(mod, 'schemes', None)
        if not isinstance(plugin_schemes, dict):
            logger.warning('Plugin %s does not export a `schemes` dict, skipping', filepath)
            continue

        result.update(plugin_schemes)
        logger.debug('Loaded %d schemes from plugin %s', len(plugin_schemes), filepath.name)

    return result


def _load_entrypoint_plugins():
    """Load schemes from installed packages using entry_points group."""
    result = {}
    try:
        eps = importlib.metadata.entry_points(group='socid_extractor.plugins')
    except TypeError:
        eps = importlib.metadata.entry_points().get('socid_extractor.plugins', [])

    for ep in eps:
        try:
            plugin_schemes = ep.load()
        except Exception:
            logger.warning('Failed to load entry point plugin %s', ep.name, exc_info=True)
            continue

        if not isinstance(plugin_schemes, dict):
            logger.warning('Entry point %s did not return a dict, skipping', ep.name)
            continue

        result.update(plugin_schemes)
        logger.debug('Loaded %d schemes from entry point %s', len(plugin_schemes), ep.name)

    return result


def load_plugins(target, plugin_dir=None):
    """Load all plugins and insert them BEFORE built-in schemes.

    Plugin schemes take priority over built-in ones because extract()
    returns the first matching scheme.
    """
    plugin_schemes = {}
    plugin_schemes.update(_load_directory_plugins(plugin_dir=plugin_dir))
    plugin_schemes.update(_load_entrypoint_plugins())

    if not plugin_schemes:
        return

    for name in plugin_schemes:
        if name in target:
            logger.warning('Plugin scheme %r overrides built-in scheme', name)

    # Prepend: plugin schemes first, then built-in (excluding overridden)
    builtin_copy = {k: v for k, v in target.items() if k not in plugin_schemes}
    target.clear()
    target.update(plugin_schemes)
    target.update(builtin_copy)
