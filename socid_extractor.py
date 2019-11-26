#!/usr/bin/env python3
import argparse
import json
import logging
import sys
import re
from http.cookies import SimpleCookie

import requests


schemes = {
    'Yandex Disk file': {
        'flags': ['@yandexdisk', 'yastatic.net'],
        'regex': r'"users":{.*?"uid":"(?P<uid>\d+)","displayName":"(?P<name>.+?)"',
     },
    'Yandex Disk photoalbum': {
        'flags': ['yastatic.net/disk/album', 'isAvailableToAlbum'],
        'regex': r'"display_name":"(?P<name>.*?)","uid":"(?P<uid>\d+)","locale":"\w+","login":"(?P<username>.*?)"',
     },
     'Yandex Music user profile': {
        'flags': ['musicCspLogger'],
        'regex': r'{"uid":"(?P<uid>\d+)","login":"(?P<username>.+?)","name":"(?P<name>.+?)"}',
        # TODO: fix random order, add lastName and firstName
     },
     'Yandex Znatoki user profile': {
        'flags': ['Ya.Znatoki'],
        'regex': r'displayName&quot;:&quot;(?P<name>[^&]+?)&quot;,&quot;uuid&quot;:(?P<yandex_uid>\d+),&quot;.+?login&quot;:&quot;(?P<username>[^&]+?)&quot;.+?&quot;id&quot;:&quot;(?P<uid>[\w-]+)&quot'
     },
     'Yandex Realty offer': {
        'flags': ['realty.yandex.ru/offer'],
        'regex': r'({"routing":{"locationBeforeTransitions.+?});',
        'extract_json': True,
        'fields': {
            'your_yuid': lambda x: x['user']['yuid'],
            'your_uid': lambda x: x['user']['uid'],
            'your_wallet_balance': lambda x: x['user']['walletInfo'].get('balance'),
            'your_emails': lambda x: ', '.join(x['user']['emails']),
            'your_name': lambda x: x['user'].get('displayName'),
            'your_username': lambda x: x['user'].get('defaultEmail'),
            'your_phone': lambda x: x['user'].get('defaultPhone'),
            'uid': lambda x: x['cards']['offers']['author']['id'],
            'name': lambda x: decode_ya_str(x['cards']['offers']['author']['agentName'])
        }
     },
     'VK user profile': {
        'flags': ['var vk =', 'change_current_info'],
        'regex': r'Profile\.init\({"user_id":(?P<uid>\d+).*?(,"loc":"(?P<username>.*?)")?,"back":"(?P<name>.*?)"'
     },
     'Instagram': {
        'flags': ['instagram://user?username'],
        'regex': r'{"id":"(?P<uid>\d+)","username":"(?P<username>.*?)"}',
     },
     'Medium': {
        'flags': ['https://medium.com', 'com.medium.reader'],
        'regex': r'"User:.*?{"id":"(?P<uid>.*?)",.*?,"username":"(?P<username>.*?)",.*?,"name":"(?P<name>.*?)",.*?,"twitterScreenName":"(?P<twitter_username>.*?)","facebookAccountId":"(?P<facebook_uid>.*?)"',
     },
     'Odnoklassniki': {
        'flags': ['OK.startupData'],
        'regex': r'path:"/profile/(?P<uid>\d+)",state:',
     },
     'Habrahabr': {
        'flags': ['habracdn.net'],
        'regex': r'<div class="page-header page-header_full js-user_(?P<uid>\d+)">[\s\S]*?/users/(?P<username>.*?)/',
     },
     'Twitter': {
        'flags': ['abs.twimg.com', 'moreCSSBundles'],
        'regex': r'{&quot;id&quot;:(?P<uid>\d+),&quot;id_str&quot;:&quot;\d+&quot;,&quot;name&quot;:&quot;(?P<username>.*?)&quot;,&quot;screen_name&quot;:&quot;(?P<name>.*?)&quot;'
     },
     'Reddit': {
        'flags': ['www.redditstatic.com', 'displayNamePrefixed'],
        'regex': r'"displayText":"(?P<username>[^\"]+)","hasUserProfile":\w+,"hideFromRobots":\w+,"id":"(?P<uid>.+?)"',
     },
     'Facebook user profile': {
        'flags': ['com.facebook.katana', 'scribe_endpoint'],
        'regex': r'"uri":"[^\"]+\/(?P<username>[^\"\\\/]+?)","entity_id":"(?P<uid>\d+)"',
     },
     'Facebook group': {
        'flags': ['com.facebook.katana', 'XPagesProfileHomeController'],
        'regex': r'"uri":"[^\"]+\/(?P<username>[^\"\\\/]+?)[\\\/]+","entity_id":"(?P<uid>\d+)"',
     },
     'GitHub': {
        'flags': ['github.githubassets.com'],
        'regex': r'data-scope-id="(?P<uid>\d+)" data-scoped-search-url="/search\?user=(?P<username>.+?)"'
     },
     'My Mail.ru': {
        'flags': ['my.mail.ru', 'models/user/journal'],
        'regex': r'"name": "(?P<name>[^"]+)",\s+"id": "(?P<uid>\d+)",[\s\S]+?"email": "(?P<username>[^@]+)@mail.ru"',
     },
     'Behance': {
        'flags': ['behance.net', 'beconfig-store_state'],
        'message': 'Cookies required, ensure you added --cookies "ilo0=1"',
        'regex': r'{"id":(?P<uid>\d+),"first_name":"(?P<first_name>[^"]+)","last_name":"(?P<last_name>[^"]+)","username":"(?P<username>[^"]+)"',
     },
     'Blogger': {
        'flags': ['www.blogger.com/static', 'blogspot.com/feeds/posts'],
        'regex': r'www.blogger.com\/feeds\/(?P<blog_id>\d+)\/posts\/default" \/>\n<link rel="me" href="https:\/\/www.blogger.com\/profile/(?P<uid>\d+)" \/>',
     },
     'D3.ru': {
        'flags': ['feedSettingsHandler.subscribe(this', 'd3.ru/static'],
        'regex': r"feedSettingsHandler.subscribe\(this, 'users', '(?P<uid>\d+)'",
     },
     'Gitlab': {
        'flags': ['gitlab-static.net'],
        'regex': r'abuse_reports.+?user_id=(?P<uid>\d+)"',
     },
     '500px': {
        'flags': ['//assetcdn.500px.org'],
        'regex': r'({"userdata":{"id":.+?"groups":\[\]}})',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['userdata']['id'],
            'username': lambda x: x['userdata']['username'],
            'name': lambda x: x['userdata']['fullname'],
            'qq_username': lambda x: x['userdata']['contacts']['qq'],
            'website': lambda x: x['userdata']['contacts']['website'],
            'blog': lambda x: x['userdata']['contacts']['blog'],
            'lastfm_username': lambda x: x['userdata']['contacts']['lastfm'],
            'facebook_uid': lambda x: x['userdata']['contacts']['facebook'],
            'msn_username': lambda x: x['userdata']['contacts']['MSN'],
            'facebook_page': lambda x: x['userdata']['contacts']['facebookpage'],
            'livejournal_username': lambda x: x['userdata']['contacts']['livejournal'],
            'instagram_username': lambda x: x['userdata']['contacts']['instagram'],
            'twitter_username': lambda x: x['userdata']['contacts']['twitter'],
            'skype_username': lambda x: x['userdata']['contacts']['skype'],
            'thumblr_username': lambda x: x['userdata']['contacts']['thumblr'],
            'gtalk_username': lambda x: x['userdata']['contacts']['gtalk'],
            'icq_uid': lambda x: x['userdata']['contacts']['icq'],
            'flickr_username': lambda x: x['userdata']['contacts']['flickr'],
            'lookatme_username': lambda x: x['userdata']['contacts']['LOOKATME'],
            'googleplus_uid': lambda x: x['userdata']['contacts']['googleplus'],
        }
     },
     'Google document': {
        'flags': ['_docs_flag_initialData'],
        'regex': r'({"docs-ails":"docs_\w+".+?"docs-(comp|fsd|dcr)":\w+})',
        'extract_json': True,
        'message': 'Auth cookies requires, add through --cookies in format "a=1;b=2"n\nTry to run twice to get result.',
        'fields': {
            'your_ls_uid': lambda x: x.get('docs-offline-lsuid'),
            'your_cpf': lambda x: x.get('docs-cpf'),
            'your_username': lambda x: x.get('docs-offline-ue') or x.get('docs-hue'),
            'your_uid': lambda x: x['docs-pid'],
            'org_name': lambda x: x['docs-doddn'],
            'org_domain': lambda x: x['docs-dodn'],
        }
     },
     'Bitbucket': {
        'flags': ['bitbucket.org/account'],
        'regex': r'({"section": {"profile.+?"whats_new_feed":.+?}})',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['global']['targetUser']['uuid'].strip('{}'),
            'username': lambda x: x['global']['targetUser']['nickname'],
            'created_at': lambda x: x['global']['targetUser']['created_on'],
            'is_service': lambda x: x['global']['targetUser']['is_staff'],
        }
     },
     'Steam': {
        'flags': ['store.steampowered.com'],
        'regex': r'({"url":".+?});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['steamid'],
            'name': lambda x: x['personaname'],
            'username': lambda x: [y for y in x['url'].split('/') if y][-1],
        }
     },
     'Stack Overflow & similar': {
        'flags': ['StackExchange.user.init'],
        'regex': r'StackExchange.user.init\({ userId: (?P<uid>\d+), accountId: (?P<stack_exchange_uid>\d+) }\);',
     },
     'SoundCloud': {
        'flags': ['eventlogger.soundcloud.com'],
        'regex': r'catch\(t\){}}\)},(\[{"id":.+?)\);',
        'extract_json': True,
        'message': 'Run with auth cookies to get your ids.',
        'fields': {
            'your_uid': lambda x: x[-2]['data'][0].get('id'),
            'your_name': lambda x: x[-2]['data'][0].get('full_name'),
            'your_username': lambda x: x[-2]['data'][0].get('username'),
            'uid': lambda x: x[-1]['data'][0]['id'],
            'name': lambda x: x[-1]['data'][0]['full_name'],
            'username': lambda x: x[-1]['data'][0]['username'],
        }
     },
     'VC.ru': {
        'flags': ['static-osnova.gcdn.co'],
        'regex': r'({"module.page":{.+});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['module.page']['subsite']['id'],
            'name': lambda x: x['module.page']['subsite']['name'],
            'username': lambda x: x['module.page']['subsite']['url'].split('/')[-1],
        }
     },
     'LiveJournal': {
        'flags': ['Site.journal'],
        'regex': r'Site.journal = ({".+?"});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['id'],
            'is_paid': lambda x: x['is_paid'],
            'is_news': lambda x: x['is_news'],
            'is_identity': lambda x: x['is_identity'],
            'is_medius': lambda x: x['is_medius'],
            'is_permanent': lambda x: x['is_permanent'],
            'is_community': lambda x: x['is_community'],
            'is_personal': lambda x: x['is_personal'],
            'is_suspended': lambda x: x['is_suspended'],
            'is_bad_content': lambda x: x['is_bad_content'],
            'username': lambda x: x['username'],
            'name': lambda x: x['display_username'],
        }
     },
}


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
}


def decode_ya_str(val):
    try:
        return val.encode('iso-8859-1').decode('utf-8')
    except:
        return val

def parse_cookies(cookies_str):
    cookies = SimpleCookie()
    cookies.load(cookies_str)
    logging.debug(cookies)
    return {key: morsel.value for key, morsel in cookies.items()}


def parse(url, cookies_str=''):
    cookies = parse_cookies(cookies_str)
    page = requests.get(url,headers=headers, cookies=cookies, allow_redirects=True)
    logging.debug(page.text)
    logging.debug(page.status_code)
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
                logging.debug(info.group(1))

                json_data = json.loads(info.group(1))

                loaded_json = json.dumps(json_data, indent=4, sort_keys=True)

                logging.debug(loaded_json)
                if logging.root.level == logging.DEBUG:
                    with open('debug_extracted.json', 'w') as f:
                        f.write(loaded_json)

                for name, get_field in scheme_data['fields'].items():
                    value = get_field(json_data)
                    values[name] = str(value) if value != None else ''
            else:
                values = info.groupdict()

            return {a: b for a, b in values.items() if b}
        else:
            print('Could not extract!')
    return {}


if __name__ == '__main__':
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
