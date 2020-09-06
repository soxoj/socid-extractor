import argparse
import logging
import sys

from .main import parse, extract

def run():
    parser = argparse.ArgumentParser(description='Extract accounts\' identifiers from pages.')
    parser.add_argument('url', help='url to parse')
    parser.add_argument('--cookies', default='', help='cookies to make http requests with auth')
    parser.add_argument('--debug', action='store_true', help='log debug information')
    parser.add_argument('--file', action='store_true', help='load from file instead of URL')

    args = parser.parse_args()

    log_level = logging.INFO if not args.debug else logging.DEBUG

    logging.basicConfig(level=log_level, format='-'*40 + '\n%(levelname)s: %(message)s')

    if not args.file:
        url = args.url
        page, status = parse(url, args.cookies)

        if status != 200:
            logging.info('Answer code {}, something went wrong'.format(status))
    else:
        page = open(args.url).read()

    info = extract(page)
    if not info:
        sys.exit()

    logging.info('Result\n' + '-'*40)
    for key, value in info.items():
        print('%s: %s' % (key, value))


if __name__ == '__main__':
    run()
