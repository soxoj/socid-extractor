# Supported sites and methods

| № | Method | Test data | Notes |
| --- | --- | --- | --- |
0 | Twitter HTML |  |  |
1 | QQ Qzone portrait |  |  |
2 | Bilibili card |  |  |
3 | Twitter Shadowban | [twitter_shadowban](https://github.com/soxoj/socid-extractor/search?q=test_twitter_shadowban) | down |
4 | Twitter GraphQL API |  |  |
5 | Facebook user profile | [facebook_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_facebook_user_profile) | requests from GitHub Actions CI servers are blocked, requires facebookexternalhit UA; use url_mutations via CLI |
6 | Facebook group | [facebook_group](https://github.com/soxoj/socid-extractor/search?q=test_facebook_group) | broken |
7 | GitHub API | [github_api](https://github.com/soxoj/socid-extractor/search?q=test_github_api) | broken |
8 | GitHub Social Accounts API |  |  |
9 | Gitlab API |  |  |
10 | Patreon | [patreon](https://github.com/soxoj/socid-extractor/search?q=test_patreon) | broken |
11 | Flickr | [flickr](https://github.com/soxoj/socid-extractor/search?q=test_flickr) | failed from github CI infra IPs |
12 | Virgool |  |  |
13 | Yandex Disk file | [yandex_disk](https://github.com/soxoj/socid-extractor/search?q=test_yandex_disk) | broken |
14 | Yandex Disk photoalbum |  |  |
15 | Yandex Music AJAX request | [yandex_music_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_music_user_profile) | captcha |
16 | Yandex Q (Znatoki) user profile |  |  |
17 | Yandex Market user profile |  |  |
18 | Yandex Music API |  |  |
19 | Yandex Realty offer |  |  |
20 | Yandex Collections |  |  |
21 | Yandex Collections API | [yandex_collections_api](https://github.com/soxoj/socid-extractor/search?q=test_yandex_collections_api) | service no longer public |
22 | Yandex Reviews user profile | [yandex_reviews](https://github.com/soxoj/socid-extractor/search?q=test_yandex_reviews) | anti-bot / captcha / rate limiting from the site |
23 | Yandex Zen user profile | [yandex_zen_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_zen_user_profile) | failed from github CI infra IPs |
24 | Yandex messenger search API |  |  |
25 | Yandex messenger profile API |  |  |
26 | Yandex Bugbounty user profile |  |  |
27 | Yandex O | [yandex_o_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_o_user_profile) | down. service no longer exists |
28 | VK user profile foaf page | [vk_foaf](https://github.com/soxoj/socid-extractor/search?q=test_vk_foaf), [vk_user_profile_no_username](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_no_username) | VK foaf.php returns empty body for unauthenticated clients (2026), VK web is SPA; static fetch has no embed with ownerId (2026) |
29 | VK user profile | [vk_blocked_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_vk_blocked_user_profile), [vk_closed_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_vk_closed_user_profile), [vk_user_profile_full](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_full), [vk_user_profile_no_username](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_no_username) | broken, VK web is SPA; static fetch has no embed with ownerId (2026), VK web is SPA; static fetch has no embed with ownerId (2026), VK web is SPA; static fetch has no embed with ownerId (2026) |
30 | VK closed user profile |  |  |
31 | VK blocked user profile |  |  |
32 | Gravatar | [gravatar](https://github.com/soxoj/socid-extractor/search?q=test_gravatar) | broken |
33 | Instagram | [instagram](https://github.com/soxoj/socid-extractor/search?q=test_instagram) | requests from GitHub Actions CI servers are blocked, broken. needs deeper rework |
34 | Instagram API | [instagram_api](https://github.com/soxoj/socid-extractor/search?q=test_instagram_api) | requests from GitHub Actions CI servers are blocked |
35 | Instagram page JSON | [instagram](https://github.com/soxoj/socid-extractor/search?q=test_instagram) | requests from GitHub Actions CI servers are blocked, broken. needs deeper rework |
36 | Instagram GraphQL | [instagram_graphql_bio_links_and_tagged_usernames](https://github.com/soxoj/socid-extractor/search?q=test_instagram_graphql_bio_links_and_tagged_usernames), [instagram_graphql_e2e](https://github.com/soxoj/socid-extractor/search?q=test_instagram_graphql_e2e) | anti-bot / captcha / rate limiting from the site, requests from GitHub Actions CI servers are blocked |
37 | Spotify API |  |  |
38 | EyeEm | [eyeem](https://github.com/soxoj/socid-extractor/search?q=test_eyeem) | EyeEm returns 403 for automated clients (2026) |
39 | Medium RSS |  |  |
40 | Medium | [medium](https://github.com/soxoj/socid-extractor/search?q=test_medium) |  |
41 | Odnoklassniki | [odnoklassniki](https://github.com/soxoj/socid-extractor/search?q=test_odnoklassniki) |  |
42 | Habrahabr HTML (old) |  |  |
43 | Habrahabr JSON | [habr](https://github.com/soxoj/socid-extractor/search?q=test_habr), [habr_no_image](https://github.com/soxoj/socid-extractor/search?q=test_habr_no_image) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
44 | My Mail.ru |  |  |
45 | Behance | [behance](https://github.com/soxoj/socid-extractor/search?q=test_behance) | broken |
46 | Blogger | [blogger](https://github.com/soxoj/socid-extractor/search?q=test_blogger) | Failed in GitHub CI |
47 | D3.ru | [d3](https://github.com/soxoj/socid-extractor/search?q=test_d3) | requests from GitHub Actions CI servers are blocked |
48 | Gitlab |  |  |
49 | 500px userByUsername API |  |  |
50 | 500px GraphQL API | [500px](https://github.com/soxoj/socid-extractor/search?q=test_500px) |  |
51 | Google Document API | [google_documents](https://github.com/soxoj/socid-extractor/search?q=test_google_documents) |  |
52 | Google Document |  |  |
53 | Google Maps contributions |  |  |
54 | YouTube ytInitialData |  |  |
55 | Youtube Channel |  |  |
56 | Bitbucket | [bitbucket](https://github.com/soxoj/socid-extractor/search?q=test_bitbucket) | Bitbucket UI/embed changed; test user URL 404 (2026) |
57 | Pinterest profile/board page | [pinterest_account](https://github.com/soxoj/socid-extractor/search?q=test_pinterest_account) |  |
58 | Reddit | [reddit](https://github.com/soxoj/socid-extractor/search?q=test_reddit) | broken |
59 | Steam | [steam](https://github.com/soxoj/socid-extractor/search?q=test_steam) | cloudflare |
60 | Steam Community Group |  |  |
61 | Steam Addiction |  |  |
62 | Stack Exchange API | [stack_exchange_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_stack_exchange_api_e2e) | anti-bot / captcha / rate limiting from the site |
63 | Stack Overflow & similar |  |  |
64 | SoundCloud | [soundcloud](https://github.com/soxoj/socid-extractor/search?q=test_soundcloud) | SoundCloud returns 403 / empty embed for automated clients (2026) |
65 | TikTok | [tiktok](https://github.com/soxoj/socid-extractor/search?q=test_tiktok), [tiktok_hydration_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tiktok_hydration_e2e) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
66 | TikTok (legacy SIGI_STATE) | [tiktok_hydration_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tiktok_hydration_e2e) | requests from GitHub Actions CI servers are blocked |
67 | Picsart API | [picsart_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_picsart_api_e2e) | requests from GitHub Actions CI servers are blocked |
68 | VC.ru |  |  |
69 | LiveJournal | [livejournal](https://github.com/soxoj/socid-extractor/search?q=test_livejournal) | requests from GitHub Actions CI servers are blocked |
70 | MySpace | [myspace](https://github.com/soxoj/socid-extractor/search?q=test_myspace) | doesnt work without proxy, 503 error |
71 | Keybase API |  |  |
72 | Wikimapia |  |  |
73 | Vimeo HTML | [vimeo_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_vimeo_html_e2e) | requests from GitHub Actions CI servers are blocked |
74 | Vimeo GraphQL API |  |  |
75 | DeviantArt | [deviantart](https://github.com/soxoj/socid-extractor/search?q=test_deviantart) | it works but is skipped for the sake of successful tests |
76 | mssg.me | [mssg_me](https://github.com/soxoj/socid-extractor/search?q=test_mssg_me) | broken |
77 | Telegram | [telegram](https://github.com/soxoj/socid-extractor/search?q=test_telegram) |  |
78 | BuzzFeed | [buzzfeed](https://github.com/soxoj/socid-extractor/search?q=test_buzzfeed) | requests from GitHub Actions CI servers are blocked |
79 | Linktree | [linktree](https://github.com/soxoj/socid-extractor/search?q=test_linktree) | broken |
80 | Twitch | [twitch](https://github.com/soxoj/socid-extractor/search?q=test_twitch) | broken |
81 | vBulletinEngine |  |  |
82 | Tumblr (default theme) |  |  |
83 | 1x.com |  |  |
84 | Last.fm | [last_fm](https://github.com/soxoj/socid-extractor/search?q=test_last_fm) | requests from GitHub Actions CI servers are blocked |
85 | Ask.fm | [ask_fm](https://github.com/soxoj/socid-extractor/search?q=test_ask_fm) | broken |
86 | Launchpad | [launchpad](https://github.com/soxoj/socid-extractor/search?q=test_launchpad) | requests from GitHub Actions CI servers are blocked |
87 | Xakep.ru |  |  |
88 | Tproger.ru | [tproger_ru](https://github.com/soxoj/socid-extractor/search?q=test_tproger_ru) | no more author pages for now |
89 | Jsfiddle.net |  |  |
90 | Disqus API | [disqus_api](https://github.com/soxoj/socid-extractor/search?q=test_disqus_api) |  |
91 | uCoz-like profile page |  |  |
92 | uID.me |  |  |
93 | tapd | [tapd](https://github.com/soxoj/socid-extractor/search?q=test_tapd) | down |
94 | freelancer.com |  |  |
95 | Yelp | [yelp_userid](https://github.com/soxoj/socid-extractor/search?q=test_yelp_userid), [yelp_username](https://github.com/soxoj/socid-extractor/search?q=test_yelp_username) | broken, broken |
96 | Trello API | [trello](https://github.com/soxoj/socid-extractor/search?q=test_trello) |  |
97 | Weibo API | [weibo_api](https://github.com/soxoj/socid-extractor/search?q=test_weibo_api), [weibo_api_by_id](https://github.com/soxoj/socid-extractor/search?q=test_weibo_api_by_id) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
98 | Weibo | [weibo](https://github.com/soxoj/socid-extractor/search?q=test_weibo) | needs rework, cookies are required to get content, requests from GitHub Actions CI servers are blocked |
99 | ICQ | [icq](https://github.com/soxoj/socid-extractor/search?q=test_icq) | broken forever |
100 | Pastebin | [pastebin](https://github.com/soxoj/socid-extractor/search?q=test_pastebin) |  |
101 | Periscope |  |  |
102 | Imgur API | [imgur_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_imgur_api_e2e) |  |
103 | PayPal |  |  |
104 | Tinder | [tinder](https://github.com/soxoj/socid-extractor/search?q=test_tinder) | broken |
105 | ifunny.co | [ifunny_co](https://github.com/soxoj/socid-extractor/search?q=test_ifunny_co) |  |
106 | Wattpad API | [wattpad_api](https://github.com/soxoj/socid-extractor/search?q=test_wattpad_api) | Wattpad API endpoint is unavailable / unstable from CI (2026) |
107 | Kik | [kik](https://github.com/soxoj/socid-extractor/search?q=test_kik) | broken |
108 | Docker Hub API | [docker_hub_api](https://github.com/soxoj/socid-extractor/search?q=test_docker_hub_api) |  |
109 | Mixcloud API | [mixcloud_api](https://github.com/soxoj/socid-extractor/search?q=test_mixcloud_api) |  |
110 | binarysearch API | [binarysearch_api](https://github.com/soxoj/socid-extractor/search?q=test_binarysearch_api) | down |
111 | pr0gramm API | [pr0gramm_api](https://github.com/soxoj/socid-extractor/search?q=test_pr0gramm_api) |  |
112 | Aparat API | [aparat_api](https://github.com/soxoj/socid-extractor/search?q=test_aparat_api) | broken |
113 | UnstoppableDomains |  |  |
114 | memory.lol | [memory_lol](https://github.com/soxoj/socid-extractor/search?q=test_memory_lol) |  |
115 | Duolingo API | [duolingo_api](https://github.com/soxoj/socid-extractor/search?q=test_duolingo_api) |  |
116 | TwitchTracker |  |  |
117 | Chess.com API | [chess_com_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_chess_com_api_e2e) |  |
118 | Roblox user API | [roblox_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_roblox_api_e2e) |  |
119 | Roblox username lookup API |  |  |
120 | MyAnimeList profile |  |  |
121 | XVideos profile |  |  |
122 | lnk.bio |  |  |
123 | Wikipedia user API |  |  |
124 | Fandom MediaWiki API |  |  |
125 | Substack public profile API |  |  |
126 | Lesswrong GraphQL API |  |  |
127 | hashnode GraphQL API |  |  |
128 | Rarible API |  |  |
129 | CSSBattle |  |  |
130 | Max (max.ru) profile |  |  |
131 | Bluesky API |  |  |
132 | Scratch API |  |  |
133 | DailyMotion API |  |  |
134 | SlideShare |  |  |
135 | WordPress.org Profile |  |  |
136 | Weebly |  |  |
137 | Calendly |  |  |
138 | Google Play Developer |  |  |
139 | Amazon Author |  |  |
140 | Habr |  |  |
141 | Taplink |  |  |
142 | Product Hunt |  |  |
143 | Chess.com HTML | [chess_com_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_chess_com_html_e2e) | chess.com HTML endpoint times out from CI (2026) |
144 | Roblox HTML | [roblox_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_roblox_html_e2e) |  |
145 | LeetCode GraphQL | [leetcode_graphql_e2e](https://github.com/soxoj/socid-extractor/search?q=test_leetcode_graphql_e2e) |  |
146 | Boosty API | [boosty_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_boosty_api_e2e) |  |
147 | Threads |  |  |
148 | Smule |  |  |
149 | Warpcast API | [warpcast_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_warpcast_api_e2e) |  |
150 | Paragraph API | [paragraph_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_paragraph_api_e2e) |  |
151 | Fragment | [fragment_e2e](https://github.com/soxoj/socid-extractor/search?q=test_fragment_e2e) |  |
152 | Tonometerbot | [tonometerbot_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tonometerbot_e2e) | anti-bot / captcha / rate limiting from the site |
153 | Spatial | [spatial_e2e](https://github.com/soxoj/socid-extractor/search?q=test_spatial_e2e) | requests from GitHub Actions CI servers are blocked |
154 | OpenSea |  |  |
155 | Hive Blog |  |  |
156 | ORCID API |  |  |
157 | OpenAlex Authors API |  |  |
158 | arXiv author page |  |  |
159 | DBLP person record |  |  |
160 | Scholia author profile |  |  |
161 | BuyMeACoffee | [buymeacoffee](https://github.com/soxoj/socid-extractor/search?q=test_buymeacoffee) |  |
162 | Discourse API |  |  |
163 | Snapchat | [snapchat](https://github.com/soxoj/socid-extractor/search?q=test_snapchat) |  |
164 | Bio Site | [bio_site](https://github.com/soxoj/socid-extractor/search?q=test_bio_site) |  |
165 | Faceit API | [faceit_api](https://github.com/soxoj/socid-extractor/search?q=test_faceit_api) |  |
166 | Fansly API | [fansly_api](https://github.com/soxoj/socid-extractor/search?q=test_fansly_api) |  |
167 | Codewars API |  |  |
168 | Minds API |  |  |
169 | HackerNoon API |  |  |
170 | Polar API |  |  |
171 | thanks.dev API |  |  |
172 | Matrix profile API |  |  |
173 | osu! | [osu](https://github.com/soxoj/socid-extractor/search?q=test_osu) |  |
174 | Lens (Hey/Orb/Buttrfly) account | [lens_account](https://github.com/soxoj/socid-extractor/search?q=test_lens_account), [lens_account_absent](https://github.com/soxoj/socid-extractor/search?q=test_lens_account_absent) |  |
175 | HuggingFace API | [huggingface_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_huggingface_api_e2e) |  |
176 | HackerNews | [hackernews](https://github.com/soxoj/socid-extractor/search?q=test_hackernews) |  |
177 | GDBrowser API | [gdbrowser_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_gdbrowser_api_e2e) |  |
178 | StreamElements API | [streamelements_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_streamelements_api_e2e) |  |
179 | Streamlabs API | [streamlabs_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_streamlabs_api_e2e) |  |
180 | Donatty API | [donatty_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_donatty_api_e2e) |  |
181 | VisnessCard API | [visnesscard_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_visnesscard_api_e2e) | requests from GitHub Actions CI servers are blocked |
182 | Codeforces API |  |  |
183 | Discogs API |  |  |
184 | iNaturalist API |  |  |
185 | Pronouny API |  |  |
186 | Zepeto API |  |  |
187 | OnlyFans API |  |  |
188 | eToro API |  |  |
189 | Gettr API |  |  |
190 | Habbo API |  |  |
191 | Hackadvisor API |  |  |
192 | Pillowfort JSON API |  |  |
193 | Scored API |  |  |
194 | YesWeHack API |  |  |
195 | Destream API |  |  |
196 | Tipeeestream API |  |  |
197 | Komi API |  |  |
198 | Cropty API |  |  |
199 | Redgifs API |  |  |
200 | Tappy API |  |  |
201 | Komoot API |  |  |
202 | Tapitag API |  |  |
203 | Vivino API |  |  |
204 | Google Scholar |  |  |
205 | Snapchat profile |  |  |
206 | Flipboard profile |  |  |
207 | Clubhouse profile |  |  |
208 | Coda.io profile |  |  |
209 | Poe.com profile |  |  |
210 | Gumroad profile |  |  |
211 | Mastodon HTML profile |  |  |
212 | Discourse HTML profile |  |  |
213 | Mastodon API |  |  |
214 | Discourse Forums |  |  |
215 | FL.ru |  |  |
216 | Manifold Markets |  |  |
217 | VSCO |  |  |
218 | Mojang API |  |  |
219 | OP.GG |  |  |
220 | coder.social |  |  |
221 | GOG |  |  |
222 | Kick API |  |  |
223 | Academia.edu |  |  |
224 | TradingView |  |  |
225 | Geocaching |  |  |
226 | Rutracker |  |  |
227 | Weburg |  |  |
228 | Pokemon Showdown |  |  |
229 | ImageShack |  |  |
230 | Replit |  |  |
231 | Itch.io |  |  |
232 | Giphy |  |  |
233 | Wattpad HTML profile |  |  |
234 | Venmo |  |  |
235 | Tumblr blog |  |  |
236 | Drive2.ru |  |  |
237 | Lichess API |  |  |
238 | Hackerrank API |  |  |
239 | Kongregate API |  |  |
240 | WordPress.com site API |  |  |
241 | Codecademy profile |  |  |
242 | About.me profile |  |  |
243 | Fur Affinity profile |  |  |
244 | Pikabu profile |  |  |
245 | Codepen profile |  |  |
246 | Letterboxd profile |  |  |
247 | Gitee profile |  |  |
248 | Slack workspace |  |  |
249 | Instructables member |  |  |
250 | Envato Author profile |  |  |
251 | Kwork freelancer |  |  |
252 | Freesound user |  |  |
253 | Star Citizen citizen |  |  |
254 | Dribbble profile |  |  |
255 | Depop shop |  |  |
256 | ModDB member |  |  |
257 | Xbox Gamertag |  |  |
258 | DonationAlerts streamer |  |  |
259 | CCM profile |  |  |
260 | Wikidot user |  |  |
261 | Couchsurfing person |  |  |
262 | ReverbNation artist |  |  |

The table has been updated at 2026-08-27 12:17:04.307899 UTC
