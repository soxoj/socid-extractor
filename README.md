# socid_extractor

Extract information about a user from profile webpages / API responses and save it in machine-readable format.

## Usage

As a command-line tool:
```
$ socid_extractor --url https://www.deviantart.com/muse1908
country: France
created_at: 2005-06-16 18:17:41
gender: female
username: Muse1908
website: www.patreon.com/musemercier
links: ['https://www.facebook.com/musemercier', 'https://www.instagram.com/muse.mercier/', 'https://www.patreon.com/musemercier']
tagline: Nothing worth having is easy...
```

Without installing: 
```
$ ./run.py --url https://www.deviantart.com/muse1908
```

As a Python library:
```
>>> import socid_extractor, requests
>>> r = requests.get('https://www.patreon.com/annetlovart')
>>> socid_extractor.extract(r.text)
{'patreon_id': '33913189', 'patreon_username': 'annetlovart', 'fullname': 'Annet Lovart', 'links': "['https://www.facebook.com/322598031832479', 'https://www.instagram.com/annet_lovart', 'https://twitter.com/annet_lovart', 'https://youtube.com/channel/UClDg4ntlOW_1j73zqSJxHHQ']"}
```

## Installation

    $ pip3 install socid-extractor

The latest development version can be installed directly from GitHub:

    $ pip3 install -U git+https://github.com/soxoj/socid_extractor.git

## Sites and methods

[More than 100 methods](https://github.com/soxoj/socid-extractor/blob/master/METHODS.md) for different sites and platforms are supported!

- Google (all documents pages, maps contributions), cookies required
- Yandex (disk, albums, znatoki, music, realty, collections), cookies required to prevent captcha blocks
- Mail.ru (my.mail.ru user mainpage, photo, video, games, communities)
- Facebook (user & group pages)
- VK.com (user page)
- OK.ru (user page)
- Instagram
- Reddit
- Medium
- Flickr
- Tumblr
- TikTok
- GitHub

...and many others.

You can also check [tests file](https://github.com/soxoj/socid-extractor/blob/master/tests/test_e2e.py) for data examples, [schemes file](https://github.com/soxoj/socid-extractor/blob/master/socid_extractor/schemes.py) to expore all the methods.

## When it may be useful

- Getting all available info by the username or/and account UID. Examples: [Week in OSINT](https://medium.com/week-in-osint/getting-a-grasp-on-googleids-77a8ab707e43), [OSINTCurious](https://osintcurio.us/2019/10/01/searching-instagram-part-2/)
- Users tracking, checking that the account was previously known (by ID) even if all public info has changed. Examples: [Aware Online](https://www.aware-online.com/en/importance-of-user-ids-in-social-media-investigations/)
- Searching by commonly used cross-service UIDs (GAIA ID, Facebook UID, Yandex Public ID, etc.)
  - DB leaks of forums and platforms in SQL format
  - Indexed links that contain target profile ID
- Searching for tracking data by comparison with other IDs - [how it works](https://www.eff.org/wp/behind-the-one-way-mirror), [how can it be used](https://www.nytimes.com/interactive/2019/12/19/opinion/location-tracking-cell-phone.html).
- Law enforcement online requests

## Tools using socid_extractor

[Maigret](https://github.com/soxoj/maigret) - powerful namechecker, generate a report with all available info from accounts found.

[TheScrapper](https://github.com/champmq/TheScrapper) - scrape emails, phone numbers and social media accounts from a website.

[YaSeeker](https://github.com/HowToFind-bot/YaSeeker) - tool to gather all available information about Yandex account by login/email.

[Marple](https://github.com/soxoj/marple) - scrape search engines results for a given username.

## Testing

```sh
python3 -m pytest tests/test_e2e.py -n 10  -k 'not cookies' -m 'not github_failed and not rate_limited'
```

## Contributing

Check [separate page](https://github.com/soxoj/socid-extractor/blob/master/CONTRIBUTING.md) if you want to add a new methods of fix anything.
