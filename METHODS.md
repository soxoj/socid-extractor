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
124 | MediaWiki API | [mediawiki_api](https://github.com/soxoj/socid-extractor/search?q=test_mediawiki_api) |  |
125 | MediaWiki user page | [mediawiki_user_page](https://github.com/soxoj/socid-extractor/search?q=test_mediawiki_user_page) |  |
126 | Fandom MediaWiki API |  |  |
127 | Substack public profile API |  |  |
128 | Lesswrong GraphQL API |  |  |
129 | hashnode GraphQL API |  |  |
130 | Rarible API |  |  |
131 | CSSBattle |  |  |
132 | Max (max.ru) profile |  |  |
133 | Bluesky API |  |  |
134 | Scratch API |  |  |
135 | DailyMotion API |  |  |
136 | SlideShare |  |  |
137 | WordPress.org Profile |  |  |
138 | Weebly |  |  |
139 | Calendly |  |  |
140 | Google Play Developer |  |  |
141 | Amazon Author |  |  |
142 | Habr |  |  |
143 | Taplink |  |  |
144 | Product Hunt |  |  |
145 | Chess.com HTML | [chess_com_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_chess_com_html_e2e) | chess.com HTML endpoint times out from CI (2026) |
146 | Roblox HTML | [roblox_html_e2e](https://github.com/soxoj/socid-extractor/search?q=test_roblox_html_e2e) |  |
147 | LeetCode GraphQL | [leetcode_graphql_e2e](https://github.com/soxoj/socid-extractor/search?q=test_leetcode_graphql_e2e) |  |
148 | Boosty API | [boosty_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_boosty_api_e2e) |  |
149 | Threads |  |  |
150 | Smule |  |  |
151 | Warpcast API | [warpcast_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_warpcast_api_e2e) |  |
152 | Paragraph API | [paragraph_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_paragraph_api_e2e) |  |
153 | Fragment | [fragment_e2e](https://github.com/soxoj/socid-extractor/search?q=test_fragment_e2e) |  |
154 | Tonometerbot | [tonometerbot_e2e](https://github.com/soxoj/socid-extractor/search?q=test_tonometerbot_e2e) | anti-bot / captcha / rate limiting from the site |
155 | Spatial | [spatial_e2e](https://github.com/soxoj/socid-extractor/search?q=test_spatial_e2e) | requests from GitHub Actions CI servers are blocked |
156 | OpenSea |  |  |
157 | Hive Blog |  |  |
158 | ORCID API |  |  |
159 | OpenAlex Authors API |  |  |
160 | arXiv author page |  |  |
161 | DBLP person record |  |  |
162 | Scholia author profile |  |  |
163 | BuyMeACoffee | [buymeacoffee](https://github.com/soxoj/socid-extractor/search?q=test_buymeacoffee) |  |
164 | Discourse API | [discourse_api](https://github.com/soxoj/socid-extractor/search?q=test_discourse_api) |  |
165 | Snapchat | [snapchat](https://github.com/soxoj/socid-extractor/search?q=test_snapchat) |  |
166 | Bio Site | [bio_site](https://github.com/soxoj/socid-extractor/search?q=test_bio_site) |  |
167 | Faceit API | [faceit_api](https://github.com/soxoj/socid-extractor/search?q=test_faceit_api) |  |
168 | Fansly API | [fansly_api](https://github.com/soxoj/socid-extractor/search?q=test_fansly_api) |  |
169 | Codewars API |  |  |
170 | Minds API |  |  |
171 | HackerNoon API |  |  |
172 | Polar API |  |  |
173 | thanks.dev API |  |  |
174 | Matrix profile API |  |  |
175 | osu! | [osu](https://github.com/soxoj/socid-extractor/search?q=test_osu) |  |
176 | Lens (Hey/Orb/Buttrfly) account | [lens_account](https://github.com/soxoj/socid-extractor/search?q=test_lens_account), [lens_account_absent](https://github.com/soxoj/socid-extractor/search?q=test_lens_account_absent) |  |
177 | HuggingFace API | [huggingface_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_huggingface_api_e2e) |  |
178 | HackerNews | [hackernews](https://github.com/soxoj/socid-extractor/search?q=test_hackernews) |  |
179 | Teletype | [teletype](https://github.com/soxoj/socid-extractor/search?q=test_teletype) |  |
180 | GDBrowser API | [gdbrowser_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_gdbrowser_api_e2e) |  |
181 | StreamElements API | [streamelements_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_streamelements_api_e2e) |  |
182 | Streamlabs API | [streamlabs_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_streamlabs_api_e2e) |  |
183 | Donatty API | [donatty_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_donatty_api_e2e) |  |
184 | VisnessCard API | [visnesscard_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_visnesscard_api_e2e) | requests from GitHub Actions CI servers are blocked |
185 | Codeforces API |  |  |
186 | Discogs API |  |  |
187 | iNaturalist API |  |  |
188 | Pronouny API |  |  |
189 | Zepeto API |  |  |
190 | OnlyFans API |  |  |
191 | eToro API |  |  |
192 | Gettr API |  |  |
193 | Habbo API |  |  |
194 | Hackadvisor API |  |  |
195 | Pillowfort JSON API |  |  |
196 | Scored API |  |  |
197 | YesWeHack API |  |  |
198 | Destream API |  |  |
199 | Tipeeestream API |  |  |
200 | Komi API |  |  |
201 | Cropty API |  |  |
202 | Redgifs API |  |  |
203 | Tappy API |  |  |
204 | Komoot API |  |  |
205 | Tapitag API |  |  |
206 | Vivino API |  |  |
207 | Google Scholar |  |  |
208 | Snapchat profile |  |  |
209 | Flipboard profile |  |  |
210 | Clubhouse profile |  |  |
211 | Coda.io profile |  |  |
212 | Poe.com profile |  |  |
213 | Gumroad profile |  |  |
214 | Mastodon HTML profile |  |  |
215 | Discourse HTML profile | [discourse_html_profile](https://github.com/soxoj/socid-extractor/search?q=test_discourse_html_profile) |  |
216 | Mastodon API |  |  |
217 | FL.ru |  |  |
218 | Manifold Markets |  |  |
219 | VSCO |  |  |
220 | Mojang API |  |  |
221 | OP.GG |  |  |
222 | coder.social |  |  |
223 | GOG |  |  |
224 | Kick API |  |  |
225 | Academia.edu |  |  |
226 | TradingView |  |  |
227 | Geocaching |  |  |
228 | Rutracker |  |  |
229 | Weburg |  |  |
230 | Pokemon Showdown |  |  |
231 | ImageShack |  |  |
232 | Replit |  |  |
233 | Itch.io |  |  |
234 | Giphy |  |  |
235 | Wattpad HTML profile |  |  |
236 | Venmo |  |  |
237 | Tumblr blog |  |  |
238 | Drive2.ru |  |  |
239 | Lichess API |  |  |
240 | Hackerrank API |  |  |
241 | Kongregate API |  |  |
242 | WordPress.com site API |  |  |
243 | Codecademy profile |  |  |
244 | About.me profile |  |  |
245 | Fur Affinity profile |  |  |
246 | Pikabu profile |  |  |
247 | Codepen profile |  |  |
248 | Letterboxd profile |  |  |
249 | Gitee profile |  |  |
250 | Slack workspace |  |  |
251 | Instructables member |  |  |
252 | Envato Author profile |  |  |
253 | Kwork freelancer |  |  |
254 | Freesound user |  |  |
255 | Star Citizen citizen |  |  |
256 | Dribbble profile |  |  |
257 | Depop shop |  |  |
258 | ModDB member |  |  |
259 | Xbox Gamertag |  |  |
260 | DonationAlerts streamer |  |  |
261 | CCM profile |  |  |
262 | Wikidot user |  |  |
263 | Couchsurfing person |  |  |
264 | ReverbNation artist |  |  |

The table has been updated at 2026-09-07 23:21:47.906618 UTC
