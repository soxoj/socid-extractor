#!/usr/bin/env python3
import json
import sys
import re

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
        'flags': ['cdn.behance.net'],
        'regex': r'{"id":(?P<uid>\d+),"first_name":"(?P<first_name>[^"]+)","last_name":"(?P<last_name>[^"]+)","username":"(?P<username>[^"]+)"',
     },
     '500px': {
        'flags': ['//assetcdn.500px.org'],
        'regex': r'{"userdata":{"id":.+?"groups":\[\]}}',
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
}


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
}

cookies = {
    'ilo0': '1',
} 


def parse(url):
    page = requests.get(url, headers=headers, cookies=cookies, allow_redirects=True)
    return page.text


def extract(page):
    for scheme_name, scheme_data in schemes.items():
        flags = scheme_data['flags']
        found = all([flag in page for flag in flags])
        if found:
            print('%s has been detected' % scheme_name)
        else:
            continue
        info = re.search(scheme_data['regex'], page)
        if info:
            if scheme_data.get('extract_json', False):
                values = {}
                json_data = json.loads(info.group(0))
                for name, get_field in scheme_data['fields'].items():
                    values[name] = str(get_field(json_data))
            else:
                values = info.groupdict()

            return {a: b for a, b in values.items() if b}
        else:
            print('Could not extract!')
    return {}


if __name__ == '__main__':
    url = sys.argv[1]
    page = parse(url)
    info = extract(page)
    for key, value in info.items():
        print('%s: %s' % (key, value))
