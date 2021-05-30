import argparse
import logging
import sys
from functools import reduce

from .activation import *
from .main import parse, extract, mutate_url
from .schemes import schemes
from .utils import parse_cookies, import_cookiejar, join_cookies


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
        if info:
            print_info(info)
    # load from url(s)
    elif args.url:
        # (url, headers)
        reqs = [(args.url, set())]
        mutations = mutate_url(args.url)
        if mutations:
            reqs += list(mutations)

        for req in reqs:
            url, add_headers = req

            print(f'Analyzing URL {url}...')
            url_headers = dict(headers)
            url_headers.update(add_headers)

            page = get_site_response(url, cookies_str, url_headers)
            info = extract(page)
            if info:
                print_info(info)


if __name__ == '__main__':
    run()
