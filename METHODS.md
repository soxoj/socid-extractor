# Supported sites and methods

| № | Method | Test data | Notes |
| --- | --- | --- | --- |
0 | Twitter HTML |  |  |
1 | Twitter Shadowban | [twitter_shadowban](https://github.com/soxoj/socid-extractor/search?q=test_twitter_shadowban) | down |
2 | Twitter GraphQL API |  |  |
3 | Facebook user profile | [facebook_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_facebook_user_profile) | requests from GitHub Actions CI servers are blocked |
4 | Facebook group | [facebook_group](https://github.com/soxoj/socid-extractor/search?q=test_facebook_group) | broken |
5 | GitHub HTML | [github_html](https://github.com/soxoj/socid-extractor/search?q=test_github_html) |  |
6 | GitHub API | [github_api](https://github.com/soxoj/socid-extractor/search?q=test_github_api) |  |
7 | Gitlab API |  |  |
8 | Patreon | [patreon](https://github.com/soxoj/socid-extractor/search?q=test_patreon) |  |
9 | Flickr | [flickr](https://github.com/soxoj/socid-extractor/search?q=test_flickr) | failed from github CI infra IPs |
10 | Yandex Disk file | [yandex_disk](https://github.com/soxoj/socid-extractor/search?q=test_yandex_disk) |  |
11 | Yandex Disk photoalbum |  |  |
12 | Yandex Music AJAX request | [yandex_music_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_music_user_profile) | captcha |
13 | Yandex Q (Znatoki) user profile |  |  |
14 | Yandex Market user profile |  |  |
15 | Yandex Music API |  |  |
16 | Yandex Realty offer |  |  |
17 | Yandex Collections |  |  |
18 | Yandex Collections API | [yandex_collections_api](https://github.com/soxoj/socid-extractor/search?q=test_yandex_collections_api) |  |
19 | Yandex Reviews user profile | [yandex_reviews](https://github.com/soxoj/socid-extractor/search?q=test_yandex_reviews) | anti-bot / captcha / rate limiting from the site |
20 | Yandex Zen user profile | [yandex_zen_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_zen_user_profile) | failed from github CI infra IPs |
21 | Yandex messenger search API |  |  |
22 | Yandex messenger profile API |  |  |
23 | Yandex Bugbounty user profile |  |  |
24 | Yandex O | [yandex_o_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_o_user_profile) |  |
25 | VK user profile foaf page | [vk_foaf](https://github.com/soxoj/socid-extractor/search?q=test_vk_foaf), [vk_user_profile_no_username](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_no_username) |  |
26 | VK user profile | [vk_blocked_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_vk_blocked_user_profile), [vk_closed_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_vk_closed_user_profile), [vk_user_profile_full](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_full), [vk_user_profile_no_username](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_no_username) |  |
27 | VK closed user profile |  |  |
28 | VK blocked user profile |  |  |
29 | Gravatar | [gravatar](https://github.com/soxoj/socid-extractor/search?q=test_gravatar) |  |
30 | Instagram | [instagram](https://github.com/soxoj/socid-extractor/search?q=test_instagram) | requests from GitHub Actions CI servers are blocked |
31 | Instagram API | [instagram_api](https://github.com/soxoj/socid-extractor/search?q=test_instagram_api) | requests from GitHub Actions CI servers are blocked |
32 | Instagram page JSON | [instagram](https://github.com/soxoj/socid-extractor/search?q=test_instagram) | requests from GitHub Actions CI servers are blocked |
33 | Spotify API |  |  |
34 | EyeEm | [eyeem](https://github.com/soxoj/socid-extractor/search?q=test_eyeem) |  |
35 | Medium | [medium](https://github.com/soxoj/socid-extractor/search?q=test_medium) |  |
36 | Odnoklassniki | [odnoklassniki](https://github.com/soxoj/socid-extractor/search?q=test_odnoklassniki) |  |
37 | Habrahabr HTML (old) |  |  |
38 | Habrahabr JSON | [habr](https://github.com/soxoj/socid-extractor/search?q=test_habr), [habr_no_image](https://github.com/soxoj/socid-extractor/search?q=test_habr_no_image) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
39 | My Mail.ru |  |  |
40 | Behance | [behance](https://github.com/soxoj/socid-extractor/search?q=test_behance) |  |
41 | Blogger | [blogger](https://github.com/soxoj/socid-extractor/search?q=test_blogger) | Failed in GitHub CI |
42 | D3.ru | [d3](https://github.com/soxoj/socid-extractor/search?q=test_d3) |  |
43 | Gitlab |  |  |
44 | 500px GraphQL API | [500px](https://github.com/soxoj/socid-extractor/search?q=test_500px) | non-actual, 500px requires POST requests for now |
45 | Google Document API | [google_documents](https://github.com/soxoj/socid-extractor/search?q=test_google_documents) |  |
46 | Google Document |  |  |
47 | Google Maps contributions |  |  |
48 | Youtube Channel |  |  |
49 | Bitbucket | [bitbucket](https://github.com/soxoj/socid-extractor/search?q=test_bitbucket) |  |
50 | Pinterest API | [pinterest_api](https://github.com/soxoj/socid-extractor/search?q=test_pinterest_api) |  |
51 | Pinterest profile/board page |  |  |
52 | Reddit | [reddit](https://github.com/soxoj/socid-extractor/search?q=test_reddit) |  |
53 | Steam | [steam](https://github.com/soxoj/socid-extractor/search?q=test_steam) | cloudflare |
54 | Steam Addiction |  |  |
55 | Stack Overflow & similar |  |  |
56 | SoundCloud | [soundcloud](https://github.com/soxoj/socid-extractor/search?q=test_soundcloud) |  |
57 | TikTok | [tiktok](https://github.com/soxoj/socid-extractor/search?q=test_tiktok) | requests from GitHub Actions CI servers are blocked |
58 | VC.ru |  |  |
59 | LiveJournal | [livejournal](https://github.com/soxoj/socid-extractor/search?q=test_livejournal) |  |
60 | MySpace | [myspace](https://github.com/soxoj/socid-extractor/search?q=test_myspace) | doesnt work without proxy, 503 error |
61 | Keybase API |  |  |
62 | Wikimapia |  |  |
63 | Vimeo HTML |  |  |
64 | Vimeo GraphQL API |  |  |
65 | DeviantArt | [deviantart](https://github.com/soxoj/socid-extractor/search?q=test_deviantart) |  |
66 | mssg.me | [mssg_me](https://github.com/soxoj/socid-extractor/search?q=test_mssg_me) |  |
67 | Telegram | [telegram](https://github.com/soxoj/socid-extractor/search?q=test_telegram) |  |
68 | BuzzFeed | [buzzfeed](https://github.com/soxoj/socid-extractor/search?q=test_buzzfeed) |  |
69 | Linktree | [linktree](https://github.com/soxoj/socid-extractor/search?q=test_linktree) |  |
70 | Twitch | [twitch](https://github.com/soxoj/socid-extractor/search?q=test_twitch) |  |
71 | vBulletinEngine |  |  |
72 | Tumblr (default theme) |  |  |
73 | 1x.com |  |  |
74 | Last.fm | [last_fm](https://github.com/soxoj/socid-extractor/search?q=test_last_fm) |  |
75 | Ask.fm | [ask_fm](https://github.com/soxoj/socid-extractor/search?q=test_ask_fm) |  |
76 | Launchpad | [launchpad](https://github.com/soxoj/socid-extractor/search?q=test_launchpad) |  |
77 | Xakep.ru |  |  |
78 | Tproger.ru | [tproger_ru](https://github.com/soxoj/socid-extractor/search?q=test_tproger_ru) | no more author pages for now |
79 | Jsfiddle.net |  |  |
80 | Disqus API | [disqus_api](https://github.com/soxoj/socid-extractor/search?q=test_disqus_api) |  |
81 | uCoz-like profile page |  |  |
82 | uID.me |  |  |
83 | tapd | [tapd](https://github.com/soxoj/socid-extractor/search?q=test_tapd) |  |
84 | freelancer.com |  |  |
85 | Yelp | [yelp_userid](https://github.com/soxoj/socid-extractor/search?q=test_yelp_userid), [yelp_username](https://github.com/soxoj/socid-extractor/search?q=test_yelp_username) |  |
86 | Trello API | [trello](https://github.com/soxoj/socid-extractor/search?q=test_trello) |  |
87 | Weibo | [weibo](https://github.com/soxoj/socid-extractor/search?q=test_weibo) | cookies are required to get content, requests from GitHub Actions CI servers are blocked |
88 | ICQ | [icq](https://github.com/soxoj/socid-extractor/search?q=test_icq) |  |
89 | Pastebin | [pastebin](https://github.com/soxoj/socid-extractor/search?q=test_pastebin) |  |
90 | Periscope |  |  |
91 | Imgur API |  |  |
92 | PayPal |  |  |
93 | Tinder | [tinder](https://github.com/soxoj/socid-extractor/search?q=test_tinder) |  |
94 | ifunny.co | [ifunny_co](https://github.com/soxoj/socid-extractor/search?q=test_ifunny_co) |  |
95 | Wattpad API | [wattpad_api](https://github.com/soxoj/socid-extractor/search?q=test_wattpad_api) |  |
96 | Kik | [kik](https://github.com/soxoj/socid-extractor/search?q=test_kik) |  |
97 | Docker Hub API | [docker_hub_api](https://github.com/soxoj/socid-extractor/search?q=test_docker_hub_api) |  |
98 | Mixcloud API | [mixcloud_api](https://github.com/soxoj/socid-extractor/search?q=test_mixcloud_api) |  |
99 | binarysearch API | [binarysearch_api](https://github.com/soxoj/socid-extractor/search?q=test_binarysearch_api) |  |
100 | pr0gramm API | [pr0gramm_api](https://github.com/soxoj/socid-extractor/search?q=test_pr0gramm_api) |  |
101 | Aparat API | [aparat_api](https://github.com/soxoj/socid-extractor/search?q=test_aparat_api) |  |
102 | UnstoppableDomains |  |  |

The table has been updated at 2023-07-07 19:00:31.026542 UTC
