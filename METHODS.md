# Supported sites and methods

| № | Method | Test data | Notes |
| --- | --- | --- | --- |
0 | Twitter HTML |  |  |
1 | Twitter Shadowban | [twitter_shadowban](https://github.com/soxoj/socid-extractor/search?q=test_twitter_shadowban) | down |
2 | Twitter GraphQL API |  |  |
3 | Facebook user profile | [facebook_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_facebook_user_profile) | requests from GitHub Actions CI servers are blocked, requires facebookexternalhit UA; use url_mutations via CLI |
4 | Facebook group | [facebook_group](https://github.com/soxoj/socid-extractor/search?q=test_facebook_group) | broken |
5 | GitHub HTML | [github_html](https://github.com/soxoj/socid-extractor/search?q=test_github_html) |  |
6 | GitHub API | [github_api](https://github.com/soxoj/socid-extractor/search?q=test_github_api) | broken |
7 | Gitlab API |  |  |
8 | Patreon | [patreon](https://github.com/soxoj/socid-extractor/search?q=test_patreon) | broken |
9 | Flickr | [flickr](https://github.com/soxoj/socid-extractor/search?q=test_flickr) | failed from github CI infra IPs |
10 | Yandex Disk file | [yandex_disk](https://github.com/soxoj/socid-extractor/search?q=test_yandex_disk) | broken |
11 | Yandex Disk photoalbum |  |  |
12 | Yandex Music AJAX request | [yandex_music_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_music_user_profile) | captcha |
13 | Yandex Q (Znatoki) user profile |  |  |
14 | Yandex Market user profile |  |  |
15 | Yandex Music API |  |  |
16 | Yandex Realty offer |  |  |
17 | Yandex Collections |  |  |
18 | Yandex Collections API | [yandex_collections_api](https://github.com/soxoj/socid-extractor/search?q=test_yandex_collections_api) | service no longer public |
19 | Yandex Reviews user profile | [yandex_reviews](https://github.com/soxoj/socid-extractor/search?q=test_yandex_reviews) | anti-bot / captcha / rate limiting from the site |
20 | Yandex Zen user profile | [yandex_zen_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_zen_user_profile) | failed from github CI infra IPs |
21 | Yandex messenger search API |  |  |
22 | Yandex messenger profile API |  |  |
23 | Yandex Bugbounty user profile |  |  |
24 | Yandex O | [yandex_o_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_o_user_profile) | down. service no longer exists |
25 | VK user profile foaf page | [vk_foaf](https://github.com/soxoj/socid-extractor/search?q=test_vk_foaf), [vk_user_profile_no_username](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_no_username) | VK foaf.php returns empty body for unauthenticated clients (2026), VK web is SPA; static fetch has no embed with ownerId (2026) |
26 | VK user profile | [vk_blocked_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_vk_blocked_user_profile), [vk_closed_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_vk_closed_user_profile), [vk_user_profile_full](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_full), [vk_user_profile_no_username](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_no_username) | broken, VK web is SPA; static fetch has no embed with ownerId (2026), VK web is SPA; static fetch has no embed with ownerId (2026), VK web is SPA; static fetch has no embed with ownerId (2026) |
27 | VK closed user profile |  |  |
28 | VK blocked user profile |  |  |
29 | Gravatar | [gravatar](https://github.com/soxoj/socid-extractor/search?q=test_gravatar) | broken |
30 | Instagram | [instagram](https://github.com/soxoj/socid-extractor/search?q=test_instagram) | requests from GitHub Actions CI servers are blocked, broken. needs deeper rework |
31 | Instagram API | [instagram_api](https://github.com/soxoj/socid-extractor/search?q=test_instagram_api) | requests from GitHub Actions CI servers are blocked |
32 | Instagram page JSON | [instagram](https://github.com/soxoj/socid-extractor/search?q=test_instagram) | requests from GitHub Actions CI servers are blocked, broken. needs deeper rework |
33 | Spotify API |  |  |
34 | EyeEm | [eyeem](https://github.com/soxoj/socid-extractor/search?q=test_eyeem) | EyeEm returns 403 for automated clients (2026) |
35 | Medium | [medium](https://github.com/soxoj/socid-extractor/search?q=test_medium) |  |
36 | Odnoklassniki | [odnoklassniki](https://github.com/soxoj/socid-extractor/search?q=test_odnoklassniki) |  |
37 | Habrahabr HTML (old) |  |  |
38 | Habrahabr JSON | [habr](https://github.com/soxoj/socid-extractor/search?q=test_habr), [habr_no_image](https://github.com/soxoj/socid-extractor/search?q=test_habr_no_image) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
39 | My Mail.ru |  |  |
40 | Behance | [behance](https://github.com/soxoj/socid-extractor/search?q=test_behance) | broken |
41 | Blogger | [blogger](https://github.com/soxoj/socid-extractor/search?q=test_blogger) | Failed in GitHub CI |
42 | D3.ru | [d3](https://github.com/soxoj/socid-extractor/search?q=test_d3) |  |
43 | Gitlab |  |  |
44 | 500px GraphQL API | [500px](https://github.com/soxoj/socid-extractor/search?q=test_500px) | non-actual, 500px requires POST requests for now |
45 | Google Document API | [google_documents](https://github.com/soxoj/socid-extractor/search?q=test_google_documents) |  |
46 | Google Document |  |  |
47 | Google Maps contributions |  |  |
48 | YouTube ytInitialData |  |  |
49 | Youtube Channel |  |  |
50 | Bitbucket | [bitbucket](https://github.com/soxoj/socid-extractor/search?q=test_bitbucket) | Bitbucket UI/embed changed; test user URL 404 (2026) |
51 | Pinterest API | [pinterest_account](https://github.com/soxoj/socid-extractor/search?q=test_pinterest_account), [pinterest_api](https://github.com/soxoj/socid-extractor/search?q=test_pinterest_api) | requests from GitHub Actions CI servers are blocked, broken |
52 | Pinterest profile/board page |  |  |
53 | Reddit | [reddit](https://github.com/soxoj/socid-extractor/search?q=test_reddit) | broken |
54 | Steam | [steam](https://github.com/soxoj/socid-extractor/search?q=test_steam) | cloudflare |
55 | Steam Addiction |  |  |
56 | Stack Overflow & similar |  |  |
57 | SoundCloud | [soundcloud](https://github.com/soxoj/socid-extractor/search?q=test_soundcloud) | SoundCloud returns 403 / empty embed for automated clients (2026) |
58 | TikTok | [tiktok](https://github.com/soxoj/socid-extractor/search?q=test_tiktok), [tiktok_hydration_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tiktok_hydration_e2e) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
59 | TikTok (legacy SIGI_STATE) | [tiktok_hydration_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tiktok_hydration_e2e) | requests from GitHub Actions CI servers are blocked |
60 | Picsart API | [picsart_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_picsart_api_e2e) |  |
61 | VC.ru |  |  |
62 | LiveJournal | [livejournal](https://github.com/soxoj/socid-extractor/search?q=test_livejournal) |  |
63 | MySpace | [myspace](https://github.com/soxoj/socid-extractor/search?q=test_myspace) | doesnt work without proxy, 503 error |
64 | Keybase API |  |  |
65 | Wikimapia |  |  |
66 | Vimeo HTML |  |  |
67 | Vimeo GraphQL API |  |  |
68 | DeviantArt | [deviantart](https://github.com/soxoj/socid-extractor/search?q=test_deviantart) | it works but is skipped for the sake of successful tests |
69 | mssg.me | [mssg_me](https://github.com/soxoj/socid-extractor/search?q=test_mssg_me) | broken |
70 | Telegram | [telegram](https://github.com/soxoj/socid-extractor/search?q=test_telegram) |  |
71 | BuzzFeed | [buzzfeed](https://github.com/soxoj/socid-extractor/search?q=test_buzzfeed) | requests from GitHub Actions CI servers are blocked |
72 | Linktree | [linktree](https://github.com/soxoj/socid-extractor/search?q=test_linktree) | broken |
73 | Twitch | [twitch](https://github.com/soxoj/socid-extractor/search?q=test_twitch) | broken |
74 | vBulletinEngine |  |  |
75 | Tumblr (default theme) |  |  |
76 | 1x.com |  |  |
77 | Last.fm | [last_fm](https://github.com/soxoj/socid-extractor/search?q=test_last_fm) |  |
78 | Ask.fm | [ask_fm](https://github.com/soxoj/socid-extractor/search?q=test_ask_fm) | broken |
79 | Launchpad | [launchpad](https://github.com/soxoj/socid-extractor/search?q=test_launchpad) | requests from GitHub Actions CI servers are blocked |
80 | Xakep.ru |  |  |
81 | Tproger.ru | [tproger_ru](https://github.com/soxoj/socid-extractor/search?q=test_tproger_ru) | no more author pages for now |
82 | Jsfiddle.net |  |  |
83 | Disqus API | [disqus_api](https://github.com/soxoj/socid-extractor/search?q=test_disqus_api) |  |
84 | uCoz-like profile page |  |  |
85 | uID.me |  |  |
86 | tapd | [tapd](https://github.com/soxoj/socid-extractor/search?q=test_tapd) | down |
87 | freelancer.com |  |  |
88 | Yelp | [yelp_userid](https://github.com/soxoj/socid-extractor/search?q=test_yelp_userid), [yelp_username](https://github.com/soxoj/socid-extractor/search?q=test_yelp_username) | broken, broken |
89 | Trello API | [trello](https://github.com/soxoj/socid-extractor/search?q=test_trello) |  |
90 | Weibo | [weibo](https://github.com/soxoj/socid-extractor/search?q=test_weibo) | needs rework, cookies are required to get content, requests from GitHub Actions CI servers are blocked |
91 | ICQ | [icq](https://github.com/soxoj/socid-extractor/search?q=test_icq) | broken forever |
92 | Pastebin | [pastebin](https://github.com/soxoj/socid-extractor/search?q=test_pastebin) |  |
93 | Periscope |  |  |
94 | Imgur API | [imgur_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_imgur_api_e2e) |  |
95 | PayPal |  |  |
96 | Tinder | [tinder](https://github.com/soxoj/socid-extractor/search?q=test_tinder) | broken |
97 | ifunny.co | [ifunny_co](https://github.com/soxoj/socid-extractor/search?q=test_ifunny_co) |  |
98 | Wattpad API | [wattpad_api](https://github.com/soxoj/socid-extractor/search?q=test_wattpad_api) |  |
99 | Kik | [kik](https://github.com/soxoj/socid-extractor/search?q=test_kik) | broken |
100 | Docker Hub API | [docker_hub_api](https://github.com/soxoj/socid-extractor/search?q=test_docker_hub_api) |  |
101 | Mixcloud API | [mixcloud_api](https://github.com/soxoj/socid-extractor/search?q=test_mixcloud_api) |  |
102 | binarysearch API | [binarysearch_api](https://github.com/soxoj/socid-extractor/search?q=test_binarysearch_api) | down |
103 | pr0gramm API | [pr0gramm_api](https://github.com/soxoj/socid-extractor/search?q=test_pr0gramm_api) |  |
104 | Aparat API | [aparat_api](https://github.com/soxoj/socid-extractor/search?q=test_aparat_api) | broken |
105 | UnstoppableDomains |  |  |
106 | memory.lol | [memory_lol](https://github.com/soxoj/socid-extractor/search?q=test_memory_lol) |  |
107 | Duolingo API | [duolingo_api](https://github.com/soxoj/socid-extractor/search?q=test_duolingo_api) |  |
108 | TwitchTracker |  |  |
109 | Chess.com API | [chess_com_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_chess_com_api_e2e) |  |
110 | Roblox user API | [roblox_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_roblox_api_e2e) |  |
111 | Roblox username lookup API |  |  |
112 | MyAnimeList profile |  |  |
113 | XVideos profile |  |  |
114 | lnk.bio |  |  |
115 | Wikipedia user API |  |  |
116 | Fandom MediaWiki API |  |  |
117 | Substack public profile API |  |  |
118 | Lesswrong GraphQL API |  |  |
119 | hashnode GraphQL API |  |  |
120 | Rarible API |  |  |
121 | CSSBattle |  |  |
122 | Max (max.ru) profile |  |  |
123 | Bluesky API |  |  |
124 | Scratch API |  |  |
125 | DailyMotion API |  |  |
126 | SlideShare |  |  |
127 | WordPress.org Profile |  |  |
128 | Weebly |  |  |
129 | Calendly |  |  |
130 | Google Play Developer |  |  |
131 | Amazon Author |  |  |
132 | Habr |  |  |
133 | Taplink |  |  |
134 | Product Hunt |  |  |
135 | Chess.com HTML | [chess_com_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_chess_com_html_e2e) |  |
136 | Roblox HTML | [roblox_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_roblox_html_e2e) |  |
137 | Threads |  |  |

The table has been updated at 2026-04-02 19:18:27.206205 UTC
