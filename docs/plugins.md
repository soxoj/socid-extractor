# Plugins

socid_extractor supports loading additional extraction schemes from plugins.

## Directory-based plugins

Place `.py` files in `~/.socid_extractor/plugins/`:

```
~/.socid_extractor/plugins/
    my_private_sites.py
    company_internal.py
```

Each file must export a module-level `schemes` dict:

```python
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
```

See [`examples/example_plugin.py`](../examples/example_plugin.py) for a full template.

### Priority

- Plugin schemes are checked **before** built-in schemes (first match wins in `extract()`)
- If a plugin defines a scheme with the same name as a built-in, the plugin version wins
- Files are loaded in alphabetical order: `00_high.py` before `50_normal.py`

### Available imports

Plugin files can use any installed Python package. Common imports:

```python
import json, re
from socid_extractor.utils import parse_datetime, safe_deep_get
```

### Error handling

- Missing `~/.socid_extractor/plugins/` directory — silently skipped
- Syntax errors in a plugin file — warning logged, file skipped
- Missing `schemes` variable — warning logged, file skipped

Enable debug logging to see plugin load details: `logging.basicConfig(level=logging.DEBUG)`

## Pip-installable plugins

Third-party packages can register plugins via entry points in `pyproject.toml`:

```toml
[project.entry-points."socid_extractor.plugins"]
my_plugin = "my_package.extractors:schemes"
```

Where `my_package/extractors.py` exports a `schemes` dict.

Install: `pip install my-socid-plugin` — schemes are automatically loaded.
