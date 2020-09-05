# socid_extractor
Extract accounts' identifiers from personal pages on various platforms.

## When it may be useful

- Checking that the account was previously known even if all public info has changed
- Getting additional info by the account UID ([Google](https://medium.com/week-in-osint/getting-a-grasp-on-googleids-77a8ab707e43), [Instagram](https://osintcurio.us/2019/10/01/searching-instagram-part-2/), etc.)
- Searching by commonly used cross-service UIDs (Facebook, Yandex, etc.)
  - DB leaks of forums and platforms in SQL format
  - Indexed links that contain target profile ID
- Searching for tracking data by comparison with other IDs - [how it works](https://www.eff.org/wp/behind-the-one-way-mirror), [how can it be used](https://www.nytimes.com/interactive/2019/12/19/opinion/location-tracking-cell-phone.html).

### Other extract methods

- [Obtaining Google IDs from albums and contacts](https://medium.com/week-in-osint/getting-a-grasp-on-googleids-77a8ab707e43)

## Using
```
$ ./socid_extractor/socid_extractor.py https://medium.com/@lys1n
Medium has been detected
uid: 4894fec6b289
username: lys1n
name: Марк Лясин
twitter_username: lys1n
facebook_uid: 1726256597385716
```

## Platforms

Over 20 services: VK (user), OK (user), Facebook (user, group), Google (all documents, maps contributions), Yandex (disk, albums, znatoki, music, realty, collections), Mail.ru (my.mail.ru user mainpage, photo, video, games, communities), Instagram, Medium, Reddit, GitHub, Bitbucket, Gravatar, Habrahabr, Behance, 500px, Steam, Last.fm, Blogger, SoundCloud, D3, VC.ru, LiveJournal, Keybase, Wikimapia.

Check `test_e2e.py` for examples.

## TODO

- [ ] Twitch - API requests only, [Chrome extension available](https://chrome.google.com/webstore/detail/twitch-username-and-user/laonpoebfalkjijglbjbnkfndibbcoon)
- [ ] Jira - auth required for profile page
- [ ] Disqus - API-requests only, [example](https://disqus.com/api/3.0/users/details?user=username%3Arohfsim&attach=userFlaggedUser&api_key=E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F)
- [ ] mssg.me