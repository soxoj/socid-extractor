# socid_extractor
Extract accounts' identifiers and other info from personal pages on popular sites.

## When it may be useful

- Getting additional info by the username or/and account UID. Examples: [Week in OSINT - Getting a Grasp on GoogleID’s](https://medium.com/week-in-osint/getting-a-grasp-on-googleids-77a8ab707e43), [OSINTCurious - searching Instagram](https://osintcurio.us/2019/10/01/searching-instagram-part-2/)
- Searching by commonly used cross-service UIDs (GAIA ID, Facebook UID, Yandex Public ID, etc.)
  - DB leaks of forums and platforms in SQL format
  - Indexed links that contain target profile ID
- Searching for tracking data by comparison with other IDs - [how it works](https://www.eff.org/wp/behind-the-one-way-mirror), [how can it be used](https://www.nytimes.com/interactive/2019/12/19/opinion/location-tracking-cell-phone.html).
- Checking that the account was previously known (by ID) even if all public info has changed

## Tools using socid_extractor

[Maigret](https://github.com/soxoj/maigret) - powerful namechecker, generate a report with all available info from accounts found. 

### Other extract methods

- [Obtaining Google IDs from albums and contacts](https://medium.com/week-in-osint/getting-a-grasp-on-googleids-77a8ab707e43)

## Installation

The latest development version can be installed directly from GitHub:

    $ pip3 install -U git+https://github.com/soxoj/socid_extractor.git

## Using
```
$ socid_extractor https://vimeo.com/alexaimephotography
uid: 75857717
name: AlexAimePhotography
username: alexaimephotography
location: France
created_at: 2017-12-06 06:49:28
is_staff: False
links: ['https://500px.com/alexaimephotography', 'https://www.flickr.com/photos/photoambiance/', 'https://www.instagram.com/alexaimephotography/', 'https://www.youtube.com/channel/UC4NiYV3Yqih2WHcwKg4uPuQ', 'https://flii.by/alexaimephotography/']
```

## Platforms

Over 20 services: VK (user), OK (user), Facebook (user, group), Google (all documents, maps contributions), Yandex (disk, albums, znatoki, music, realty, collections), Mail.ru (my.mail.ru user mainpage, photo, video, games, communities), Instagram, Medium, Reddit, GitHub, Bitbucket, Gravatar, Habrahabr, Behance, 500px, Steam, Last.fm, Blogger, SoundCloud, D3, VC.ru, LiveJournal, Keybase, Wikimapia, etc.

Check `tests/test_e2e.py` for examples.
