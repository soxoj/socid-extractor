"""Tests for the plugin loading mechanism."""
import json
import logging

import pytest

from socid_extractor.plugins import _load_directory_plugins, load_plugins


@pytest.fixture
def plugin_dir(tmp_path):
    d = tmp_path / 'plugins'
    d.mkdir()
    return d


def test_loads_valid_plugin(plugin_dir):
    (plugin_dir / 'my_plugin.py').write_text(
        "schemes = {'Test Scheme': {'flags': ['test_flag'], 'regex': r'test'}}\n"
    )
    result = _load_directory_plugins(plugin_dir=plugin_dir)
    assert 'Test Scheme' in result
    assert result['Test Scheme']['flags'] == ['test_flag']


def test_missing_directory_silently_skipped(tmp_path):
    result = _load_directory_plugins(plugin_dir=tmp_path / 'nonexistent')
    assert result == {}


def test_syntax_error_skipped_with_warning(plugin_dir, caplog):
    (plugin_dir / 'bad.py').write_text('def foo(\n')
    with caplog.at_level(logging.WARNING):
        result = _load_directory_plugins(plugin_dir=plugin_dir)
    assert result == {}
    assert 'Failed to load plugin' in caplog.text


def test_missing_schemes_var_skipped(plugin_dir, caplog):
    (plugin_dir / 'no_schemes.py').write_text('x = 42\n')
    with caplog.at_level(logging.WARNING):
        result = _load_directory_plugins(plugin_dir=plugin_dir)
    assert result == {}
    assert 'does not export' in caplog.text


def test_sorted_load_order(plugin_dir):
    (plugin_dir / '02_second.py').write_text(
        "schemes = {'Second': {'flags': ['s'], 'regex': r's'}}\n"
    )
    (plugin_dir / '01_first.py').write_text(
        "schemes = {'First': {'flags': ['f'], 'regex': r'f'}}\n"
    )
    result = _load_directory_plugins(plugin_dir=plugin_dir)
    keys = list(result.keys())
    assert keys == ['First', 'Second']


def test_non_py_files_ignored(plugin_dir):
    (plugin_dir / 'readme.txt').write_text('not a plugin')
    (plugin_dir / 'data.json').write_text('{}')
    result = _load_directory_plugins(plugin_dir=plugin_dir)
    assert result == {}


def test_plugin_with_imports_and_lambdas(plugin_dir):
    (plugin_dir / 'with_imports.py').write_text(
        "import json\n"
        "schemes = {'Import Test': {'flags': ['\"import_test\":'], 'regex': r'^(\\{[\\s\\S]+\\})$',\n"
        "    'extract_json': True,\n"
        "    'fields': {'uid': lambda x: x.get('id')}}}\n"
    )
    result = _load_directory_plugins(plugin_dir=plugin_dir)
    assert 'Import Test' in result
    assert callable(result['Import Test']['fields']['uid'])


def test_plugins_prepended_before_builtin(plugin_dir):
    """Plugin schemes appear before built-in schemes in dict order."""
    (plugin_dir / 'extra.py').write_text(
        "schemes = {'Plugin Scheme': {'flags': ['pf'], 'regex': r'pr'}}\n"
    )
    target = {'Builtin': {'flags': ['bf'], 'regex': r'br'}}
    load_plugins(target, plugin_dir=plugin_dir)
    keys = list(target.keys())
    assert keys.index('Plugin Scheme') < keys.index('Builtin')


def test_override_warning(plugin_dir, caplog):
    (plugin_dir / 'override.py').write_text(
        "schemes = {'Existing': {'flags': ['new'], 'regex': r'new'}}\n"
    )
    target = {'Existing': {'flags': ['old'], 'regex': r'old'}}
    with caplog.at_level(logging.WARNING):
        load_plugins(target, plugin_dir=plugin_dir)
    assert 'overrides' in caplog.text
    # Plugin version wins (it's first in iteration AND overwrites)
    assert target['Existing']['flags'] == ['new']


def test_no_plugins_no_change(tmp_path):
    target = {'A': {'flags': ['a']}, 'B': {'flags': ['b']}}
    original = dict(target)
    load_plugins(target, plugin_dir=tmp_path / 'nonexistent')
    assert target == original


def test_e2e_extract_with_plugin(plugin_dir):
    """Full cycle: plugin scheme is matched by extract()."""
    (plugin_dir / 'custom.py').write_text(
        "import json\n"
        "schemes = {'Custom Plugin Site': {\n"
        "    'flags': ['\"custom_plugin_marker\"'],\n"
        "    'regex': r'^(\\{[\\s\\S]+\\})$',\n"
        "    'extract_json': True,\n"
        "    'fields': {\n"
        "        'uid': lambda x: x.get('custom_id'),\n"
        "        'username': lambda x: x.get('custom_name'),\n"
        "    },\n"
        "}}\n"
    )
    # Build a schemes dict with one builtin + load plugin
    target = {'Builtin': {'flags': ['builtin_only'], 'regex': r'builtin'}}
    load_plugins(target, plugin_dir=plugin_dir)

    # Simulate what extract() does: iterate and match
    page = json.dumps({"custom_plugin_marker": True, "custom_id": 42, "custom_name": "alice"})
    import re as re_mod
    for scheme_name, scheme_data in target.items():
        flags = scheme_data['flags']
        if all(flag in page for flag in flags):
            assert scheme_name == 'Custom Plugin Site'
            break
    else:
        pytest.fail('No scheme matched')
