import argparse
import logging
import sys
from functools import reduce

from .activation import *
from .main import parse, extract
from .matching import get_similarity, get_similarity_description


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
    parser.add_argument('--match', nargs=2, help='compare 2 accounts data and get matching score')
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

    if args.match:
        extracted = []
        for acc in args.match:
            extracted_acc_info = extract(get_site_response(acc, args.cookies, headers))
            if not extracted_acc_info:
                print(f'No info extracted by link {acc}\n'
                    'Please check if user exists and socid_extractor supports this site.')
                return
            extracted.append(extracted_acc_info)

        all_fields = list(reduce(lambda x, y: x.union(y), [set(a.keys()) for a in extracted]))
        # pair matching
        average_similarity_acc = []
        for n1, info1 in enumerate(extracted):
            for n2, info2 in enumerate(extracted):
                if n1 >= n2:
                    continue
                for f in all_fields:
                    v1 = info1.get(f)
                    v2 = info2.get(f)
                    if not (v1 and v2):
                        continue

                    score, sim_type = get_similarity(v1, v2)
                    average_similarity_acc.append(score)
                    print(get_similarity_description(score, sim_type, f))
                    logging.debug(v1, v2)

        average_similarity = round(sum(average_similarity_acc) / len(average_similarity_acc), 2)
        print(f'Average accounts similarity: {average_similarity * 100}%')
    else:
        if not args.file:
            page = get_site_response(args.url, args.cookies, headers)
        else:
            page = open(args.url).read()

        info = extract(page)
        if not info:
            sys.exit()

        print_info(info)


if __name__ == '__main__':
    run()
