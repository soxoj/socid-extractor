# socid_extractor

Extract information about a user from profile webpages / API responses and save it in machine-readable format.

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

[YaSeeker](https://github.com/HowToFind-bot/YaSeeker) - tool to gather all available information about Yandex account by login/email.

## Installation

    $ pip3 install socid-extractor

The latest development version can be installed directly from GitHub:

    $ pip3 install -U git+https://github.com/soxoj/socid_extractor.git

## Using

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

## Sites

- Google (all documents pages, maps contributions), cookies required
- Yandex (disk, albums, znatoki, music, realty, collections), cookies required to prevent captcha blocks
- Facebook (user & group pages)
- Instagram
- Reddit
- Medium
- Flickr
- Tumblr
- TikTok
- GitHub
- VK (user page)
- OK (user page)
- Mail.ru (my.mail.ru user mainpage, photo, video, games, communities)

...and many others.

Check [tests file](./tests/test_e2e.py) for extracted data examples, [schemes file](./socid_extractor/schemes.py) to check all supported sites.
