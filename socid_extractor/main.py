import logging
from http.cookies import SimpleCookie

import requests

from .schemes import *

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
}


def parse_cookies(cookies_str):
    cookies = SimpleCookie()
    cookies.load(cookies_str)
    logging.debug(cookies)
    return {key: morsel.value for key, morsel in cookies.items()}


def parse(url, cookies_str='', timeout=3):
    cookies = parse_cookies(cookies_str)
    page = requests.get(url, headers=HEADERS, cookies=cookies, allow_redirects=True, timeout=(timeout, timeout))
    logging.debug('Server response: %s', page.text)
    logging.debug('Status code: %d', page.status_code)
    return page.text, page.status_code


def extract(page):
    for scheme_name, scheme_data in schemes.items():
        flags = scheme_data['flags']
        found = all([flag in page for flag in flags])

        if found:
            logging.info('%s has been detected' % scheme_name)
            if 'message' in scheme_data:
                print(scheme_data['message'])
        else:
            continue

        info = re.search(scheme_data['regex'], page)

        if info:
            if scheme_data.get('extract_json', False):
                values = {}
                extracted = info.group(1)

                logging.debug('Extracted: %s', extracted)

                transforms = scheme_data.get('transforms', [])
                if transforms:
                    for t in transforms:
                        logging.debug(t)
                        extracted = t(extracted)
                        logging.debug(extracted)

                json_data = json.loads(extracted)

                if json_data == {}:
                    continue

                loaded_json_str = json.dumps(json_data, indent=4, sort_keys=True)

                logging.debug(loaded_json_str)
                if logging.root.level == logging.DEBUG:
                    with open('debug_extracted.json', 'w') as f:
                        f.write(loaded_json_str)

                for name, get_field in scheme_data['fields'].items():
                    value = get_field(json_data)
                    values[name] = str(value) if value != None else ''
            else:
                values = info.groupdict()

            return {a: b for a, b in values.items() if b or type(b) == bool}
        else:
            logging.info('Could not extract!')
    return {}
