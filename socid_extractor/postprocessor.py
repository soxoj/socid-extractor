import re
import requests


class Gravatar:
    def __init__(self, data):
        if not 'image' in data:
            self.username = None
            return

        self.url = data['image']
        self.email_hash = self.extract_email_hash()
        if self.email_hash:
            self.username = self.get_username()
        else:
            self.username = None

    def extract_email_hash(self):
        gravatar_re = re.search(r'gravatar\.com/avatar/(\w{32})', self.url)
        if gravatar_re:
            return gravatar_re.group(1)
        return ''

    def make_main_url(self):
        return f'https://gravatar.com/{self.email_hash}'

    def make_en_url(self):
        return f'https://en.gravatar.com/{self.email_hash}'

    def get_username(self):
        gravatar_account_location = requests.head(self.make_en_url())
        username = gravatar_account_location.headers.get('location', '').strip('/')
        if username == 'profiles/no-such-user':
            username = ''

        return username

    def process(self):
        output = {}

        if self.username:
            output = {
                'gravatar_url': self.make_main_url(),
                'gravatar_username': self.username,
                'gravatar_email_md5_hash': self.email_hash,
            }

        return output


class EmailToUsername:
    def __init__(self, data):
        self.data = data

    def process(self):
        output = {}

        for k, v in self.data.items():
            if v and v[0] in "'[{\"":
                continue
            if 'email' in k and '@' in v:
                new_k = k + '_username'
                supposed_username = v.split('@')[0]
                output[new_k] = supposed_username

        return output


class YandexUsernameToEmail:
    def __init__(self, data):
        self.data = data

    def process(self):
        output = {}
        email = None

        if 'yandex_uid' in self.data or 'yandex_public_id' in self.data:
            if 'username' in self.data and self.data['username']:
                email = self.data['username'] + '@yandex.ru'
                output['email'] = email

        return output


POSTPROCESSORS = [Gravatar, EmailToUsername, YandexUsernameToEmail]
