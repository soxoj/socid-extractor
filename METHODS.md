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
10 | Patreon | [patreon](https://github.com/soxoj/socid-extractor/search?q=test_patreon) | anti-bot / captcha / rate limiting from the site |
11 | Patreon RSC | [patreon_rsc](https://github.com/soxoj/socid-extractor/search?q=test_patreon_rsc) | anti-bot / captcha / rate limiting from the site |
12 | Flickr | [flickr](https://github.com/soxoj/socid-extractor/search?q=test_flickr) | failed from github CI infra IPs |
13 | Virgool |  |  |
14 | Yandex Disk file | [yandex_disk](https://github.com/soxoj/socid-extractor/search?q=test_yandex_disk) | broken |
15 | Yandex Disk photoalbum |  |  |
16 | Yandex Music AJAX request | [yandex_music_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_music_user_profile) | captcha |
17 | Yandex Q (Znatoki) user profile |  |  |
18 | Yandex Market user profile |  |  |
19 | Yandex Music API |  |  |
20 | Yandex Realty offer |  |  |
21 | Yandex Collections |  |  |
22 | Yandex Collections API | [yandex_collections_api](https://github.com/soxoj/socid-extractor/search?q=test_yandex_collections_api) | service no longer public |
23 | Yandex Reviews user profile | [yandex_reviews](https://github.com/soxoj/socid-extractor/search?q=test_yandex_reviews) | anti-bot / captcha / rate limiting from the site |
24 | Yandex Zen user profile | [yandex_zen_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_zen_user_profile) | failed from github CI infra IPs |
25 | Yandex messenger search API |  |  |
26 | Yandex messenger profile API |  |  |
27 | Yandex Bugbounty user profile |  |  |
28 | Yandex O | [yandex_o_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_yandex_o_user_profile) | down. service no longer exists |
29 | VK user profile foaf page | [vk_foaf](https://github.com/soxoj/socid-extractor/search?q=test_vk_foaf), [vk_user_profile_no_username](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_no_username) | VK foaf.php returns empty body for unauthenticated clients (2026), VK web is SPA; static fetch has no embed with ownerId (2026) |
30 | VK user profile | [vk_blocked_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_vk_blocked_user_profile), [vk_closed_user_profile](https://github.com/soxoj/socid-extractor/search?q=test_vk_closed_user_profile), [vk_user_profile_full](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_full), [vk_user_profile_no_username](https://github.com/soxoj/socid-extractor/search?q=test_vk_user_profile_no_username) | broken, VK web is SPA; static fetch has no embed with ownerId (2026), VK web is SPA; static fetch has no embed with ownerId (2026), VK web is SPA; static fetch has no embed with ownerId (2026) |
31 | VK closed user profile |  |  |
32 | VK blocked user profile |  |  |
33 | Gravatar | [gravatar](https://github.com/soxoj/socid-extractor/search?q=test_gravatar) | broken |
34 | Instagram | [instagram](https://github.com/soxoj/socid-extractor/search?q=test_instagram) | requests from GitHub Actions CI servers are blocked, broken. needs deeper rework |
35 | Instagram API | [instagram_api](https://github.com/soxoj/socid-extractor/search?q=test_instagram_api) | requests from GitHub Actions CI servers are blocked |
36 | Instagram page JSON | [instagram](https://github.com/soxoj/socid-extractor/search?q=test_instagram) | requests from GitHub Actions CI servers are blocked, broken. needs deeper rework |
37 | Instagram GraphQL | [instagram_graphql_bio_links_and_tagged_usernames](https://github.com/soxoj/socid-extractor/search?q=test_instagram_graphql_bio_links_and_tagged_usernames), [instagram_graphql_e2e](https://github.com/soxoj/socid-extractor/search?q=test_instagram_graphql_e2e) | anti-bot / captcha / rate limiting from the site, requests from GitHub Actions CI servers are blocked |
38 | Spotify API |  |  |
39 | EyeEm | [eyeem](https://github.com/soxoj/socid-extractor/search?q=test_eyeem) | EyeEm returns 403 for automated clients (2026) |
40 | Medium RSS |  |  |
41 | Medium | [medium](https://github.com/soxoj/socid-extractor/search?q=test_medium) |  |
42 | Odnoklassniki | [odnoklassniki](https://github.com/soxoj/socid-extractor/search?q=test_odnoklassniki) |  |
43 | Habrahabr HTML (old) |  |  |
44 | Habrahabr JSON | [habr](https://github.com/soxoj/socid-extractor/search?q=test_habr), [habr_no_image](https://github.com/soxoj/socid-extractor/search?q=test_habr_no_image) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
45 | My Mail.ru |  |  |
46 | Behance | [behance](https://github.com/soxoj/socid-extractor/search?q=test_behance) | broken |
47 | Blogger | [blogger](https://github.com/soxoj/socid-extractor/search?q=test_blogger) | Failed in GitHub CI |
48 | D3.ru | [d3](https://github.com/soxoj/socid-extractor/search?q=test_d3) | requests from GitHub Actions CI servers are blocked |
49 | Gitlab |  |  |
50 | 500px userByUsername API |  |  |
51 | 500px GraphQL API | [500px](https://github.com/soxoj/socid-extractor/search?q=test_500px) |  |
52 | Google Document API | [google_documents](https://github.com/soxoj/socid-extractor/search?q=test_google_documents) |  |
53 | Google Document |  |  |
54 | Google Maps contributions |  |  |
55 | YouTube ytInitialData |  |  |
56 | Youtube Channel |  |  |
57 | Bitbucket | [bitbucket](https://github.com/soxoj/socid-extractor/search?q=test_bitbucket) | Bitbucket UI/embed changed; test user URL 404 (2026) |
58 | Pinterest profile/board page | [pinterest_account](https://github.com/soxoj/socid-extractor/search?q=test_pinterest_account) |  |
59 | Reddit | [reddit](https://github.com/soxoj/socid-extractor/search?q=test_reddit) | broken |
60 | Steam | [steam](https://github.com/soxoj/socid-extractor/search?q=test_steam) | cloudflare |
61 | Steam Community Group |  |  |
62 | Steam Addiction |  |  |
63 | Stack Exchange API | [stack_exchange_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_stack_exchange_api_e2e) | anti-bot / captcha / rate limiting from the site |
64 | Stack Overflow & similar |  |  |
65 | SoundCloud | [soundcloud](https://github.com/soxoj/socid-extractor/search?q=test_soundcloud) | SoundCloud returns 403 / empty embed for automated clients (2026) |
66 | TikTok | [tiktok](https://github.com/soxoj/socid-extractor/search?q=test_tiktok), [tiktok_hydration_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tiktok_hydration_e2e) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
67 | TikTok (legacy SIGI_STATE) | [tiktok_hydration_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tiktok_hydration_e2e) | requests from GitHub Actions CI servers are blocked |
68 | Picsart API | [picsart_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_picsart_api_e2e) | requests from GitHub Actions CI servers are blocked |
69 | VC.ru |  |  |
70 | LiveJournal | [livejournal](https://github.com/soxoj/socid-extractor/search?q=test_livejournal) | requests from GitHub Actions CI servers are blocked |
71 | MySpace | [myspace](https://github.com/soxoj/socid-extractor/search?q=test_myspace) | doesnt work without proxy, 503 error |
72 | Keybase API |  |  |
73 | Wikimapia |  |  |
74 | Vimeo HTML | [vimeo_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_vimeo_html_e2e) | requests from GitHub Actions CI servers are blocked |
75 | Vimeo GraphQL API |  |  |
76 | DeviantArt | [deviantart](https://github.com/soxoj/socid-extractor/search?q=test_deviantart) | it works but is skipped for the sake of successful tests |
77 | mssg.me | [mssg_me](https://github.com/soxoj/socid-extractor/search?q=test_mssg_me) | broken |
78 | Telegram | [telegram](https://github.com/soxoj/socid-extractor/search?q=test_telegram) |  |
79 | BuzzFeed | [buzzfeed](https://github.com/soxoj/socid-extractor/search?q=test_buzzfeed) | requests from GitHub Actions CI servers are blocked |
80 | Linktree | [linktree](https://github.com/soxoj/socid-extractor/search?q=test_linktree) | broken |
81 | Twitch | [twitch](https://github.com/soxoj/socid-extractor/search?q=test_twitch) | broken |
82 | vBulletinEngine |  |  |
83 | Tumblr (default theme) |  |  |
84 | 1x.com |  |  |
85 | Last.fm | [last_fm](https://github.com/soxoj/socid-extractor/search?q=test_last_fm) | requests from GitHub Actions CI servers are blocked |
86 | Ask.fm | [ask_fm](https://github.com/soxoj/socid-extractor/search?q=test_ask_fm) | broken |
87 | Launchpad | [launchpad](https://github.com/soxoj/socid-extractor/search?q=test_launchpad) | requests from GitHub Actions CI servers are blocked |
88 | Xakep.ru |  |  |
89 | Tproger.ru | [tproger_ru](https://github.com/soxoj/socid-extractor/search?q=test_tproger_ru) | no more author pages for now |
90 | Jsfiddle.net |  |  |
91 | Disqus API | [disqus_api](https://github.com/soxoj/socid-extractor/search?q=test_disqus_api) |  |
92 | uCoz-like profile page |  |  |
93 | uID.me |  |  |
94 | tapd | [tapd](https://github.com/soxoj/socid-extractor/search?q=test_tapd) | down |
95 | freelancer.com |  |  |
96 | Yelp | [yelp_userid](https://github.com/soxoj/socid-extractor/search?q=test_yelp_userid), [yelp_username](https://github.com/soxoj/socid-extractor/search?q=test_yelp_username) | broken, broken |
97 | Trello API | [trello](https://github.com/soxoj/socid-extractor/search?q=test_trello) |  |
98 | Weibo API | [weibo_api](https://github.com/soxoj/socid-extractor/search?q=test_weibo_api), [weibo_api_by_id](https://github.com/soxoj/socid-extractor/search?q=test_weibo_api_by_id) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
99 | Weibo | [weibo](https://github.com/soxoj/socid-extractor/search?q=test_weibo) | needs rework, cookies are required to get content, requests from GitHub Actions CI servers are blocked |
100 | ICQ | [icq](https://github.com/soxoj/socid-extractor/search?q=test_icq) | broken forever |
101 | Pastebin | [pastebin](https://github.com/soxoj/socid-extractor/search?q=test_pastebin) |  |
102 | Periscope |  |  |
103 | Imgur API | [imgur_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_imgur_api_e2e) |  |
104 | PayPal |  |  |
105 | Tinder | [tinder](https://github.com/soxoj/socid-extractor/search?q=test_tinder) | broken |
106 | ifunny.co | [ifunny_co](https://github.com/soxoj/socid-extractor/search?q=test_ifunny_co) |  |
107 | Wattpad API | [wattpad_api](https://github.com/soxoj/socid-extractor/search?q=test_wattpad_api) | Wattpad API endpoint is unavailable / unstable from CI (2026) |
108 | Kik | [kik](https://github.com/soxoj/socid-extractor/search?q=test_kik) | broken |
109 | Docker Hub API | [docker_hub_api](https://github.com/soxoj/socid-extractor/search?q=test_docker_hub_api) |  |
110 | Mixcloud API | [mixcloud_api](https://github.com/soxoj/socid-extractor/search?q=test_mixcloud_api) |  |
111 | binarysearch API | [binarysearch_api](https://github.com/soxoj/socid-extractor/search?q=test_binarysearch_api) | down |
112 | pr0gramm API | [pr0gramm_api](https://github.com/soxoj/socid-extractor/search?q=test_pr0gramm_api) |  |
113 | Aparat API | [aparat_api](https://github.com/soxoj/socid-extractor/search?q=test_aparat_api) | broken |
114 | UnstoppableDomains |  |  |
115 | memory.lol | [memory_lol](https://github.com/soxoj/socid-extractor/search?q=test_memory_lol) |  |
116 | Duolingo API | [duolingo_api](https://github.com/soxoj/socid-extractor/search?q=test_duolingo_api) |  |
117 | TwitchTracker |  |  |
118 | Chess.com API | [chess_com_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_chess_com_api_e2e) |  |
119 | Roblox user API | [roblox_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_roblox_api_e2e) |  |
120 | Roblox username lookup API |  |  |
121 | MyAnimeList profile |  |  |
122 | XVideos profile |  |  |
123 | lnk.bio |  |  |
124 | Wikipedia user API |  |  |
125 | Fandom MediaWiki API |  |  |
126 | Substack public profile API |  |  |
127 | Lesswrong GraphQL API |  |  |
128 | hashnode GraphQL API |  |  |
129 | Rarible API |  |  |
130 | CSSBattle |  |  |
131 | Max (max.ru) profile |  |  |
132 | Bluesky API |  |  |
133 | Scratch API |  |  |
134 | DailyMotion API |  |  |
135 | SlideShare |  |  |
136 | WordPress.org Profile |  |  |
137 | Weebly |  |  |
138 | Calendly |  |  |
139 | Google Play Developer |  |  |
140 | Amazon Author |  |  |
141 | Habr |  |  |
142 | Taplink |  |  |
143 | Product Hunt |  |  |
144 | Chess.com HTML | [chess_com_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_chess_com_html_e2e) | chess.com HTML endpoint times out from CI (2026) |
145 | Roblox HTML | [roblox_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_roblox_html_e2e) |  |
146 | LeetCode GraphQL | [leetcode_graphql_e2e](https://github.com/soxoj/socid-extractor/search?q=test_leetcode_graphql_e2e) |  |
147 | Boosty API | [boosty_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_boosty_api_e2e) |  |
148 | Threads |  |  |
149 | Smule |  |  |
150 | Warpcast API | [warpcast_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_warpcast_api_e2e) |  |
151 | Paragraph API | [paragraph_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_paragraph_api_e2e) |  |
152 | Fragment | [fragment_e2e](https://github.com/soxoj/socid-extractor/search?q=test_fragment_e2e) |  |
153 | Tonometerbot | [tonometerbot_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tonometerbot_e2e) | anti-bot / captcha / rate limiting from the site |
154 | Spatial | [spatial_e2e](https://github.com/soxoj/socid-extractor/search?q=test_spatial_e2e) | requests from GitHub Actions CI servers are blocked |
155 | OpenSea |  |  |
156 | Hive Blog |  |  |
157 | ORCID API |  |  |
158 | OpenAlex Authors API |  |  |
159 | arXiv author page |  |  |
160 | DBLP person record |  |  |
161 | Scholia author profile |  |  |
162 | BuyMeACoffee | [buymeacoffee](https://github.com/soxoj/socid-extractor/search?q=test_buymeacoffee) |  |
163 | Discourse API | [discourse_api](https://github.com/soxoj/socid-extractor/search?q=test_discourse_api) |  |
164 | Snapchat | [snapchat](https://github.com/soxoj/socid-extractor/search?q=test_snapchat) |  |
165 | Bio Site | [bio_site](https://github.com/soxoj/socid-extractor/search?q=test_bio_site) |  |
166 | Faceit API | [faceit_api](https://github.com/soxoj/socid-extractor/search?q=test_faceit_api) |  |
167 | Fansly API | [fansly_api](https://github.com/soxoj/socid-extractor/search?q=test_fansly_api) |  |
168 | Codewars API |  |  |
169 | Minds API |  |  |
170 | HackerNoon API |  |  |
171 | Polar API |  |  |
172 | thanks.dev API |  |  |
173 | Matrix profile API |  |  |
174 | osu! | [osu](https://github.com/soxoj/socid-extractor/search?q=test_osu) |  |
175 | Lens (Hey/Orb/Buttrfly) account | [lens_account](https://github.com/soxoj/socid-extractor/search?q=test_lens_account), [lens_account_absent](https://github.com/soxoj/socid-extractor/search?q=test_lens_account_absent) |  |
176 | HuggingFace API | [huggingface_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_huggingface_api_e2e) |  |
177 | HackerNews | [hackernews](https://github.com/soxoj/socid-extractor/search?q=test_hackernews) |  |
178 | Teletype | [teletype](https://github.com/soxoj/socid-extractor/search?q=test_teletype) |  |
179 | GDBrowser API | [gdbrowser_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_gdbrowser_api_e2e) |  |
180 | StreamElements API | [streamelements_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_streamelements_api_e2e) |  |
181 | Streamlabs API | [streamlabs_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_streamlabs_api_e2e) |  |
182 | Donatty API | [donatty_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_donatty_api_e2e) |  |
183 | VisnessCard API | [visnesscard_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_visnesscard_api_e2e) | requests from GitHub Actions CI servers are blocked |
184 | Codeforces API |  |  |
185 | Discogs API |  |  |
186 | iNaturalist API |  |  |
187 | Pronouny API |  |  |
188 | Zepeto API |  |  |
189 | OnlyFans API |  |  |
190 | eToro API |  |  |
191 | Gettr API |  |  |
192 | Habbo API |  |  |
193 | Hackadvisor API |  |  |
194 | Pillowfort JSON API |  |  |
195 | Scored API |  |  |
196 | YesWeHack API |  |  |
197 | Destream API |  |  |
198 | Tipeeestream API |  |  |
199 | Komi API |  |  |
200 | Cropty API |  |  |
201 | Redgifs API |  |  |
202 | Tappy API |  |  |
203 | Komoot API |  |  |
204 | Tapitag API |  |  |
205 | Vivino API |  |  |
206 | Google Scholar |  |  |
207 | Snapchat profile |  |  |
208 | Flipboard profile |  |  |
209 | Clubhouse profile |  |  |
210 | Coda.io profile |  |  |
211 | Poe.com profile |  |  |
212 | Gumroad profile |  |  |
213 | Mastodon HTML profile |  |  |
214 | Discourse HTML profile | [discourse_html_profile](https://github.com/soxoj/socid-extractor/search?q=test_discourse_html_profile) |  |
215 | Mastodon API |  |  |
216 | FL.ru |  |  |
217 | Manifold Markets |  |  |
218 | VSCO |  |  |
219 | Mojang API |  |  |
220 | OP.GG |  |  |
221 | coder.social |  |  |
222 | GOG |  |  |
223 | Kick API |  |  |
224 | Academia.edu |  |  |
225 | TradingView |  |  |
226 | Geocaching |  |  |
227 | Rutracker |  |  |
228 | Weburg |  |  |
229 | Pokemon Showdown |  |  |
230 | ImageShack |  |  |
231 | Replit |  |  |
232 | Itch.io |  |  |
233 | Giphy |  |  |
234 | Wattpad HTML profile |  |  |
235 | Venmo |  |  |
236 | Tumblr blog |  |  |
237 | Drive2.ru |  |  |
238 | Lichess API |  |  |
239 | Hackerrank API |  |  |
240 | Kongregate API |  |  |
241 | WordPress.com site API |  |  |
242 | Codecademy profile |  |  |
243 | About.me profile |  |  |
244 | Fur Affinity profile |  |  |
245 | Pikabu profile |  |  |
246 | Codepen profile |  |  |
247 | Letterboxd profile |  |  |
248 | Gitee profile |  |  |
249 | Slack workspace |  |  |
250 | Instructables member |  |  |
251 | Envato Author profile |  |  |
252 | Kwork freelancer |  |  |
253 | Freesound user |  |  |
254 | Star Citizen citizen |  |  |
255 | Dribbble profile |  |  |
256 | Depop shop |  |  |
257 | ModDB member |  |  |
258 | Xbox Gamertag |  |  |
259 | DonationAlerts streamer |  |  |
260 | CCM profile |  |  |
261 | Wikidot user |  |  |
262 | Couchsurfing person |  |  |
263 | ReverbNation artist |  |  |

The table has been updated at 2026-09-07 21:26:08.324494 UTC
