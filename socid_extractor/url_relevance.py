# Rough substring filter for CLI: avoids HTTP when no scheme hint matches the URL string.
import re

from .schemes import schemes

STOPWORDS = frozenset(
    {
        'api',
        'file',
        'group',
        'html',
        'page',
        'profile',
        'user',
    }
)


def _name_fallback_tokens(scheme_name):
    parts = re.findall(r'[a-z0-9.]+', scheme_name.lower())
    return tuple(p for p in parts if len(p) > 1 and p not in STOPWORDS)


def check_url_relevance(url):
    low = url.lower()
    for scheme_name, scheme_data in schemes.items():
        hints = scheme_data.get('url_hints') or ()
        for hint in (*hints, *_name_fallback_tokens(scheme_name)):
            if len(hint) > 1 and hint in low:
                return True
        # A scheme that knows how to rewrite this URL is a hint in itself: schemes
        # keyed on a route rather than on a host (Discourse and the like) match any
        # domain, and listing those domains by hand is exactly what they avoid.
        for mutation in scheme_data.get('url_mutations') or ():
            if re.search(mutation['from'], url):
                return True
    return False
