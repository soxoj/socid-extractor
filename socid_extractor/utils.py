import math
import re
from datetime import datetime


def check_empty_object(res):
    return res if res or type(res) == bool else None


def extract_facebook_uid(link):
    avatar_re = re.search(r'graph.facebook.com/(\w+)/picture', link)
    if avatar_re:
        return avatar_re.group(1)
    return None


def get_yandex_profile_pic(default_avatar_id):
    return f'https://avatars.mds.yandex.net/get-yapic/{default_avatar_id}/islands-200'


def decode_ya_str(val):
    try:
        return val.encode('iso-8859-1').decode('utf-8')
    except:
        return val


def timestamp_to_datetime(t):
    if not t:
        return ''
    elif len(str(t)) < 10:
        t = math.floor(datetime.today().timestamp()) - t

    return datetime.fromtimestamp(int(t))
