# Supported sites and methods

| № | Method | Test data | Notes |
| --- | --- | --- | --- |
0 | Twitter HTML |  |  |
1 | Twitter Shadowban | [twitter_shadowban](https://github.com/soxoj/socid-extractor/search?q=test_twitter_shadowban) | down |
2 | Twitter GraphQL API |  |  |
3 | Facebook user profile | [facebook_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_facebook_user_profile) | requests from GitHub Actions CI servers are blocked, requires facebookexternalhit UA; use url_mutations via CLI |
4 | Facebook group | [facebook_group](https://github.com/soxoj/socid-extractor/search?q=test_facebook_group) | broken |
5 | GitHub API | [github_api](https://github.com/soxoj/socid-extractor/search?q=test_github_api) | broken |
6 | GitHub Social Accounts API |  |  |
7 | Gitlab API |  |  |
8 | Patreon | [patreon](https://github.com/soxoj/socid-extractor/search?q=test_patreon) | broken |
9 | Flickr | [flickr](https://github.com/soxoj/socid-extractor/search?q=test_flickr) | failed from github CI infra IPs |
10 | Virgool |  |  |
11 | Yandex Disk file | [yandex_disk](https://github.com/soxoj/socid-extractor/search?q=test_yandex_disk) | broken |
12 | Yandex Disk photoalbum |  |  |
13 | Yandex Music AJAX request | [yandex_music_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_music_user_profile) | captcha |
14 | Yandex Q (Znatoki) user profile |  |  |
15 | Yandex Market user profile |  |  |
16 | Yandex Music API |  |  |
17 | Yandex Realty offer |  |  |
18 | Yandex Collections |  |  |
19 | Yandex Collections API | [yandex_collections_api](https://github.com/soxoj/socid-extractor/search?q=test_yandex_collections_api) | service no longer public |
20 | Yandex Reviews user profile | [yandex_reviews](https://github.com/soxoj/socid-extractor/search?q=test_yandex_reviews) | anti-bot / captcha / rate limiting from the site |
21 | Yandex Zen user profile | [yandex_zen_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_zen_user_profile) | failed from github CI infra IPs |
22 | Yandex messenger search API |  |  |
23 | Yandex messenger profile API |  |  |
24 | Yandex Bugbounty user profile |  |  |
25 | Yandex O | [yandex_o_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_o_user_profile) | down. service no longer exists |
26 | VK user profile foaf page | [vk_foaf](https://github.com/soxoj/socid-extractor/search?q=test_vk_foaf), [vk_user_profile_no_username](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_no_username) | VK foaf.php returns empty body for unauthenticated clients (2026), VK web is SPA; static fetch has no embed with ownerId (2026) |
27 | VK user profile | [vk_blocked_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_vk_blocked_user_profile), [vk_closed_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_vk_closed_user_profile), [vk_user_profile_full](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_full), [vk_user_profile_no_username](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_no_username) | broken, VK web is SPA; static fetch has no embed with ownerId (2026), VK web is SPA; static fetch has no embed with ownerId (2026), VK web is SPA; static fetch has no embed with ownerId (2026) |
28 | VK closed user profile |  |  |
29 | VK blocked user profile |  |  |
30 | Gravatar | [gravatar](https://github.com/soxoj/socid-extractor/search?q=test_gravatar) | broken |
31 | Instagram | [instagram](https://github.com/soxoj/socid-extractor/search?q=test_instagram) | requests from GitHub Actions CI servers are blocked, broken. needs deeper rework |
32 | Instagram API | [instagram_api](https://github.com/soxoj/socid-extractor/search?q=test_instagram_api) | requests from GitHub Actions CI servers are blocked |
33 | Instagram page JSON | [instagram](https://github.com/soxoj/socid-extractor/search?q=test_instagram) | requests from GitHub Actions CI servers are blocked, broken. needs deeper rework |
34 | Spotify API |  |  |
35 | EyeEm | [eyeem](https://github.com/soxoj/socid-extractor/search?q=test_eyeem) | EyeEm returns 403 for automated clients (2026) |
36 | Medium RSS |  |  |
37 | Medium | [medium](https://github.com/soxoj/socid-extractor/search?q=test_medium) |  |
38 | Odnoklassniki | [odnoklassniki](https://github.com/soxoj/socid-extractor/search?q=test_odnoklassniki) |  |
39 | Habrahabr HTML (old) |  |  |
40 | Habrahabr JSON | [habr](https://github.com/soxoj/socid-extractor/search?q=test_habr), [habr_no_image](https://github.com/soxoj/socid-extractor/search?q=test_habr_no_image) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
41 | My Mail.ru |  |  |
42 | Behance | [behance](https://github.com/soxoj/socid-extractor/search?q=test_behance) | broken |
43 | Blogger | [blogger](https://github.com/soxoj/socid-extractor/search?q=test_blogger) | Failed in GitHub CI |
44 | D3.ru | [d3](https://github.com/soxoj/socid-extractor/search?q=test_d3) | requests from GitHub Actions CI servers are blocked |
45 | Gitlab |  |  |
46 | 500px userByUsername API |  |  |
47 | 500px GraphQL API | [500px](https://github.com/soxoj/socid-extractor/search?q=test_500px) | non-actual, 500px requires POST requests for now |
48 | Google Document API | [google_documents](https://github.com/soxoj/socid-extractor/search?q=test_google_documents) |  |
49 | Google Document |  |  |
50 | Google Maps contributions |  |  |
51 | YouTube ytInitialData |  |  |
52 | Youtube Channel |  |  |
53 | Bitbucket | [bitbucket](https://github.com/soxoj/socid-extractor/search?q=test_bitbucket) | Bitbucket UI/embed changed; test user URL 404 (2026) |
54 | Pinterest API | [pinterest_api](https://github.com/soxoj/socid-extractor/search?q=test_pinterest_api) | broken |
55 | Pinterest profile/board page | [pinterest_account](https://github.com/soxoj/socid-extractor/search?q=test_pinterest_account) |  |
56 | Reddit | [reddit](https://github.com/soxoj/socid-extractor/search?q=test_reddit) | broken |
57 | Steam | [steam](https://github.com/soxoj/socid-extractor/search?q=test_steam) | cloudflare |
58 | Steam Addiction |  |  |
59 | Stack Exchange API | [stack_exchange_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_stack_exchange_api_e2e) | anti-bot / captcha / rate limiting from the site |
60 | Stack Overflow & similar |  |  |
61 | SoundCloud | [soundcloud](https://github.com/soxoj/socid-extractor/search?q=test_soundcloud) | SoundCloud returns 403 / empty embed for automated clients (2026) |
62 | TikTok | [tiktok](https://github.com/soxoj/socid-extractor/search?q=test_tiktok), [tiktok_hydration_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tiktok_hydration_e2e) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
63 | TikTok (legacy SIGI_STATE) | [tiktok_hydration_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tiktok_hydration_e2e) | requests from GitHub Actions CI servers are blocked |
64 | Picsart API | [picsart_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_picsart_api_e2e) | requests from GitHub Actions CI servers are blocked |
65 | VC.ru |  |  |
66 | LiveJournal | [livejournal](https://github.com/soxoj/socid-extractor/search?q=test_livejournal) | requests from GitHub Actions CI servers are blocked |
67 | MySpace | [myspace](https://github.com/soxoj/socid-extractor/search?q=test_myspace) | doesnt work without proxy, 503 error |
68 | Keybase API |  |  |
69 | Wikimapia |  |  |
70 | Vimeo HTML | [vimeo_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_vimeo_html_e2e) |  |
71 | Vimeo GraphQL API |  |  |
72 | DeviantArt | [deviantart](https://github.com/soxoj/socid-extractor/search?q=test_deviantart) | it works but is skipped for the sake of successful tests |
73 | mssg.me | [mssg_me](https://github.com/soxoj/socid-extractor/search?q=test_mssg_me) | broken |
74 | Telegram | [telegram](https://github.com/soxoj/socid-extractor/search?q=test_telegram) |  |
75 | BuzzFeed | [buzzfeed](https://github.com/soxoj/socid-extractor/search?q=test_buzzfeed) | requests from GitHub Actions CI servers are blocked |
76 | Linktree | [linktree](https://github.com/soxoj/socid-extractor/search?q=test_linktree) | broken |
77 | Twitch | [twitch](https://github.com/soxoj/socid-extractor/search?q=test_twitch) | broken |
78 | vBulletinEngine |  |  |
79 | Tumblr (default theme) |  |  |
80 | 1x.com |  |  |
81 | Last.fm | [last_fm](https://github.com/soxoj/socid-extractor/search?q=test_last_fm) |  |
82 | Ask.fm | [ask_fm](https://github.com/soxoj/socid-extractor/search?q=test_ask_fm) | broken |
83 | Launchpad | [launchpad](https://github.com/soxoj/socid-extractor/search?q=test_launchpad) | requests from GitHub Actions CI servers are blocked |
84 | Xakep.ru |  |  |
85 | Tproger.ru | [tproger_ru](https://github.com/soxoj/socid-extractor/search?q=test_tproger_ru) | no more author pages for now |
86 | Jsfiddle.net |  |  |
87 | Disqus API | [disqus_api](https://github.com/soxoj/socid-extractor/search?q=test_disqus_api) |  |
88 | uCoz-like profile page |  |  |
89 | uID.me |  |  |
90 | tapd | [tapd](https://github.com/soxoj/socid-extractor/search?q=test_tapd) | down |
91 | freelancer.com |  |  |
92 | Yelp | [yelp_userid](https://github.com/soxoj/socid-extractor/search?q=test_yelp_userid), [yelp_username](https://github.com/soxoj/socid-extractor/search?q=test_yelp_username) | broken, broken |
93 | Trello API | [trello](https://github.com/soxoj/socid-extractor/search?q=test_trello) |  |
94 | Weibo API | [weibo_api](https://github.com/soxoj/socid-extractor/search?q=test_weibo_api), [weibo_api_by_id](https://github.com/soxoj/socid-extractor/search?q=test_weibo_api_by_id) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
95 | Weibo | [weibo](https://github.com/soxoj/socid-extractor/search?q=test_weibo) | needs rework, cookies are required to get content, requests from GitHub Actions CI servers are blocked |
96 | ICQ | [icq](https://github.com/soxoj/socid-extractor/search?q=test_icq) | broken forever |
97 | Pastebin | [pastebin](https://github.com/soxoj/socid-extractor/search?q=test_pastebin) |  |
98 | Periscope |  |  |
99 | Imgur API | [imgur_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_imgur_api_e2e) |  |
100 | PayPal |  |  |
101 | Tinder | [tinder](https://github.com/soxoj/socid-extractor/search?q=test_tinder) | broken |
102 | ifunny.co | [ifunny_co](https://github.com/soxoj/socid-extractor/search?q=test_ifunny_co) |  |
103 | Wattpad API | [wattpad_api](https://github.com/soxoj/socid-extractor/search?q=test_wattpad_api) |  |
104 | Kik | [kik](https://github.com/soxoj/socid-extractor/search?q=test_kik) | broken |
105 | Docker Hub API | [docker_hub_api](https://github.com/soxoj/socid-extractor/search?q=test_docker_hub_api) |  |
106 | Mixcloud API | [mixcloud_api](https://github.com/soxoj/socid-extractor/search?q=test_mixcloud_api) |  |
107 | binarysearch API | [binarysearch_api](https://github.com/soxoj/socid-extractor/search?q=test_binarysearch_api) | down |
108 | pr0gramm API | [pr0gramm_api](https://github.com/soxoj/socid-extractor/search?q=test_pr0gramm_api) |  |
109 | Aparat API | [aparat_api](https://github.com/soxoj/socid-extractor/search?q=test_aparat_api) | broken |
110 | UnstoppableDomains |  |  |
111 | memory.lol | [memory_lol](https://github.com/soxoj/socid-extractor/search?q=test_memory_lol) |  |
112 | Duolingo API | [duolingo_api](https://github.com/soxoj/socid-extractor/search?q=test_duolingo_api) |  |
113 | TwitchTracker |  |  |
114 | Chess.com API | [chess_com_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_chess_com_api_e2e) |  |
115 | Roblox user API | [roblox_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_roblox_api_e2e) |  |
116 | Roblox username lookup API |  |  |
117 | MyAnimeList profile |  |  |
118 | XVideos profile |  |  |
119 | lnk.bio |  |  |
120 | Wikipedia user API |  |  |
121 | Fandom MediaWiki API |  |  |
122 | Substack public profile API |  |  |
123 | Lesswrong GraphQL API |  |  |
124 | hashnode GraphQL API |  |  |
125 | Rarible API |  |  |
126 | CSSBattle |  |  |
127 | Max (max.ru) profile |  |  |
128 | Bluesky API |  |  |
129 | Scratch API |  |  |
130 | DailyMotion API |  |  |
131 | SlideShare |  |  |
132 | WordPress.org Profile |  |  |
133 | Weebly |  |  |
134 | Calendly |  |  |
135 | Google Play Developer |  |  |
136 | Amazon Author |  |  |
137 | Habr |  |  |
138 | Taplink |  |  |
139 | Product Hunt |  |  |
140 | Chess.com HTML | [chess_com_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_chess_com_html_e2e) |  |
141 | Roblox HTML | [roblox_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_roblox_html_e2e) |  |
142 | LeetCode GraphQL | [leetcode_graphql_e2e](https://github.com/soxoj/socid-extractor/search?q=test_leetcode_graphql_e2e) | LeetCode GraphQL requires POST request |
143 | Boosty API | [boosty_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_boosty_api_e2e) |  |
144 | Threads |  |  |
145 | Smule |  |  |
146 | Warpcast API | [warpcast_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_warpcast_api_e2e) |  |
147 | Paragraph API | [paragraph_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_paragraph_api_e2e) |  |
148 | Fragment | [fragment_e2e](https://github.com/soxoj/socid-extractor/search?q=test_fragment_e2e) |  |
149 | Tonometerbot | [tonometerbot_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tonometerbot_e2e) | anti-bot / captcha / rate limiting from the site |
150 | Spatial | [spatial_e2e](https://github.com/soxoj/socid-extractor/search?q=test_spatial_e2e) | requests from GitHub Actions CI servers are blocked |
151 | OpenSea |  |  |
152 | Hive Blog |  |  |
153 | BuyMeACoffee | [buymeacoffee](https://github.com/soxoj/socid-extractor/search?q=test_buymeacoffee) |  |
154 | Discourse API |  |  |

The table has been updated at 2026-06-01 07:47:37.379241 UTC
