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
        data = {}

        if self.username:
            data = {
                'gravatar_url': self.make_main_url(),
                'gravatar_username': self.username,
                'gravatar_email_hash': self.email_hash,
            }

        return data


POSTPROCESSORS = [Gravatar]
