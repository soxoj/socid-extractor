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


def get_gravatar_email_hash(image_url):
    gravatar_re = re.search(r'gravatar\.com/avatar/(\w{32})', image_url)
    if gravatar_re:
        return gravatar_re.group(1)
    return ''


def get_gravatar_url(image_url):
    email_hash = get_gravatar_email_hash(image_url)
    if email_hash:
        return f'https://gravatar.com/{email_hash}'
    return ''

def get_gravatar_username(image_url):
    username = ''
    email_hash = get_gravatar_email_hash(image_url)
    if email_hash:
        gravatar_account_location = requests.head(f'https://en.gravatar.com/{email_hash}')
        username = gravatar_account_location.headers.get('location', '').strip('/')
        if username == 'profiles/no-such-user':
            username = ''
    return username


def extract_digits(text):
    digits_re = re.search(r'\d+', text)
    if digits_re:
        return digits_re[0]
    return ''
