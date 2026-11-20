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
9 | Gitlab API | [gitlab_api](https://github.com/soxoj/socid-extractor/search?q=test_gitlab_api) |  |
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
43 | Habrahabr JSON | [habr](https://github.com/soxoj/socid-extractor/search?q=test_habr), [habr_no_image](https://github.com/soxoj/socid-extractor/search?q=test_habr_no_image) | requests from GitHub Actions CI servers are blocked, requests from GitHub Actions CI servers are blocked |
44 | My Mail.ru |  |  |
45 | Behance | [behance](https://github.com/soxoj/socid-extractor/search?q=test_behance) | broken |
46 | Blogger | [blogger](https://github.com/soxoj/socid-extractor/search?q=test_blogger) | Failed in GitHub CI |
47 | D3.ru | [d3](https://github.com/soxoj/socid-extractor/search?q=test_d3) | requests from GitHub Actions CI servers are blocked |
48 | Gitlab |  |  |
49 | 500px userByUsername API |  |  |
50 | 500px GraphQL API | [500px](https://github.com/soxoj/socid-extractor/search?q=test_500px) | broken |
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
123 | MediaWiki API | [mediawiki_api](https://github.com/soxoj/socid-extractor/search?q=test_mediawiki_api) |  |
124 | MediaWiki user page | [mediawiki_user_page](https://github.com/soxoj/socid-extractor/search?q=test_mediawiki_user_page) |  |
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
151 | Fragment | [fragment_e2e](https://github.com/soxoj/socid-extractor/search?q=test_fragment_e2e) | broken |
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
162 | Snapchat | [snapchat](https://github.com/soxoj/socid-extractor/search?q=test_snapchat) |  |
163 | Discourse API | [discourse_api](https://github.com/soxoj/socid-extractor/search?q=test_discourse_api) |  |
164 | Flarum API | [flarum_api](https://github.com/soxoj/socid-extractor/search?q=test_flarum_api) |  |
165 | Bio Site | [bio_site](https://github.com/soxoj/socid-extractor/search?q=test_bio_site) |  |
166 | Faceit API | [faceit_api](https://github.com/soxoj/socid-extractor/search?q=test_faceit_api) |  |
167 | Fansly API | [fansly_api](https://github.com/soxoj/socid-extractor/search?q=test_fansly_api) |  |
168 | bunq.me API | [bunq_me_api](https://github.com/soxoj/socid-extractor/search?q=test_bunq_me_api) |  |
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
179 | Teletype | [teletype](https://github.com/soxoj/socid-extractor/search?q=test_teletype) | down |
180 | GDBrowser API | [gdbrowser_api_e2e](https://github.com/soxoj/socid-extractor/search?q=test_gdbrowser_api_e2e) | cloudflare |
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
208 | Flipboard profile |  |  |
209 | Clubhouse profile |  |  |
210 | Coda.io profile |  |  |
211 | Poe.com profile |  |  |
212 | Gumroad profile |  |  |
213 | Mastodon HTML profile |  |  |
214 | Discourse HTML profile | [discourse_html_profile](https://github.com/soxoj/socid-extractor/search?q=test_discourse_html_profile) |  |
215 | Mastodon API | [mastodon_api](https://github.com/soxoj/socid-extractor/search?q=test_mastodon_api) |  |
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
264 | XenForo | [xenforo](https://github.com/soxoj/socid-extractor/search?q=test_xenforo) |  |
265 | Lemmy API | [lemmy_api](https://github.com/soxoj/socid-extractor/search?q=test_lemmy_api) |  |
266 | NodeBB API | [nodebb_api](https://github.com/soxoj/socid-extractor/search?q=test_nodebb_api) |  |
267 | phpBB | [phpbb](https://github.com/soxoj/socid-extractor/search?q=test_phpbb), [phpbb_author_search](https://github.com/soxoj/socid-extractor/search?q=test_phpbb_author_search) | requests from GitHub Actions CI servers are blocked |
268 | Gitea / Forgejo | [gitea_forgejo](https://github.com/soxoj/socid-extractor/search?q=test_gitea_forgejo) |  |
269 | bbPress | [bbpress](https://github.com/soxoj/socid-extractor/search?q=test_bbpress) |  |
270 | BuddyPress | [buddypress](https://github.com/soxoj/socid-extractor/search?q=test_buddypress) |  |
271 | Vanilla | [vanilla](https://github.com/soxoj/socid-extractor/search?q=test_vanilla), [vanilla_about_panel](https://github.com/soxoj/socid-extractor/search?q=test_vanilla_about_panel) |  |

The table has been updated at 2026-11-19 16:22:44.230847 UTC
