import argparse
import ast
import json
import logging
import sys
from functools import reduce

from .activation import *
from .main import parse, extract, mutate_url
from .schemes import schemes
from .url_relevance import check_url_relevance
from .utils import parse_cookies, import_cookiejar, join_cookies


def _jsonify_value(v):
    if isinstance(v, str) and v[:1] in ('[', '{'):
        try:
            parsed = ast.literal_eval(v)
            if isinstance(parsed, (list, tuple, dict)):
                return parsed
        except (ValueError, SyntaxError):
            pass
    return v


def jsonify_info(info):
    return {k: _jsonify_value(v) for k, v in (info or {}).items()}


def print_info(info):
    logging.info('Result\n' + '-' * 40)
    for key, value in info.items():
        print('%s: %s' % (key, value))


def get_site_response(url, cookies=None, headers={}):
    page, status = parse(url, cookies, headers=headers, timeout=10)
    if status != 200:
        logging.info('Answer code {}, something went wrong'.format(status))
    return page


def run():
    parser = argparse.ArgumentParser(
        description=f'Extract accounts\' identifiers from pages. {len(schemes)} sites (methods) are supported.',
        prog='socid_extractor',
    )
    parser.add_argument('--url', help='url to parse')
    parser.add_argument('--cookies', default='', help='plaintext cookies (a=b; c=d) to make http requests with')
    parser.add_argument('--cookie-jar', help='cookiejar file to make http requests with')
    parser.add_argument('-v', '--verbose', action='store_true', help='display verbose information')
    parser.add_argument('-d', '--debug', action='store_true', help='display debug information')
    parser.add_argument('--file', help='file to parse')
    parser.add_argument('--activation', type=str, help='use certain type of request activation')
    parser.add_argument(
        '--skip-fetch-if-no-url-hint',
        action='store_true',
        help='skip HTTP request when the URL does not match any supported site hint (substring check; may skip generic engines)',
    )
    parser.add_argument('--json', action='store_true', help='output results as JSON')

    args = parser.parse_args()

    log_level = logging.ERROR
    if args.verbose:
        log_level = logging.INFO
    elif args.debug:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level, format='-' * 40 + '\n%(levelname)s: %(message)s')

    cookies = {}
    cookies.update(parse_cookies(args.cookies))
    if args.cookie_jar:
        cookies.update(import_cookiejar(args.cookie_jar))

    cookies_str = join_cookies(cookies)

    headers = {}
    if args.activation:
        cookies_str, headers = globals().get(args.activation)(cookies_str)
        logging.debug(cookies_str)
        logging.debug(headers)

    # load from file
    if args.file:
        page = open(args.file).read()
        info = extract(page)
        if args.json:
            print(json.dumps(jsonify_info(info), ensure_ascii=False, indent=2, default=str))
        elif info:
            print_info(info)
    # load from url(s)
    elif args.url:
        # (url, headers)
        reqs = [(args.url, set())]
        mutations = mutate_url(args.url)
        if mutations:
            reqs += list(mutations)

        results = []
        for req in reqs:
            url, add_headers = req

            if not args.json:
                print(f'Analyzing URL {url}...')
            url_headers = dict(headers)
            url_headers.update(add_headers)

            if args.skip_fetch_if_no_url_hint and not check_url_relevance(url):
                print('Skipping fetch: URL did not match any supported site hint.', file=sys.stderr)
                continue

            page = get_site_response(url, cookies_str, url_headers)
            info = extract(page)
            if args.json:
                jsonified = jsonify_info(info)
                if jsonified:
                    results.append({'url': url, 'info': jsonified})
            elif info:
                print_info(info)

        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    run()
