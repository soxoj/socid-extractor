from dateutil.parser import parse as parse_datetime_str
import html
import json
import itertools

from .utils import *

schemes = {
    'Yandex Disk file': {
        'flags': ['@yandexdisk', 'yastatic.net'],
        'regex': r'"users":{.*?"uid":"(?P<yandex_uid>\d+)","displayName":"(?P<name>.+?)"',
    },
    'Yandex Disk photoalbum': {
        'flags': ['yastatic.net/disk/album', 'isAvailableToAlbum'],
        'regex': r'"display_name":"(?P<name>.*?)","uid":"(?P<uid>\d+)","locale":"\w+","login":"(?P<username>.*?)"',
    },
    # https://music.yandex.ru/handlers/library.jsx?owner=
    'Yandex Music AJAX request': {
        'flags': ['{"success":true,"verified'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'fields': {
            'yandex_uid': lambda x: x['owner']['uid'],
            'username': lambda x: x['owner']['login'],
            'name': lambda x: x['owner']['name'],
            'image': lambda x: get_yandex_profile_pic(x['owner']['avatarHash']),
            'links': lambda x: [link for links in x['profiles'] for link in links['addresses']],
            'is_verified': lambda x: x['verified'],
            'liked_albums': lambda x: x['counts'].get('likedAlbums'),
            'liked_artists': lambda x: x['counts'].get('likedArtists'),
            'has_tracks': lambda x: x.get('hasTracks'),
        }
    },
    'Yandex Q (Znatoki) user profile': {
        'flags': ['Ya.Znatoki'],
        'regex': r'id="restoreData" type="application/json">({.+?})</script>',
        'extract_json': True,
        'transforms': [
            html.unescape,
            json.loads,
            lambda x: x['store']['entities'].get('user', {'':{}})[x['store']['page'].get('userStats', {}).get('id', '')],
            json.dumps,
        ],
        'fields': {
            'yandex_znatoki_id': lambda x: x['id'],
            'yandex_uid': lambda x: x['uuid'],
            'bio': lambda x: x['about'],
            'name': lambda x: x['displayName'],
            'image': lambda x: get_yandex_profile_pic(x.get('avatarId')),
            'is_org': lambda x: x.get('authOrg'),
            'is_banned': lambda x: x['banned'],
            'is_deleted': lambda x: x['deleted'],
            'created_at': lambda x: x['created'],
            'last_answer_at': lambda x: x.get('lastAnswerTime'),
            'rating': lambda x: x['rating'],
            'gender': lambda x: x['sex'],
            'links': lambda x: list(set(filter(lambda x: x, [x['url'], x.get('promoUrl'), x.get('socialContactUrl')]))),
            'verified_categories': lambda x: x.get('verifiedIn'),
            'is_from_q': lambda x: x.get('theqMerged'),
            'is_bad_or_shock': lambda x: x.get('badOrShock'),
            'is_excluded_from_rating': lambda x: x.get('excludeFromRating'),
            'teaser': lambda x: x.get('teaser'),
            'facebook_username': lambda x: x['socialFacebook'],
            'instagram_username': lambda x: x['socialInstagram'],
            'telegram_username': lambda x: x['socialTelegram'],
            'twitter_username': lambda x: x['socialTwitter'],
            'vk_username': lambda x: x['socialVkontakte'],
            'answers_count': lambda x: x.get('stats', {}).get('answersCount'),
            'following_count': lambda x: x.get('stats', {}).get('subscribersCount'),
        }
    },
    'Yandex Market user profile': {
        'flags': ['MarketNode', '{"entity":"user"'],
        'regex': r'{"user":({"entity":"user".+?}),"isEmptyList',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('login'),
            'yandex_uid': lambda x: x.get('uid'),
            'yandex_public_id': lambda x: x.get('publicId'),
            'fullname': lambda x: x.get('publicDisplayName'),
            'image': lambda x: x.get('avatar').replace('//', 'https://').replace('retina-50', '200'),
            'reviews_count': lambda x: x.get('grades'),
            'is_deleted': lambda x: x.get('isDeleted'),
            'is_hidden_name': lambda x: x.get('isDisplayNameEmpty'),
            'is_verified': lambda x: x.get('verified'),
            'linked_social': lambda x: [{
                'type': a['provider']['name'],
                'uid': a['userid'],
                'username': a['username'],
                'profile_id': a['profile_id']
            } for a in x.get('social')],
            'links': lambda x: list(itertools.chain(*[l.get('addresses') for l in x.get('social', [])])),
        },
    },
    'Yandex Music API': {
        'flags': ['invocationInfo', 'req-id"'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('result', {}),
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('login'),
            'yandex_uid': lambda x: x.get('uid'),
            'yandex_public_id': lambda x: x.get('publicId'),
            'fullname': lambda x: x.get('fullName'),
            'links': lambda x: x.get('socialProfiles'),
            'is_verified': lambda x: x.get('verified'),
            'has_tracks': lambda x: x.get('statistics', {}).get('hasTracks'),
            'liked_users': lambda x: x.get('statistics', {}).get('likedUsers'),
            'liked_by_users': lambda x: x.get('statistics', {}).get('likedByUsers'),
            'liked_artists': lambda x: x.get('statistics', {}).get('likedArtists'),
            'liked_albums': lambda x: x.get('statistics', {}).get('likedAlbums'),
            'ugc_tracks_count': lambda x: x.get('statistics', {}).get('ugcTracks'),
            'is_private_statistics': lambda x: x.get('statistics') == 'private',
            'is_private_social_profiles': lambda x: x.get('socialProfiles') == 'private',
        },
    },
    'Yandex Realty offer': {
        'flags': ['realty.yandex.ru/offer'],
        'regex': r'({"routing":{"locationBeforeTransitions.+?});',
        'extract_json': True,
        'fields': {
            'your_yuid': lambda x: x['user']['yuid'],
            'your_uid': lambda x: x['user']['uid'],
            'your_wallet_balance': lambda x: x['user']['walletInfo'].get('balance'),
            'your_emails': lambda x: ', '.join(x['user']['emails']),
            'your_name': lambda x: x['user'].get('displayName'),
            'your_username': lambda x: x['user'].get('defaultEmail'),
            'your_phone': lambda x: x['user'].get('defaultPhone'),
            'yandex_uid': lambda x: x['cards']['offers']['author']['id'],
            'name': lambda x: decode_ya_str(x['cards']['offers']['author']['agentName'])
        }
    },
    'Yandex Collections': {
        'flags': ['<meta name="collections"', '/collections'],
        'regex': r'(?:id="restoreData">)(.+?)<\/script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: list(x['entities']['users'].values())[1],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x.get('id'),
            'yandex_public_id': lambda x: x.get('public_id'),
            'fullname': lambda x: x.get('display_name'),
            'image': lambda x: get_yandex_profile_pic(x.get('default_avatar_id')),
            'gender': lambda x: x.get('sex'),
            'description': lambda x: x.get('description'),
            'phone_id': lambda x: x.get('phone_id'),
            'company_info': lambda x: x.get('company_info'),
            'likes': lambda x: x['stats'].get('likes'),
            'cards': lambda x: x['stats'].get('cards'),
            'boards': lambda x: x['stats'].get('boards'),
            # TODO: other stats
            'is_passport': lambda x: x.get('is_passport'),
            'is_restricted': lambda x: x.get('is_restricted'),
            'is_forbid': lambda x: x.get('is_forbid'),
            'is_verified': lambda x: x.get('is_verified'),
            'is_km': lambda x: x.get('is_km'),
            'is_business': lambda x: x.get('is_business'),

        }
    },
    'Yandex Collections API': {
        'flags': ['board_subscriptions', 'subscriptions_on_self_boards'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'fields': {
            'id': lambda x: x.get('id'),
            'yandex_public_id': lambda x: x.get('public_id'),
            'fullname': lambda x: x.get('display_name'),
            'image': lambda x: get_yandex_profile_pic(x.get('default_avatar_id')),
            'gender': lambda x: x.get('sex'),
            'description': lambda x: x.get('description'),
            'phone_id': lambda x: x.get('phone_id'),
            'company_info': lambda x: x.get('company_info'),
            'likes': lambda x: x['stats'].get('likes'),
            'cards': lambda x: x['stats'].get('cards'),
            'boards': lambda x: x['stats'].get('boards'),
            # TODO: other stats
            'is_passport': lambda x: x.get('is_passport'),
            'is_restricted': lambda x: x.get('is_restricted'),
            'is_forbid': lambda x: x.get('is_forbid'),
            'is_verified': lambda x: x.get('is_verified'),
            'is_km': lambda x: x.get('is_km'),
            'is_business': lambda x: x.get('is_business'),
        }
    },
    'Yandex Reviews user profile': {
        'flags': ['isInternalYandexNet', 'ReviewFormContent'],
        'regex': r'window.__PRELOADED_DATA = ({[\s\S]+?})\n\s+}catch',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['pageData']['initialState'],
            json.dumps,
        ],
        'fields': {
            'yandex_public_id': lambda x: x.get('pkUser', {}).get('publicId'),
            'fullname': lambda x: decode_ya_str(x.get('pkUser', {}).get('name')),
            'image': lambda x: get_yandex_profile_pic(x.get('pkUser', {}).get('pic')),
            'is_verified': lambda x: x.get('pkUser', {}).get('verified'),
            'reviews_count': lambda x: len(x.get('reviews', {}).get('all', {}).keys()),
            'following_count': lambda x: x.get('subscription', {}).get('subscribersCount'),
            'follower_count': lambda x: x.get('subscription', {}).get('subscriptionsCount'),
        },
    },
    'Yandex Zen user profile': {
        'flags': ['https://zen.yandex.ru/user/', 'zen-lib'],
        'regex': r'\n\s+var data = ({"__[\s\S]+?});\n',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: list(filter(lambda y: '__serverState' in y[0], x.items())),
            lambda x: x[0][1]['channel']['source'],
            json.dumps,
        ],
        'fields': {
            'yandex_public_id': lambda x: x.get('publicId'),
            'fullname': lambda x: x.get('title'),
            'image': lambda x: x.get('logo'),
            'bio': lambda x: x.get('description'),
            'yandex_messenger_guid': lambda x: x.get('messengerGuid'),
            'links': lambda x: x.get('socialLinks'),
            'type': lambda x: x.get('type'),
            'comments_count': lambda x: x.get('userCommentsCount'),
            'status': lambda x: x.get('socialProfileStatus'),
            'following_count': lambda x: x.get('subscribers'),
            'follower_count': lambda x: x.get('subscriptions'),
        },
    },
    'Yandex messenger search API': {
        'flags': ['messages', 'matches', 'users_and_chats'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['data']['users_and_chats']['items'],
            lambda x: x if len(x) == 1 else list(filter(lambda y: y['matches'].get('nickname'), x)),
            lambda x: x[0] if x else {},
            json.dumps,
        ],
        'fields': {
            'fullname': lambda x: x['data']['display_name'],
            'username': lambda x: x['matches'].get('nickname', [None])[0],
            'yandex_messenger_guid': lambda x: x['data']['guid'],
            'registration_status': lambda x: x['data']['registration_status'],
            'image': lambda x: get_yandex_profile_pic(x['data'].get('avatar_id')),
            'yandex_phone_id': lambda x: x['data'].get('phone_id'),
            'yandex_uid': lambda x: x['data'].get('uid'),
        },
    },
    'Yandex messenger profile API': {
        'flags': ['guid', 'registration_status', 'contacts'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['data']['users'][0],
            json.dumps,
        ],
        'fields': {
            'fullname': lambda x: x['display_name'],
            'yandex_messenger_guid': lambda x: x['guid'],
            'registration_status': lambda x: x['registration_status'],
            'image': lambda x: get_yandex_profile_pic(x.get('avatar_id')),
            'yandex_phone_id': lambda x: x.get('phone_id'),
        },
    },
    'Yandex Bugbounty user profile': {
        'flags': ['yandex_bug_bounty_terms_conditions', 'user__pic'],
        'regex': r'upics\.yandex\.net\/(?P<yandex_uid>\d+)[\s\S]+<span>(?P<firstname>.+?)<\/span>\s+<em>(?P<username>.+?)<\/em>([\s\S]+?class="link">(?P<email>.+?)<\/a>)?([\s\S]+?<a href="(?P<url>.+?)" target="_blank" class="link link_social">)?',
    },
    'VK user profile': {
        'flags': ['Profile.init({', 'change_current_info'],
        'regex': r'Profile\.init\({"user_id":(?P<vk_id>\d+).*?(,"loc":"(?P<vk_username>.*?)")?,"back":"(?P<fullname>.*?)"'
    },
    'VK closed user profile': {
        'flags': ['var vk =', 'page_current_info'],
        'regex': r'<h1 class="page_name">(?P<fullname>.*?)</h1>'
    },
    'VK blocked user profile': {
        'flags': ['window.vk = {', '/images/deactivated_50.png'],
        'regex': r'<h2 class="op_header">(?P<fullname>.+?)</h2>'
    },
    'Gravatar': {
        'flags': ['gravatar.com\\/avatar', 'thumbnailUrl'],
        'regex': r'^(.+?)$',
        'extract_json': True,
        'fields': {
            'gravatar_id': lambda x: x['entry'][0]['id'],
            'gravatar_username': lambda x: x['entry'][0]['preferredUsername'],
            'fullname': lambda x: x['entry'][0]['displayName'],
            'location': lambda x: x['entry'][0].get('currentLocation'),
            'emails': lambda x: [y['value'] for y in x['entry'][0].get('emails', [])],
            'links': lambda x: [y['url'] for y in x['entry'][0].get('accounts', [])],
        }
    },
    'Instagram': {
        'flags': ['instagram://user?username'],
        'regex': r'window._sharedData =(.+?);</script>',
        'extract_json': True,
        'fields': {
            'instagram_username': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('username'),
            'fullname': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('full_name'),
            'id': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('id'),
            'image': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('profile_pic_url_hd'),
            'bio': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('biography'),
            'business_email': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('business_email'),
            'external_url': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('external_url'),
        }
    },
    'Spotify API': {
        'flags': ['"uri": "spotify:user:'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('name'),
            'follower_count': lambda x: x.get('followers_count'),
            'following_count': lambda x: x.get('following_count'),
            'image': lambda x: x.get('image_url', ''),
        }
    },
    'EyeEm': {
        'flags': ['window.__APOLLO_STATE__', 'cdn.eyeem.com/thumb'],
        'regex': r'__APOLLO_STATE__ = ({.+?});\n',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: list(filter(lambda x: 'User:' in x[0], x.items()))[0][1],
            json.dumps,
        ],
        'fields': {
            'eyeem_id': lambda x: x['id'],
            'eyeem_username': lambda x: x['nickname'],
            'fullname': lambda x: x['fullname'],
            'bio': lambda x: x['description'],
            'follower_count': lambda x: x['totalFollowers'],
            'friends': lambda x: x['totalFriends'],
            'liked_photos': lambda x: x['totalLikedPhotos'],
            'photos': lambda x: x['totalPhotos'],
            'facebook_uid': lambda x: extract_facebook_uid(x['thumbUrl'])
        }
    },
    'Medium': {
        'flags': ['https://medium.com', 'com.medium.reader'],
        'regex': r'__APOLLO_STATE__ = ({.+})',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: [v for k,v in x.items() if k.startswith('User:')][0],
            json.dumps,
        ],
        'fields': {
            'medium_id': lambda x: x.get('id'),
            'medium_username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name'),
            'bio': lambda x: x.get('bio'),
            'twitter_username': lambda x: x.get('twitterScreenName'),
            'is_suspended': lambda x: x.get('isSuspended'),
            'facebook_uid': lambda x: x.get('facebookAccountId'),
            'is_blocking': lambda x: x.get('isBlocking'),
            'is_muting': lambda x: x.get('isMuting'),
            'post_counts': lambda x: x.get('userPostCounts'),
        }
    },
    'Odnoklassniki': {
        'flags': ['OK.startupData'],
        'regex': r'path:"/(profile/)?(?P<ok_user_name_id>.+?)",state:".+?friendId=(?P<ok_id>\d+?)"',
    },
    'Habrahabr': {
        'flags': ['habracdn.net'],
        'bs': True,
        'fields': {
            'uid': lambda x: x.find('div', {'class': 'user-info__stats'}).parent.attrs['class'][-1].split('_')[-1],
            'username': lambda x: x.find('a', {'class': 'media-obj__image'}).get('href').split('/')[-2],
            'image': lambda x: 'http:' + x.find('div', {'class': 'user-info__stats'}).find('img').get('src'),
        },
    },
    # unactual
    'Twitter HTML': {
        'flags': ['abs.twimg.com', 'moreCSSBundles'],
        'regex': r'{&quot;id&quot;:(?P<uid>\d+),&quot;id_str&quot;:&quot;\d+&quot;,&quot;name&quot;:&quot;(?P<username>.*?)&quot;,&quot;screen_name&quot;:&quot;(?P<name>.*?)&quot;'
    },
    # https://shadowban.eu/.api/user
    # https://gist.github.com/superboum/ab31bc4c85c731b9e89ebda5eaed9a3a
    'Twitter Shadowban': {
        'flags': ['"timestamp"', '"profile": {', 'has_tweets'],
        'regex': r'^({.+?})$',
        'extract_json': True,
        'fields': {
            'has_tweets': lambda x: x['profile'].get('has_tweets'),
            'username': lambda x: x['profile'].get('screen_name'),
            'is_exists': lambda x: x['profile'].get('exists'),
            'is_suspended': lambda x: x['profile'].get('suspended'),
            'is_protected': lambda x: x['profile'].get('protected'),
            'has_ban': lambda x: x.get('tests', {}).get('ghost', {}).get('ban'),
            'has_banned_in_search_suggestions': lambda x: not x['tests']['typeahead'] if x.get('tests', {}).get('typeahead') else None,
            'has_search_ban': lambda x: not x['tests']['search'] if x.get('tests', {}).get('search') else None,
            'has_never_replies': lambda x: not x['tests']['more_replies']['tweet'] if x.get('tests', {}).get('more_replies', {}).get('tweet') else None,
            'is_deboosted': lambda x: x['tests']['more_replies']['ban'] if x.get('tests', {}).get('more_replies', {}).get('ban') else None,
        }
    },
    'Twitter GraphQL API': {
        'flags': ['{"data":{"'],
        'regex': r'^{"data":{"user":({.+})}}$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'fullname': lambda x: x.get('legacy', {}).get('name'),
            'bio': lambda x: x.get('legacy', {}).get('description'),
            'created_at': lambda x: parse_datetime_str(x.get('legacy', {}).get('created_at', '')),
            'image': lambda x: x.get('legacy', {}).get('profile_image_url_https', '').replace('_normal', ''),
            'image_bg': lambda x: x.get('legacy', {}).get('profile_banner_url'),
            'is_protected': lambda x: x.get('legacy', {}).get('protected'),
            'follower_count': lambda x: x.get('legacy', {}).get('followers_count'),
            'following_count': lambda x: x.get('legacy', {}).get('friends_count'),
            'location': lambda x: x.get('legacy', {}).get('location'),
            'favourites_count': lambda x: x.get('legacy', {}).get('favourites_count'),
            'links': lambda x: [y.get('expanded_url') for y in x.get('legacy', {}).get('entities', {}).get('url', {}).get('urls', [])],
        }
    },
    'Facebook user profile': {
        'flags': ['com.facebook.katana', 'scribe_endpoint'],
        'regex': r'{"imp_id":".+?","ef_page":.+?,"uri":".+?\/(?P<username>[^\/]+?)","entity_id":"(?P<uid>\d+)"}',
    },
    'Facebook group': {
        'flags': ['com.facebook.katana', 'XPagesProfileHomeController'],
        'regex': r'{"imp_id":".+?","ef_page":.+?,"uri":".+?\/(?P<username>[^\/]+?)","entity_id":"(?P<uid>\d+)"}',
    },
    'GitHub HTML': {
        'flags': ['github.githubassets.com'],
        'regex': r'data-scope-id="(?P<uid>\d+)" data-scoped-search-url="/users/(?P<username>.+?)/search"'
    },
    # https://api.github.com/users/torvalds
    'GitHub API': {
        'flags': ['gists_url', 'received_events_url'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'image': lambda x: x.get('avatar_url'),
            'created_at': lambda x: x.get('created_at'),
            'location': lambda x: x.get('location'),
            'follower_count': lambda x: x.get('followers'),
            'following_count': lambda x: x.get('following'),
            'fullname': lambda x: x.get('name'),
            'public_gists_count': lambda x: x.get('public_gists'),
            'public_repos_count': lambda x: x.get('public_repos'),
            'twitter_username': lambda x: x.get('twitter_username'),
            'is_looking_for_job': lambda x: x.get('hireable'),
            'gravatar_id': lambda x: x.get('gravatar_id'),
            'bio': lambda x: x['bio'].strip() if x.get('bio', '') else None,
            'is_company': lambda x: x.get('company'),
            'blog_url': lambda x: x.get('blog'),
        }
    },
    'Gitlab API': {
        'flags': ['"web_url":"https://gitlab.com/'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x[0].get('id'),
        }
    },
    'My Mail.ru': {
        'flags': ['my.mail.ru', 'models/user/journal">'],
        'regex': r'journal">\s+({\s+"name":[\s\S]+?})',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('dir').split('/')[-2] if x else '',
            'auId': lambda x: x.get('auId'),
            'email': lambda x: x.get('email'),
            'name': lambda x: x.get('name'),
            'isVip': lambda x: x.get('isVip'),
            'isCommunity': lambda x: x.get('isCommunity'),
            'isVideoChannel': lambda x: x.get('isVideoChannel'),
        }
    },
    'Behance': {
        'flags': ['behance.net', 'beconfig-store_state'],
        'message': 'Cookies required, ensure you added --cookies "ilo0=1"',
        'regex': r'{"id":(?P<uid>\d+),"first_name":"(?P<first_name>[^"]+)","last_name":"(?P<last_name>[^"]+)","username":"(?P<username>[^"]+)"',
    },
    'Blogger': {
        'flags': ['www.blogger.com/static', 'blogspot.com/feeds/posts'],
        'regex': r'www.blogger.com\/feeds\/(?P<blog_id>\d+)\/posts\/default" \/>\n<link rel="me" href="https:\/\/www.blogger.com\/profile/(?P<uid>\d+)" \/>',
    },
    'D3.ru': {
        'flags': ['feedSettingsHandler.subscribe(this', 'd3.ru/static'],
        'regex': r"feedSettingsHandler.subscribe\(this, 'users', '(?P<uid>\d+)'",
    },
    'Gitlab': {
        'flags': ['gitlab-static.net'],
        'regex': r'abuse_reports.+?user_id=(?P<uid>\d+)"',
    },
    '500px GraphQL API': {
        'flags': ['{"data":{"profile":{"id"'],
        'regex': r'^{"data":({.+})}$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['profile']['id'],
            'legacy_id': lambda x: x['profile']['legacyId'],
            'username': lambda x: x['profile']['username'],
            'name': lambda x: x['profile']['displayName'],
            'created_at': lambda x: x['profile']['registeredAt'],
            'image': lambda x: x['profile']['avatar']['images'][-1]['url'],
            'image_bg': lambda x: x['profile']['coverPhotoUrl'],
            'qq_username': lambda x: x['profile']['socialMedia'].get('qq'),
            'website': lambda x: x['profile']['socialMedia'].get('website'),
            'blog': lambda x: x['profile']['socialMedia'].get('blog'),
            'lastfm_username': lambda x: x['profile']['socialMedia'].get('lastfm'),
            'facebook_link': lambda x: x['profile']['socialMedia'].get('facebook'),
            'msn_username': lambda x: x['profile']['socialMedia'].get('MSN'),
            'facebook_page': lambda x: x['profile']['socialMedia'].get('facebookpage'),
            'livejournal_username': lambda x: x['profile']['socialMedia'].get('livejournal'),
            'instagram_username': lambda x: x['profile']['socialMedia'].get('instagram'),
            'twitter_username': lambda x: x['profile']['socialMedia'].get('twitter'),
            'skype_username': lambda x: x['profile']['socialMedia'].get('skype'),
            'thumblr_username': lambda x: x['profile']['socialMedia'].get('thumblr'),
            'gtalk_username': lambda x: x['profile']['socialMedia'].get('gtalk'),
            'icq_uid': lambda x: x['profile']['socialMedia'].get('icq'),
            'flickr_username': lambda x: x['profile']['socialMedia'].get('flickr'),
            'lookatme_username': lambda x: x['profile']['socialMedia'].get('LOOKATME'),
            'googleplus_uid': lambda x: x['profile']['socialMedia'].get('googleplus'),
        }
    },
    'Google Document': {
        'flags': ['_docs_flag_initialData'],
        'regex': r'({"docs-ails":"docs_\w+".+?});',
        'extract_json': True,
        'message': 'Auth cookies requires, add through --cookies in format "a=1;b=2"n\nTry to run twice to get result.',
        'fields': {
            'your_ls_uid': lambda x: x.get('docs-offline-lsuid'),
            'your_cpf': lambda x: x.get('docs-cpf'),
            'your_username': lambda x: x.get('docs-offline-ue') or x.get('docs-hue'),
            'your_uid': lambda x: x['docs-pid'],
            'org_name': lambda x: x['docs-doddn'],
            'org_domain': lambda x: x['docs-dodn'],
        }
    },
    'Google Maps contributions': {
        'flags': ['/maps/preview/opensearch.xml', '<meta content="Contributions by'],
        'regex': r'"Contributions by (?P<name>.+?)",("(?P<contributions_count>\d+) Contribution|"(?P<contribution_level>.+?)")',
    },
    'Youtube Channel': {
        'flags': ['<span itemprop="author" itemscope itemtype="http://schema.org/Person">'],
        'regex': r'itemtype="http:\/\/schema\.org\/Person"[\s\S]+?https:\/\/plus\.google\.com\/(?P<gaia_id>\d+)">[\s\S]+?itemprop="name" content="(?P<name>.+?)"'
    },
    'Bitbucket': {
        'flags': ['https://api.bitbucket.org'],
        'regex': r'({.+?"section": {"profile.+?"whats_new_feed":.+?}});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['global']['targetUser']['uuid'].strip('{}'),
            'username': lambda x: x['global']['targetUser']['nickname'],
            'created_at': lambda x: x['global']['targetUser']['created_on'],
            'is_service': lambda x: x['global']['targetUser']['is_staff'],
        }
    },
    'Pinterest API': {
        'flags': ['{"resource_response":{"status"'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['resource_response']['data'],
            json.dumps,
        ],
        'fields': {
            'pinterest_id': lambda x: x.get('id'),
            'pinterest_username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('full_name'),
            'bio': lambda x: x.get('about'),
            'type': lambda x: x.get('type'),
            'image': lambda x: x.get('image_xlarge_url'),
            'board_count': lambda x: x.get('board_count'),
            'pin_count': lambda x: x.get('pin_count'),
            'location': lambda x: x.get('location'),
            'country': lambda x: x.get('country'),
            'follower_count': lambda x: x.get('follower_count'),
            'following_count': lambda x: x.get('following_count'),
            'group_board_count': lambda x: x.get('group_board_count'),
            'last_pin_save_datetime': lambda x: x.get('last_pin_save_time'),
            'is_website_verified': lambda x: x.get('domain_verified'),
            'website': lambda x: x.get('website_url'),
            'has_board': lambda x: x.get('has_board'),
            'has_catalog': lambda x: x.get('has_catalog'),
            'is_indexed': lambda x: x.get('indexed'),
            'is_partner': lambda x: x.get('is_partner'),
            'is_tastemaker': lambda x: x.get('is_tastemaker'),
            'is_verified_merchant': lambda x: x.get('is_verified_merchant'),
            'verified_identity': lambda x: check_empty_object(x.get('verified_identity')),
            'locale': lambda x: x.get('locale'),
        }
    },
    'Pinterest profile/board page': {
        'flags': ['https://s.pinimg.com/webapp/', 'content="Pinterest"'],
        'regex': r'<script id="initial-state" type="application/json">({.+?})</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['resourceResponses'][0]['response']['data'],
            lambda x: x['user'] if 'user' in x else x.get('owner'),
            json.dumps,
        ],
        'fields': {
            'pinterest_id': lambda x: x.get('id'),
            'pinterest_username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('full_name'),
            'bio': lambda x: x.get('about'),
            'type': lambda x: x.get('type'),
            'image': lambda x: x.get('image_xlarge_url'),
            'board_count': lambda x: x.get('board_count'),
            'pin_count': lambda x: x.get('pin_count'),
            'location': lambda x: x.get('location'),
            'country': lambda x: x.get('country'),
            'follower_count': lambda x: x.get('follower_count'),
            'following_count': lambda x: x.get('following_count'),
            'is_website_verified': lambda x: x.get('domain_verified'),
            'website': lambda x: x.get('domain_url'),
            'is_indexed': lambda x: x.get('indexed'),
            'is_partner': lambda x: x.get('is_partner'),
            'is_tastemaker': lambda x: x.get('is_tastemaker'),
            'is_verified_merchant': lambda x: x.get('is_verified_merchant'),
            'verified_identity': lambda x: check_empty_object(x.get('verified_identity')),
            'locale': lambda x: x.get('locale'),
        }
    },
    'Reddit': {
        'flags': ['<link rel="canonical" href="https://www.reddit.com/user/'],
        'regex': r'___r = ({.+?});<\/script><script>',
        'extract_json': True,
        'transforms': [
            lambda x: json.dumps(list(json.loads(x)['users']['models'].values())[0]),
        ],
        'fields': {
            'reddit_id': lambda x: x['profileId'],
            'reddit_username': lambda x: x['username'],
            'fullname': lambda x: x['displayName'],
            'image': lambda x: x['accountIcon'],
            'is_employee': lambda x: x['isEmployee'],
            'is_nsfw': lambda x: x['isNSFW'],
            'is_mod': lambda x: x['isMod'],
            'is_following': lambda x: x['isFollowing'],
            'has_user_profile': lambda x: x['hasUserProfile'],
            'hide_from_robots': lambda x: x['hideFromRobots'],
            'created_at': lambda x: timestamp_to_datetime(x['createdUtc']),
            'total_karma': lambda x: x['totalKarma'],
            'post_karma': lambda x: x['postKarma'],
        },
    },
    'Steam': {
        'flags': ['store.steampowered.com', 'profile_header_bg_texture'],
        'regex': r'({"url":".+?});',
        'extract_json': True,
        'fields': {
            'steam_id': lambda x: x['steamid'],
            'nickname': lambda x: x['personaname'],  # это не совсем имя, а ник
            'username': lambda x: [y for y in x['url'].split('/') if y][-1],
        }
    },
    'Steam Addiction': {
        # TODO: добавить отображение предыдущих ников по ссылке /ajaxaliases/, например https://steamcommunity.com/profiles/76561198222448544/ajaxaliases/
        'flags': ['steamcommunity.com'],
        'regex': r'<bdi><span class="filtered_text">(?P<real_name>.+)<\/span><\/bdi>(\s*&nbsp;\s*<img class="profile_flag" src=".*">\s*(?P<country>.*)<\/div>)*',
    },
    'Stack Overflow & similar': {
        'flags': ['StackExchange.user.init'],
        'regex': r'StackExchange.user.init\({ userId: (?P<uid>\d+), accountId: (?P<stack_exchange_uid>\d+) }\);',
    },
    'SoundCloud': {
        'flags': ['eventlogger.soundcloud.com'],
        'regex': r'catch\(e\)\{\}\}\)\},(\[\{"id":.+?)\);',
        'extract_json': True,
        'message': 'Run with auth cookies to get your ids.',
        'fields': {
            # 'your_uid': lambda x: x[-2]['data'][0].get('id'),
            # 'your_name': lambda x: x[-2]['data'][0].get('full_name'),
            # 'your_username': lambda x: x[-2]['data'][0].get('username'),
            'uid': lambda x: x[-1]['data'][0]['id'],
            'name': lambda x: x[-1]['data'][0]['full_name'],
            'username': lambda x: x[-1]['data'][0]['username'],
            'following_count': lambda x: x[-1]['data'][0]['followings_count'],
            'follower_count': lambda x: x[-1]['data'][0]['followers_count'],
            'is_verified': lambda x: x[-1]['data'][0]['verified'],
            'image': lambda x: x[-1]['data'][0]['avatar_url'],
            'location': lambda x: x[-1]['data'][0]['city'],
            'country_code': lambda x: x[-1]['data'][0]['country_code'],
            'bio': lambda x: x[-1]['data'][0]['description'],
            'created_at': lambda x: x[-1]['data'][0]['created_at'],
        }
    },
    'TikTok': {
        'flags': ['tiktokcdn.com', '__NEXT_DATA__'],
        'regex': r'<script id="__NEXT_DATA__" type="application/json" crossorigin="anonymous">(.+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['props']['pageProps'].get('userInfo', {}),
            json.dumps,
        ],
        'fields': {
            'tiktok_id': lambda x: x['user']['id'],
            'tiktok_username': lambda x: x['user']['uniqueId'],
            'fullname': lambda x: x['user']['nickname'],
            'bio': lambda x: x['user']['signature'],
            'image': lambda x: x['user']['avatarMedium'],
            'is_verified': lambda x: x['user']['verified'],
            'is_secret': lambda x: x['user']['secret'],
            'sec_uid': lambda x: x['user']['secUid'],
            'following_count': lambda x: x['stats']['followingCount'],
            'follower_count': lambda x: x['stats']['followerCount'],
            'heart_count': lambda x: x['stats']['heartCount'],
            'video_count': lambda x: x['stats']['videoCount'],
            'digg_count': lambda x: x['stats']['diggCount'],
        }
    },
    'VC.ru': {
        'flags': ['property="og:site_name" content="vc.ru"', '"subsite":{"id"'],
        'regex': r'({"module.page":{.+});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['module.page']['subsite']['id'],
            'name': lambda x: x['module.page']['subsite']['name'],
            'username': lambda x: x['module.page']['subsite']['url'].split('/')[-1],
        }
    },
    'LiveJournal': {
        'flags': ['Site.journal'],
        'regex': r'Site.journal = ({".+?"});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['id'],
            'is_paid': lambda x: x['is_paid'],
            'is_news': lambda x: x['is_news'],
            'is_identity': lambda x: x['is_identity'],
            'is_medius': lambda x: x['is_medius'],
            'is_permanent': lambda x: x['is_permanent'],
            'is_community': lambda x: x['is_community'],
            'is_personal': lambda x: x['is_personal'],
            'is_suspended': lambda x: x['is_suspended'],
            'is_bad_content': lambda x: x['is_bad_content'],
            'username': lambda x: x['username'],
            'name': lambda x: x['display_username'],
        }
    },
    'MySpace': {
        'flags': ['myspacecdn.com'],
        'regex': r'context = ({.+?});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['displayProfileId'],
            'username': lambda x: x['filterStreamUrl'].split('/')[2],
        }
    },
    'Keybase API': {
        'flags': ['{"status":{"code":0,"name":"OK"},"them":'],
        'regex': r'^(.+?"them":\[{.+?}\]})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['them'][0]['id'],
            'username': lambda x: x['them'][0]['basics']['username'],
            'name': lambda x: x['them'][0].get('profile', {}).get('full_name'),
            'location': lambda x: x['them'][0].get('profile', {}).get('location'),
            'bio': lambda x: x['them'][0].get('profile', {}).get('bio'),
            'twitter_username': lambda x: x['them'][0]['proofs_summary']['by_presentation_group'].get('twitter', [{}])[
                0].get('nametag'),
            'github_username': lambda x: x['them'][0]['proofs_summary']['by_presentation_group'].get('github', [{}])[
                0].get('nametag'),
            'reddit_username': lambda x: x['them'][0]['proofs_summary']['by_presentation_group'].get('reddit', [{}])[
                0].get('nametag'),
            'hackernews_username': lambda x:
            x['them'][0]['proofs_summary']['by_presentation_group'].get('hackernews', [{}])[0].get('nametag'),
        }
    },
    'Wikimapia': {
        'flags': ['src="/js/linkrouter.js', 'container-fluid inner-page'],
        'regex': r'<tr class="current">[\s\S]{10,100}a href="\/user\/(?P<wikimapia_uid>\d+)">\n\s+.{10,}\n\s+<strong>(?P<username>.+?)<\/strong>[\s\S]{50,200}<\/tr>',
    },
    # unactual
    'Vimeo HTML': {
        'flags': ['https://i.vimeocdn.com/favicon/main-touch'],
        'regex': r'"app_config":({"user":.+?})},\"coach_notes',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['user']['id'],
            'name': lambda x: x['user']['display_name'],
            'username': lambda x: x['user']['name'],
            'location': lambda x: x['user']['location'],
            'created_at': lambda x: x['user']['join_date']['raw'],
            'account_type': lambda x: x['user']['account_type'],
            'is_staff': lambda x: x['user']['is_staff'],
            'links': lambda x: [a['url'] for a in x['user']['links']],
        }
    },
    'Vimeo GraphQL API': {
        'flags': ['{\n    "uri": "/users/'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['uri'].split('/')[-1],
            'gender': lambda x: x['gender'],
            'image': lambda x: x['pictures'].get('sizes', [{'link': ''}])[-1]['link'],
            'bio': lambda x: x.get('bio'),
            'location': lambda x: x['location_details'].get('formatted_address'),
            'username': lambda x: x['name'],
            'is_verified': lambda x: x['verified'],
            'skills': lambda x: ','.join(x['skills']),
            'created_at': lambda x: x['created_time'],
            'videos': lambda x: x['metadata']['public_videos']['total'],
            'is_looking_for_job': lambda x: x['available_for_hire'],
            'is_working_remotely': lambda x: x['can_work_remotely'],
        }
    },
    'DeviantArt': {
        'flags': ['window.deviantART = '],
        'regex': r'({\\"username\\":\\".+?\",\\"country.+?legacyTextEditUrl.+?})},\\"\d+\\":{\\"id',
        'extract_json': True,
        'transforms': [
            lambda x: x.replace('\\"', '"'),
            lambda x: x.replace('\\\\"', '\''),
            lambda x: x.replace('\\\\u002F', '/'),
        ],
        'fields': {
            'country': lambda x: x['country'],
            'created_at': lambda x: timestamp_to_datetime(x['deviantFor']),
            'gender': lambda x: x['gender'],
            'username': lambda x: x['username'],
            'twitter_username': lambda x: x['twitterUsername'],
            'website': lambda x: x['website'],
            'links': lambda x: [y['value'] for y in x['socialLinks']],
            'tagline': lambda x: x['tagline'],
        }
    },
    'Flickr': {
        'flags': ['api.flickr.com', 'photostream-models', 'person-profile-models'],
        'regex': r'modelExport:(.*),[\s\S]*auth',
        'extract_json': True,
        'transforms': [
            lambda x: x.replace('%20', ' '),
            lambda x: x.replace('%2C', ','),
            json.loads,
            lambda x: x['main'],
            json.dumps,
        ],
        'fields': {
            'flickr_id': lambda x: x['photostream-models'][0]['owner']['id'],
            'flickr_username': lambda x: x['photostream-models'][0]['owner'].get('pathAlias'),
            'flickr_nickname': lambda x: x['photostream-models'][0]['owner']['username'],
            'fullname': lambda x: x['photostream-models'][0]['owner'].get('realname'),
            'location': lambda x: x['person-profile-models'][0].get('location'),
            'image': lambda x: 'https:' + x['photostream-models'][0]['owner']['buddyicon']['retina'],
            'photo_count': lambda x: x['person-profile-models'][0]['photoCount'],
            'follower_count': lambda x: x['person-contacts-count-models'][0]['followerCount'],
            'following_count': lambda x: x['person-contacts-count-models'][0]['followingCount'],
            'created_at': lambda x: timestamp_to_datetime(x['photostream-models'][0]['owner'].get('dateCreated', 0)),
            'is_pro': lambda x: x['photostream-models'][0]['owner'].get('isPro'),
            'is_deleted': lambda x: x['photostream-models'][0]['owner'].get('isDeleted'),
            'is_ad_free': lambda x: x['photostream-models'][0]['owner'].get('isAdFree'),
        }
    },
    'mssg.me': {
        'flags': ['content="https://mssg.me/'],
        'regex': r'window.INITIAL_DATA = (.*);[\s\S]*window.LOCALES',
        'extract_json': True,
        'fields': {
            'fullname': lambda x: x['card']['profile']['fullname'],
            'bio': lambda x: x['card']['profile']['category'],
            'messengers': lambda x: [y.get('messenger') for y in x['card']['messengers']],
            'messenger_values': lambda x: [y.get('name') for y in x['card']['messengers']],
        }
    },
    'Patreon': {
        'flags': ['www.patreon.com/api', 'pledge_url'],
        'regex': r'Object.assign\(window.patreon.bootstrap, ([\s\S]*)\);[\s\S]*Object.assign\(window.patreon.campaignFeatures, {}\);',
        'extract_json': True,
        'fields': {
            'patreon_id': lambda x: x['campaign']['included'][0]['id'],
            'patreon_username': lambda x: x['campaign']['included'][0]['attributes']['vanity'],
            'fullname': lambda x: x['campaign']['included'][0]['attributes']['full_name'],
            'links': lambda x: [y['attributes'].get('external_profile_url') for y in x['campaign']['included'] if
                                y['attributes'].get('app_name')],
        }
    },
    # TODO: add image
    'Telegram': {
        'flags': ['tg://resolve?domain='],
        'regex': r'"og:title" content="(?P<fullname>.+)">[\s\S]*"og:description" content="(?P<about>.+)">[\s\S]+?<img class="tgme_page_photo_image" src="(?P<image>.+)"',
    },
    'BuzzFeed': {
        'flags': ['window.BZFD = window.BZFD'],
        'regex': r'id="__NEXT_DATA__" type="application\/json">(.+?)<\/script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['props']['pageProps'],
            json.dumps,
        ],
        'fields': {
            'buzzfeed_id': lambda x: x['user_uuid'],
            'id': lambda x: x['user']['id'],
            'fullname': lambda x: x['user']['displayName'],
            'buzzfeed_username': lambda x: x['user']['username'],
            'bio': lambda x: x['user']['bio'],
            'posts': lambda x: x['buzz_count'],
            'memberSince': lambda x: timestamp_to_datetime(x['user']['memberSince']),
            'isCommunityUser': lambda x: x['user']['isCommunityUser'],
            'deleted': lambda x: x['user']['deleted'],
            # 'social_names': lambda x: [y.get('name') for y in x['user']['social']],
            'social_links': lambda x: [y.get('url') for y in x['user']['social']],
        }
    },
    'Linktree': {
        'flags': ['content="Linktree. Make your link do more."'],
        'regex': r'id="__NEXT_DATA__" type="application\/json" crossorigin="anonymous">(.+?)<\/script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['props']['pageProps'],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x.get('account', {}).get('id'),
            'username': lambda x: x.get('username'),
            'image': lambda x: x.get('profilePictureUrl'),
            'is_active': lambda x: x.get('account', {}).get('isActive'),
            'is_verified': lambda x: x.get('isProfileVerified'),
            'facebook_pixel_id': lambda x: x.get('account', {}).get('facebookPixelId'),
            'google_analytics_id': lambda x: x.get('account', {}).get('googleAnalyticsId'),
            'is_email_verified': lambda x: x.get('account', {}).get('owner', {}).get('isEmailVerified'),
            'bio': lambda x: x.get('description'),
            'tier': lambda x: x.get('account', {}).get('tier'),
            'links': lambda x: [y.get('url') for y in x.get('account', {}).get('links', [])] + x.get('socialLinks', []),
        }
    },
    'Twitch': {
        'flags': ['<meta property="al:android:url" content="twitch://'],
        'regex': r'id="__NEXT_DATA__" type="application\/json">(.+?)<\/script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['props']['relayQueryRecords'],
            lambda x: [v for k, v in x.items() if k.startswith('User') or k.endswith('followers')],
            lambda x: dict(list(x[0].items()) + list(x[1].items())),
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x.get('id').split('{')[-1],
            'views_count': lambda x: x.get('profileViewCount'),
            'username': lambda x: x.get('login'),
            'bio': lambda x: x.get('description'),
            'fullname': lambda x: x.get('displayName'),
            'image': lambda x: x.get('profileImageURL(width:300)'),
            'likes_count': lambda x: x.get('totalCount'),
            'image_bg': lambda x: x.get('bannerImageURL'),
        },
    },
    'vBulletinEngine': {
        'flags': ['vBulletin.register_control'],
        'bs': True,
        'fields': {
            'status': lambda x: x.find('span', {'class': 'online-status'}).findAll('span')[1].text,
            'country': lambda x: (x.find('span', {'class': 'sprite_flags'}) or {}).get('title'),
            'image': lambda x: x.find('span', {'class': 'avatarcontainer'}).find('img').get('src'),
        }
    },
    'Tumblr (default theme)': {
        'flags': ['https://assets.tumblr.com'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('h1', {'class': 'blog-title'}).find('a').text,
            'title': lambda x: x.find('div', {'class': 'title-group'}).find('span', {'class': 'description'}).text.strip(),
            'links': lambda x: [enrich_link(a.find('a').get('href')) for a in x.find('div', {'class': 'nav-wrapper'}).find_all('li', {'class': 'nav-item nav-item--page'})],
        }
    },
    '1x.com': {
        'flags': ['content="https://www.1x.com/'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('div', {'class': 'coveroverlay'}).find('td', {'valign': 'bottom'}).find('div').contents[0],
            'image': lambda x:  'https://1x.com/' + x.find('img', {'class': 'member_profilepic'}).get('src', ''),
        }
    },
    'Last.fm': {
        'flags': ['Music Profile | Last.fm</title>'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('span', {'class': 'header-title-display-name'}).contents[0].strip(),
            # TODO: date convert
            'bio': lambda x: x.find('span', {'class': 'header-scrobble-since'}).contents[0].strip(),
            'image': lambda x: x.find('span', {'class': 'avatar'}).find('img').get('src', ''),
        }
    },
    'Ask.fm': {
        'flags': [' | ASKfm</title>'],
        'bs': True,
        'fields': {
            'username': lambda x: x.find('span', {'class': 'userName_wrap'}).find('span', {'class': 'userName'}).contents[0].lstrip('@'),
            'fullname': lambda x: x.find('h1', {'class': 'userName_status'}).find('span', {'class': 'userName'}).contents[0].lstrip('@'),
            'posts_count': lambda x: x.find('div', {'class': 'profileStats_number profileTabAnswerCount'}).contents[0],
            'likes_count': lambda x: x.find('div', {'class': 'profileStats_number profileTabLikeCount'}).contents[0],
            'photo': lambda x: x.find('a', {'class': 'userAvatar-big'}).get('style').replace('background-image:url(','').rstrip(')'),
            'location': lambda x: x.find('div', {'class': 'icon-location'}).contents[0],
        }
    },
    'Launchpad': {
        'flags': ['in Launchpad</title>'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('h2', {'id': 'watermark-heading'}).find('a').contents[0],
            'username': lambda x: x.find('dl', {'id': 'launchpad-id'}).find('dd').contents[0],
            'languages': lambda x: x.find('dl', {'id': 'languages'}).find('dd').contents[0].strip(),
            'karma': lambda x: x.find('a', {'id': 'karma-total'}).contents[0],
            'created_at': lambda x: x.find('dd', {'id': 'member-since'}).contents[0],
            'timezone': lambda x: re.sub(r'\s+', ' ', x.find('dl', {'id': 'timezone'}).find('dd').contents[0] or '').strip(),
            'openpgp_key': lambda x: x.find('dl', {'id': 'pgp-keys'}).find('dd').contents[0].strip(),
        },
    },
}
