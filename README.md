# socid_extractor
Extract accounts' identifiers from personal pages on various platforms.

## When it may be useful

- Checking that the account was previously known even if all public info has changed
- Searching by commonly used cross-service UIDs (Facebook, Yandex, etc.)
  - DB leaks of forums and platforms in SQL format
  - Indexed links that contain target profile ID

## Using
```
$ ./socid_extractor.py https://medium.com/@lys1n
Medium has been detected
uid: 4894fec6b289
username: lys1n
name: Марк Лясин
twitter_username: lys1n
facebook_uid: 1726256597385716
```

## Platforms

Over 20 services: VK (user), OK (user), Facebook (user, group), Google (all documents), Yandex (disk, albums, znatoki, music, realty), Instagram, Medium, Reddit, GitHub, Bitbucket, Habrahabr, My.mail.ru, Behance, 500px, Steam, Last.fm, Blogger, SoundCloud, D3, VC.ru.

Check `test_socid_extractor.py` for examples.

## TODO

- [ ] Twitch - API requests only, [Chrome extension available](https://chrome.google.com/webstore/detail/twitch-username-and-user/laonpoebfalkjijglbjbnkfndibbcoon)
- [ ] LiveJournal
- [ ] Jira
- [ ] Disqus
