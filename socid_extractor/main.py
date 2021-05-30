import logging
from http.cookies import SimpleCookie
from bs4 import BeautifulSoup as bs

import requests

from .schemes import *
from .postprocessor import POSTPROCESSORS
from .utils import parse_cookies

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
}

PROCESS_ERRORS = (AttributeError, KeyError, IndexError, TypeError)


def parse(url, cookies_str='', timeout=3, headers={}):
    cookies = parse_cookies(cookies_str)
    req_headers = dict(HEADERS)
    req_headers.update(headers)
    logging.debug(req_headers)
    page = requests.get(url, headers=req_headers, cookies=cookies, allow_redirects=True, timeout=(timeout, timeout))
    logging.debug('Server response: \'%s\'', page.text)
    logging.debug('Status code: %d', page.status_code)
    return page.text, page.status_code


def mutate_url(url):
    mutate_results = []
    for scheme_name, scheme_data in schemes.items():
        mutations_list = scheme_data.get('url_mutations')
        if not mutations_list:
            continue
        for mutation in mutations_list:
            from_regexp = mutation['from']
            url_match = re.search(from_regexp, url)
            if not url_match:
                continue
            components = url_match.groupdict()
            mutate_results.append((
                mutation['to'].format(**components),
                mutation.get('headers', set())
            ))
    return mutate_results


def transform(scheme_data, extracted_data):
    transforms = scheme_data.get('transforms', [])
    if transforms:
        for t in transforms:
            logging.debug(t)
            try:
                extracted_data = t(extracted_data)
            except PROCESS_ERRORS as e:
                logging.debug(f'Transform error: {e}')
                extracted_data = {}
            logging.debug(extracted_data)
    return extracted_data


def map_fields(scheme_data, transformed_data):
    values = {}
    for name, get_field in scheme_data['fields'].items():
        try:
            value = get_field(transformed_data)
            values[name] = str(value) if value not in (None, [], {}) else ''
        except PROCESS_ERRORS as e:
            logging.debug(f'Unable to extact field {name}: {e}')
    return values


def extract(page):
    for scheme_name, scheme_data in schemes.items():
        flags = scheme_data['flags']
        found = all([flag in page for flag in flags])

        if found:
            logging.info('%s has been detected' % scheme_name)
            if 'message' in scheme_data:
                logging.info(scheme_data['message'])
        else:
            continue

        use_regexp_group = 'regex' in scheme_data
        use_html_parser = 'bs' in scheme_data

        if not any([use_regexp_group, use_html_parser]):
            logging.info('Could not extract!')

        values = {}

        if use_regexp_group:
            regexp_group = re.search(scheme_data['regex'], page, re.MULTILINE)
            if not regexp_group:
                logging.debug('Unable to extract with regexp!')
                continue

            if scheme_data.get('extract_json', False):
                extracted = regexp_group.group(1)
                logging.debug('Extracted: %s', extracted)

                transformed = transform(scheme_data, extracted)

                json_data = json.loads(transformed)

                if json_data == {}:
                    logging.debug('Unabled to extract json!')
                    continue

                loaded_json_str = json.dumps(json_data, indent=4, sort_keys=True)

                logging.debug(loaded_json_str)
                if logging.root.level == logging.DEBUG:
                    with open('debug_extracted.json', 'w') as f:
                        f.write(loaded_json_str)

                values = map_fields(scheme_data, json_data)
            else:
                groupdict = regexp_group.groupdict()
                if groupdict:
                    values = groupdict
                else:
                    extracted = regexp_group.group(1)
                    logging.debug('Extracted: %s', extracted)

                    transformed_data = transform(scheme_data, extracted)
                    values = map_fields(scheme_data, transformed_data)

        if use_html_parser:
            soup = bs(page, 'html.parser')
            for name, get_field in scheme_data['fields'].items():
                try:
                    value = get_field(soup)
                    values[name] = str(value) if value != None else ''
                except PROCESS_ERRORS as e:
                    logging.debug(f'BS extract error: {e}')

        for p in POSTPROCESSORS:
            try:
                additonal_data = p(values).process()
                values.update(additonal_data)
            except PROCESS_ERRORS as e:
                logging.debug('Postprocess error: ', e)

        return {a: b for a, b in values.items() if b or type(b) == bool}

    # all schemes have been checked
    return {}
