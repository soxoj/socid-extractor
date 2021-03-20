import math
import re
import requests
from datetime import datetime

def check_empty_object(res):
    return res if res or type(res) == bool else None


def extract_facebook_uid(link):
    avatar_re = re.search(r'graph.facebook.com/(\w+)/picture', link)
    if avatar_re:
        return avatar_re.group(1)
    return None


def get_yandex_profile_pic(default_avatar_id):
    url = 'https://avatars.mds.yandex.net/get-yapic/0/0-0/islands-300'
    if default_avatar_id:
        default_avatar_id = default_avatar_id.replace('user_avatar/yapic/', '')
        url = f'https://avatars.mds.yandex.net/get-yapic/{default_avatar_id}/islands-200'
    return url

def decode_ya_str(val):
    try:
        return val.encode('iso-8859-1').decode('utf-8')
    except:
        return val


def enrich_link(html_url):
    fixed_url = html_url.lstrip('/')
    if fixed_url and not fixed_url.startswith('http'):
        fixed_url = 'https://' + fixed_url
    return fixed_url


def timestamp_to_datetime(t):
    if not t:
        return ''
    elif len(str(t)) < 10:
        t = math.floor(datetime.today().timestamp()) - t

    return datetime.fromtimestamp(int(t))


def extract_digits(text):
    digits_re = re.search(r'\d+', text)
    if digits_re:
        return digits_re[0]
    return ''


def get_ucoz_email(text):
    if text != 'Адрес скрыт':
        return text
    return ''


def get_ucoz_userlink(user_dom_node):
    prompt = user_dom_node.next_sibling.next_sibling.get('onclick')
    user_link = prompt.split("'")[-2]
    return user_link


def get_ucoz_domain(user_dom_node):
    return get_ucoz_userlink(user_dom_node).rsplit('/', 2)[0]


def get_ucoz_image(dom):
    url = dom.find('span', class_='user_avatar').find('img').get('src')
    if url.startswith('http'):
        return url
    domain = get_ucoz_domain(dom.find('div', string='Пользователь:'))
    return domain + url


def get_ucoz_uid_node(dom):
    return dom.find('b', string='uID профиль') or dom.find('b', string='uNet профиль')
