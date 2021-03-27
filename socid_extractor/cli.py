import argparse
import logging
import sys
from functools import reduce

from .activation import *
from .main import parse, extract, mutate_url


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
    parser = argparse.ArgumentParser(description='Extract accounts\' identifiers from pages.')
    parser.add_argument('--url', help='url to parse')
    parser.add_argument('--cookies', default='', help='cookies to make http requests with auth')
    parser.add_argument('-v', '--verbose', action='store_true', help='display verbose information')
    parser.add_argument('-d', '--debug', action='store_true', help='display debug information')
    parser.add_argument('--file', action='store_true', help='load from file instead of URL')
    parser.add_argument('--activation', type=str, help='use certain type of request activation')

    args = parser.parse_args()

    log_level = logging.ERROR
    if args.verbose:
        log_level = logging.INFO
    elif args.debug:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level, format='-' * 40 + '\n%(levelname)s: %(message)s')

    headers = {}
    if args.activation:
        cookies, headers = globals().get(args.activation)(args.cookies)
        logging.debug(cookies)
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

            page = get_site_response(url, args.cookies, url_headers)
            info = extract(page)
            if info:
                print_info(info)


if __name__ == '__main__':
    run()
