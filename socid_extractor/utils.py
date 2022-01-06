import logging
import math
import re
from datetime import datetime, timezone
from http.cookies import SimpleCookie

def import_cookiejar(filename):
    from http.cookiejar import MozillaCookieJar
    cookies_obj = MozillaCookieJar(filename)
    cookies_obj.load(ignore_discard=True, ignore_expires=True)
    cookies = {}

    for domain in cookies_obj._cookies.values():
        for key, cookie in list(domain.values())[0].items():
            cookies[key] = cookie.value
    return cookies


def parse_cookies(cookies_str):
    cookies = SimpleCookie()
    cookies.load(cookies_str)
    logging.debug(cookies)
    return {key: morsel.value for key, morsel in cookies.items()}


def join_cookies(cookies: dict):
    return ' ;'.join(f'{k}={v}' for k, v in cookies.items())


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


# support timestamp with milliseconds
# coming to common UTC timezone with print it
def parse_datetime(t):
    if not t:
        return ''
    elif len(str(t)) < 10:
        t = math.floor(datetime.today().timestamp()) - t

    if len(str(t)) == 10 and not '-' in str(t):
        return datetime.fromtimestamp(int(t), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
    elif len(str(t)) == 10 and '-' in str(t):
        return datetime.strptime(t, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S %Z')
    elif len(str(t)) == 13:
        return datetime.fromtimestamp(float(t)/ 1000.0, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S.{} %Z'.format(str(t)[-3:]))
    
    return t
  

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

def extract_periscope_uid(text):
    userId = re.search(r'"userId":"([\w\d]*)"}', text)
    return userId.group(1)
    
def get_mymail_uid(username):
    # TODO: move to external function
    import requests
    req = requests.get('http://appsmail.ru/platform/mail/' + username)
    return req.json()['uid']
