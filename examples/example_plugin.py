"""Example socid_extractor plugin.

Place this file (or your own .py files) in ~/.socid_extractor/plugins/
Each file must export a module-level `schemes` dict in the same format
as socid_extractor/schemes.py.

Plugin schemes take priority over built-in schemes (they are checked first).
Files are loaded in alphabetical order, so you can control priority with
naming: 00_high_priority.py, 50_normal.py, 99_low_priority.py.
"""
import json
import re

# You can import socid_extractor utilities:
# from socid_extractor.utils import parse_datetime, safe_deep_get

schemes = {
    'Example Service API': {
        'url_hints': ('example-service.com',),
        'flags': ['"example_uid":', '"example_username":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('example_uid'),
            'username': lambda x: x.get('example_username'),
            'fullname': lambda x: x.get('display_name'),
        },
        # Optional: URL mutations for Maigret integration
        # 'url_mutations': [{
        #     'from': r'https?://example-service\.com/(?P<username>[^/?#]+)',
        #     'to': 'https://api.example-service.com/users/{username}',
        # }],
    },
}
