from dateutil.parser import parse as parse_datetime_str
import html
import json
import itertools

from .utils import *

schemes = {
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
        'flags': ['{"data":{"', 'user":{"id":'],
        'regex': r'^{"data":{"user":({.+})}}$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www.)?twitter.com/(?P<username>[^/]+).*',
                'to': 'https://twitter.com/i/api/graphql/ZRnOhhXPwue_JGILb9TNug/UserByScreenName?variables=%7B%22screen_name%22%3A%22{username}%22%2C%22withHighlightedLabel%22%3Atrue%7D',
            }
        ],
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
        'flags': ['<html id="facebook"', '<title>Facebook</title>'],
        'regex': r'({"__bbox":{"complete".+"sequence_number":0}})',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['result']['data']['user'],
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('url').split('/')[-1],
            'fullname': lambda x: x.get('name'),
            'is_verified': lambda x: x.get('is_verified'),
            'image': lambda x: x.get('profile_picture_for_sticky_bar', {}).get('uri', ''),
            'image_bg': lambda x: x.get('cover_photo', {}).get('photo', {}).get('image', {}).get('uri', ''),
        }
    },
    'Facebook group': {
        'flags': ['com.facebook.katana', 'XPagesProfileHomeController'],
        'regex': r'{"imp_id":".+?","ef_page":.+?,"uri":".+?\/(?P<username>[^\/]+?)","entity_id":"(?P<uid>\d+)"}',
    },
    'GitHub HTML': {
        'flags': ['github.githubassets.com'],
        'regex': r'data-hydro-click.+?profile_user_id&quot;:(?P<uid>\d+).+?originating_url&quot;:&quot;https:\/\/github\.com\/(?P<username>[^&]+)'
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
        'flags': ['avatar_url', 'https://gitlab.com'],
        'regex': r'^\[({[\S\s]+?})\]$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https://gitlab.com/(?P<username>.+)/?',
                'to': 'https://gitlab.com/api/v4/users?username={username}',
            }
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'fullname': lambda x: x.get('name'),
            'username': lambda x: x.get('username'),
            'state': lambda x: x.get('state'),
            'image': lambda x: x.get('avatar_url'),
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
            'image': lambda x: x['campaign']['data']['attributes']['avatar_photo_url'],
            'image_bg': lambda x: x['campaign']['data']['attributes']['cover_photo_url'],
            'is_nsfw': lambda x: x['campaign']['data']['attributes']['is_nsfw'],
            'created_at': lambda x: x['campaign']['data']['attributes']['published_at'],
            'bio': lambda x: x['campaign']['data']['attributes']['summary'],
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
            'created_at': lambda x: parse_datetime(x['photostream-models'][0]['owner'].get('dateCreated', 0)),
            'is_pro': lambda x: x['photostream-models'][0]['owner'].get('isPro'),
            'is_deleted': lambda x: x['photostream-models'][0]['owner'].get('isDeleted'),
            'is_ad_free': lambda x: x['photostream-models'][0]['owner'].get('isAdFree'),
        }
    },
    'Yandex Disk file': {
        'flags': ["project:'disk-public',page:'icon'", '@yandexdisk', 'yastatic.net'],
        'regex': r'"users":{.*?"uid":"(?P<yandex_uid>\d+)","displayName":"(?P<name>.+?)"',
    },
    'Yandex Disk photoalbum': {
        'flags': ["project:'disk-public',page:'album'"],
        'regex': r'"users":{.*?"uid":"(?P<yandex_uid>\d+)","displayName":"(?P<name>.+?)"',
    },
    'Yandex Music AJAX request': {
        'flags': ['{"success":true,"verified'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://music.yandex.ru/users/(?P<username>[^/]+).*',
                'to': 'https://music.yandex.ru/handlers/library.jsx?owner={username}',
                'headers': {"Referer": "https://music.yandex.ru/users/test/playlists"},
            }
        ],
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
    # TODO: rework
    'Yandex Market user profile': {
        'flags': ['MarketNode', '{"entity":"user"'],
        'regex': r'>{"widgets":{"@MarketNode/MyArticles/ArticlesGrid.+?"collections":({"publicUser":{"\d+".+?}}})}<',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: list(x['publicUser'].values())[0],
            json.dumps,
        ],
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
        'regex': r'({"routing":{"currentRoute".+?});',
        'extract_json': True,
        'fields': {
            'your_yuid': lambda x: x['user']['yuid'],
            'your_uid': lambda x: x['user']['uid'],
            'your_wallet_balance': lambda x: x['user']['walletInfo'].get('balance'),
            'your_emails': lambda x: ', '.join(x['user']['emails']),
            'your_name': lambda x: x['user'].get('displayName'),
            'your_username': lambda x: x['user'].get('defaultEmail'),
            'your_phone': lambda x: x['user'].get('defaultPhone'),
            'yandex_uid': lambda x: x['offerCard']['card']['author']['id'],
            'name': lambda x: decode_ya_str(x['offerCard']['card']['author']['profile']['name'])
        }
    },
    'Yandex Collections': {
        'flags': ['<meta name="collections"', '/collections'],
        'regex': r'(?:id="restoreData">)(.+?)<\/script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['entities']['users'].get(x['profileUser'].get('id'), {}),
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
        'flags': ['default_avatar_id', 'collections', 'is_passport'],
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
    'Yandex O': {
        'flags': ['<PLACEHOLDER>'],  # NOT PRESENT
        'regex': r'<script type="application/json" id="initial-state" nonce=".+?">(.+?)<\/script>',
        'extract_json': True,
        'fields': {
            'yandex_public_id': lambda x: x['publicProfile']['params']['publicUserId'],
            'fullname': lambda x: decode_ya_str(x['publicProfile']['data']['publicProfile']['seller']['name']),
            'image': lambda x: x['publicProfile']['data']['publicProfile']['seller']['avatar']['size_100x100'],
            'score': lambda x: x['publicProfile']['data']['publicProfile']['seller']['userBadge']['score'],
        }
    },
    'VK user profile foaf page': {
        'flags': ['<foaf:Person>', '<ya:publicAccess>'],
        'bs': True,
        'fields': {
            'is_private': lambda x: x.find('ya:publicaccess').contents[0] == 'allowed',
            'state': lambda x: x.find('ya:profilestate').contents[0],
            'first_name': lambda x: x.find('ya:firstname').contents[0],
            'last_name': lambda x: x.find('ya:secondname').contents[0],
            'fullname': lambda x: x.find('foaf:name').contents[0],
            'gender': lambda x: x.find('foaf:gender').contents[0],
            'created_at': lambda x: parse_datetime_str(x.find('ya:created').get('dc:date')),
            'updated_at': lambda x: parse_datetime_str(x.find('ya:modified').get('dc:date')),
            # 'following_count': lambda x: x.find('ya:subscribedToCount'),
            # 'follower_count': lambda x: x.find('ya:friendsCount'),
            # 'friends_count': lambda x: x.find('ya:subscribersCount'),
            # 'image': lambda x: x.find('foaf:Image'),
            'website': lambda x: x.find('foaf:homepage').contents[0],
            # 'links': lambda x: x.find('foaf:externalProfile'),
        },
    },
    'VK user profile': {
        'flags': ['<span class="ui_tab_content_new">', '"ownerId":'],
        'url_mutations': [
            {
                'from': r'https?://.*?vk.com/id(?P<vk_id>\d+)',
                'to': 'https://vk.com/foaf.php?id={vk_id}',
            }
        ],
        'regex': r'"ownerId":(?P<vk_id>\d+),"wall".*?"loc":"(?P<vk_username>.*?)","back":"(?P<fullname>.*?)"'
    },
    'VK closed user profile': {
        'flags': ['error_msg":"This profile is private', 'first_name_nom', 'last_name_gen'],
        'regex': r'<title>(?P<fullname>.*?)<\/title>'
    },
    'VK blocked user profile': {
        'flags': ['window.vk = {', 'User was deleted or banned'],
        'regex': r'<title>(?P<fullname>.*?)<\/title>'
    },
    'Gravatar': {
        'flags': ['gravatar.com\\/avatar', 'thumbnailUrl'],
        'url_mutations': [
            {
                'from': r'https?://.*?gravatar.com/(?P<username>[^/]+)',
                'to': 'https://en.gravatar.com/{username}.json',
            }
        ],
        'regex': r'^(.+?)$',
        'extract_json': True,
        'fields': {
            'gravatar_id': lambda x: x['entry'][0]['id'],
            'image': lambda x: x['entry'][0]['thumbnailUrl'],
            'username': lambda x: x['entry'][0]['preferredUsername'],
            'fullname': lambda x: x['entry'][0].get('name', {}).get('formatted'),
            'name': lambda x: x['entry'][0]['displayName'],
            'location': lambda x: x['entry'][0].get('currentLocation'),
            'emails': lambda x: [y['value'] for y in x['entry'][0].get('emails', [])],
            'links': lambda x: [y['url'] for y in x['entry'][0].get('accounts', [])] + [y['value'] for y in
                                                                                        x['entry'][0].get('urls', [])],
            'bio': lambda x: x['entry'][0].get('aboutMe'),
        }
    },
    'Instagram': {
        'flags': ['instagram://user?username'],
        'regex': r'<script type="application/json" .*?>(.*?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'],
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('full_name'),
            'id': lambda x: x.get('id'),
            'image': lambda x: x.get('profile_pic_url_hd'),
            'bio': lambda x: x.get('biography'),
            'business_email': lambda x: x.get('business_email'),
            'external_url': lambda x: x.get('external_url'),
            'facebook_uid': lambda x: x.get('fbid'),
            'is_business': lambda x: x.get('is_business_account'),
            'is_joined_recently': lambda x: x.get('is_joined_recently'),
            'is_private': lambda x: x.get('is_private'),
            'is_verified': lambda x: x.get('is_verified'),
            'follower_count': lambda x: x.get('edge_followed_by', {}).get('count'),
            'following_count': lambda x: x.get('edge_follow', {}).get('count'),
        }
    },
    'Instagram API': {
        'flags': ['{"user":{"pk"', 'profile_pic_url'],
        'regex': r'^(.+?)$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x['user'].get('username'),
            'id': lambda x: x['user'].get('pk'),
            'image': lambda x: x['user'].get('profile_pic_url'),
        }
    },
    'Instagram page JSON': {
        'flags': ['"logging_page_id":"profilePage', 'profile_pic_url'],
        'regex': r'^(.+?)$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['graphql']['user'],
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('full_name'),
            'id': lambda x: x.get('id'),
            'image': lambda x: x.get('profile_pic_url_hd'),
            'bio': lambda x: x.get('biography'),
            'business_email': lambda x: x.get('business_email'),
            'external_url': lambda x: x.get('external_url'),
            'facebook_uid': lambda x: x.get('fbid'),
            'is_business': lambda x: x.get('is_business_account'),
            'is_joined_recently': lambda x: x.get('is_joined_recently'),
            'is_private': lambda x: x.get('is_private'),
            'is_verified': lambda x: x.get('is_verified'),
            'follower_count': lambda x: x.get('edge_followed_by', {}).get('count'),
            'following_count': lambda x: x.get('edge_follow', {}).get('count'),
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
            'friends_count': lambda x: x['totalFriends'],
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
            lambda x: [v for k, v in x.items() if k.startswith('User:')][0],
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
            'follower_count': lambda x: x.get('socialStats', {}).get('followerCount'),
            'following_count': lambda x: x.get('socialStats', {}).get('followingCount'),
        }
    },
    'Odnoklassniki': {
        'flags': ['OK.startupData'],
        'regex': r'path:"/(profile/)?(?P<ok_user_name_id>.+?)",state:".+?friendId=(?P<ok_id>\d+?)"',
    },
    'Habrahabr HTML (old)': {
        'flags': ['habracdn.net'],
        'bs': True,
        'fields': {
            'uid': lambda x: x.find('div', {'class': 'user-info__stats'}).parent.attrs['class'][-1].split('_')[-1],
            'username': lambda x: x.find('a', {'class': 'media-obj__image'}).get('href').split('/')[-2],
            'image': lambda x: 'http:' + x.find('div', {'class': 'user-info__stats'}).find('img').get('src'),
        },
    },
    'Habrahabr JSON': {
        'flags': ['habrastorage.org'],
        'regex': r'({"authorRefs":{.+?}),"viewport',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: list(x['authorRefs'].values())[0],
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x['alias'],
            'about': lambda x: x['speciality'],
            'birthday': lambda x: x['birthday'],
            'gender': lambda x: x['gender'],
            'rating': lambda x: x['rating'],
            'karma': lambda x: x['scoreStats']['score'],
            'fullname': lambda x: x['fullname'],
            'is_readonly': lambda x: x['isReadonly'],
            'location': lambda x: x['location'],
            'image': lambda x: x['avatarUrl'],
            'follower_count': lambda x: x.get('legacy', {}).get('followStats', {}).get('followStats'),
            'following_count': lambda x: x.get('legacy', {}).get('followStats', {}).get('followersCount'),
        }
    },
    'My Mail.ru': {
        'flags': ['my.mail.ru', 'models/user/journal">'],
        'regex': r'journal">\s+({\s+"name":[\s\S]+?})',
        'extract_json': True,
        'fields': {
            'mail_uid': lambda x: get_mymail_uid(x.get('dir').split('/')[-2] if x else ''),
            'mail_id': lambda x: x.get('id'),
            'username': lambda x: x.get('dir').split('/')[-2] if x else '',
            'au_id': lambda x: x.get('auId'),
            'email': lambda x: x.get('email'),
            'name': lambda x: x.get('name'),
            'is_vip': lambda x: x.get('isVip'),
            'is_community': lambda x: x.get('isCommunity'),
            'is_video_channel': lambda x: x.get('isVideoChannel'),
            'image': lambda x: 'https://filin.mail.ru/pic?email=' + x.get('email'),
        }
    },
    'Behance': {
        'flags': ['behance.net', 'beconfig-store_state'],
        'regex': r'<script type="application/json" id="beconfig-store_state">({.+?})</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['profile']['owner'],
            json.dumps,
        ],
        'url_mutations': [
            {
                'from': r'https?://(www.)?behance.net/(?P<username>[^/]+).*',
                'to': 'https://www.behance.net/{username}/appreciated',
                'headers': {'Cookie': 'ilo0=true'},
            }
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'fullname': lambda x: x.get('display_name'),
            'last_name': lambda x: x.get('last_name'),
            'first_name': lambda x: x.get('first_name'),
            'website': lambda x: x.get('website'),
            'username': lambda x: x.get('username'),
            'is_verified': lambda x: x.get('verified') == 1,
            'teams': lambda x: x.get('teams'),
            'bio': lambda x: x.get('about')[0]['value'],
            'image': lambda x: x.get('images', {}).get('276'),
            'image_bg': lambda x: x.get('banner_image_url'),
            'company': lambda x: x.get('company'),
            'city': lambda x: x.get('city'),
            'country': lambda x: x.get('country'),
            'location': lambda x: x.get('location'),
            'created_at': lambda x: parse_datetime(x.get('created_on')),
            'occupation': lambda x: x.get('occupation'),
            'links': lambda x: [a['url'] for a in x.get('social_links')],
            'twitter_username': lambda x: x.get('twitter', '').lstrip('@'),
            'comments': lambda x: x['stats']['comments'],
            'followers_count': lambda x: x['stats']['followers'],
            'following_count': lambda x: x['stats']['following'],
            'profile_views': lambda x: x['stats']['received_profile_views'],
            'project_views': lambda x: x['stats']['views'],
            'appreciations': lambda x: x['stats']['appreciations'],
        }
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
        'url_mutations': [
            {
                'from': r'https://500px.com/p/(?P<username>.+)/?',
                'to': 'https://api.500px.com/graphql?operationName=ProfileRendererQuery&variables=%7B%22username%22%3A%22{username}%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22105058632482dd2786fd5775745908dc928f537b28e28356b076522757d65c19%22%7D%7D',
            }
        ],
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
    'Google Document API': {
        'flags': ['alternateLink', 'copyRequiresWriterPermission'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'url_mutations': [
            {
                # credits: https://github.com/Malfrats/xeuledoc
                'from': r'https://(docs|drive).google.com/(spreadsheets|document|presentation|drawings|file)/d/(?P<gdoc_id>[\w-]+)',
                'to': 'https://clients6.google.com/drive/v2beta/files/{gdoc_id}?fields=alternateLink%2CcopyRequiresWriterPermission%2CcreatedDate%2Cdescription%2CdriveId%2CfileSize%2CiconLink%2Cid%2Clabels(starred%2C%20trashed)%2ClastViewedByMeDate%2CmodifiedDate%2Cshared%2CteamDriveId%2CuserPermission(id%2Cname%2CemailAddress%2Cdomain%2Crole%2CadditionalRoles%2CphotoLink%2Ctype%2CwithLink)%2Cpermissions(id%2Cname%2CemailAddress%2Cdomain%2Crole%2CadditionalRoles%2CphotoLink%2Ctype%2CwithLink)%2Cparents(id)%2Ccapabilities(canMoveItemWithinDrive%2CcanMoveItemOutOfDrive%2CcanMoveItemOutOfTeamDrive%2CcanAddChildren%2CcanEdit%2CcanDownload%2CcanComment%2CcanMoveChildrenWithinDrive%2CcanRename%2CcanRemoveChildren%2CcanMoveItemIntoTeamDrive)%2Ckind&supportsTeamDrives=true&enforceSingleParent=true&key=AIzaSyC1eQ1xj69IdTMeii5r7brs3R90eck-m7k',
                'headers': {"X-Origin": "https://drive.google.com"},
            }
        ],
        'fields': {
            'created_at': lambda x: x.get('createdDate'),
            'updated_at': lambda x: x.get('modifiedDate'),
            'fake_gaia_id': lambda x: x.get('permissions')[1]['id'],
            'fullname': lambda x: x.get('permissions')[1]['name'],
            'email': lambda x: x.get('permissions')[1]['emailAddress'],
            'image': lambda x: x.get('permissions')[1]['photoLink'],
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
            'viewer_uid': lambda x: x['docs-pid'],
            'org_name': lambda x: x['docs-doddn'],
            'org_domain': lambda x: x['docs-dodn'],
            'mime_type': lambda x: x.get('docs-dm'),
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
        'regex': r'({.+?"section": {"profile.+?"repositories":.+?}});',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['global']['targetUser'],
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x['uuid'].strip('{}'),
            'id': lambda x: x['account_id'],
            'fullname': lambda x: x['display_name'],
            'nickname': lambda x: x['nickname'],
            'location': lambda x: x['location'],
            'image': lambda x: x['links']['avatar']['href'],
            'occupation': lambda x: x['job_title'],
            'created_at': lambda x: x['created_on'],
            'is_service': lambda x: x['is_staff'],
            'is_active': lambda x: x['is_active'],
            'has_2fa_enabled': lambda x: x['has_2fa_enabled'],
        }
    },
    'Pinterest API': {
        'flags': ['{"resource_response":{', 'video_pin_count'],
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
        'flags': ['https://www.redditstatic.com/'],
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
            'created_at': lambda x: parse_datetime(x['createdUtc']),
            'total_karma': lambda x: x['karma']['total'],
            'post_karma': lambda x: x['karma']['fromPosts'],
            'comments_karma': lambda x: x['karma']['fromComments'],
            'awards_given_karma': lambda x: x['karma']['fromAwardsGiven'],
            'awards_got_karma': lambda x: x['karma']['fromAwardsReceived'],
        },
    },
    'Steam': {
        'flags': ['store.steampowered.com', 'profile_header_bg_texture'],
        'regex': r'({"url":".+?});',
        'extract_json': True,
        'fields': {
            'steam_id': lambda x: x['steamid'],
            'nickname': lambda x: x['personaname'],
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
        'bs': True,
        'fields': {
            'uid': lambda x: x.find('div', {'class': 'avatar'}).find('a').get('href').split('/')[-2],
            'image': lambda x: x.find('div', {'class': 'avatar'}).find('img').get('src'),
            'stack_exchange_uid': lambda x:
            x.find('div', {'id': 'mainbar-full'}).find('a', {'class': 'grid--cell'}).get('href').split('/')[-2],
        }
    },
    'SoundCloud': {
        'flags': ['eventlogger.soundcloud.com'],
        'regex': r'{"hydratable":"user","data":({.+?)}];',
        'extract_json': True,
        'message': 'Run with auth cookies to get your ids.',
        'transforms': [
            json.loads,
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x['id'],
            'name': lambda x: x['full_name'],
            'username': lambda x: x['username'].lstrip('@'),
            'following_count': lambda x: x['followings_count'],
            'follower_count': lambda x: x['followers_count'],
            'is_verified': lambda x: x['verified'],
            'image': lambda x: x['avatar_url'],
            'location': lambda x: x['city'],
            'country_code': lambda x: x['country_code'],
            'bio': lambda x: x['description'],
            'created_at': lambda x: x['created_at'],
        }
    },
    'TikTok': {
        'flags': ['tiktokcdn.com', 'SIGI_STATE'],
        'regex': r'<script id="SIGI_STATE"[^>]+>(.+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: {**x['UserModule']['users'].get(x['UserPage']['uniqueId'], {}),
                       **x['UserModule']['stats'].get(x['UserPage']['uniqueId'], {})},
            json.dumps,
        ],
        'fields': {
            'tiktok_id': lambda x: x['id'],
            'tiktok_username': lambda x: x['uniqueId'],
            'fullname': lambda x: x['nickname'],
            'bio': lambda x: x['signature'],
            'image': lambda x: x['avatarMedium'],
            'is_verified': lambda x: x['verified'],
            'is_secret': lambda x: x['secret'],
            'sec_uid': lambda x: x['secUid'],
            'following_count': lambda x: x['followingCount'],
            'follower_count': lambda x: x['followerCount'],
            'heart_count': lambda x: x['heartCount'],
            'video_count': lambda x: x['videoCount'],
            'digg_count': lambda x: x['diggCount'],
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
        'regex': r'Site.journal = ({.+?});',
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
        'regex': r'({\\"username\\":\\".+?\",\\"country.+?legacyTextEditUrl.+?})',
        'extract_json': True,
        'transforms': [
            lambda x: x.replace('\\"', '"'),
            lambda x: x.replace('\\\\"', '\''),
            lambda x: x.replace('\\\\u002F', '/'),
            lambda x: x.replace("\\'", "'")
        ],
        'fields': {
            'country': lambda x: x['country'],
            'created_at': lambda x: parse_datetime(x['deviantFor']),
            'gender': lambda x: x['gender'],
            'username': lambda x: x['username'],
            'twitter_username': lambda x: x['twitterUsername'],
            'website': lambda x: x['website'],
            'links': lambda x: [y['value'] for y in x['socialLinks']],
            'tagline': lambda x: x['tagline'],
            'image': lambda x: x['devidDeviation']['author']['usericon'],
            'bio': lambda x: x['textContent']['excerpt'],
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
    'Telegram': {
        'flags': ['tgme_page_title'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('div', {'class': 'tgme_page_title'}).find('span').text,
            'image': lambda x: x.find('img', {'class': 'tgme_page_photo_image'}).get('src'),
            'bio': lambda x: x.find('div', {'class': 'tgme_page_description'}).get_text(separator='\n'),
        }
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
            'uuid': lambda x: x['user_uuid'],
            'id': lambda x: x['user']['id'],
            'fullname': lambda x: x['user']['displayName'],
            'username': lambda x: x['user']['username'],
            'bio': lambda x: x['user']['bio'],
            'posts_count': lambda x: x['buzz_count'],
            'created_at': lambda x: parse_datetime(x['user']['memberSince']),
            'is_community_user': lambda x: x['user']['isCommunityUser'],
            'is_deleted': lambda x: x['user']['deleted'],
            'social_links': lambda x: [y.get('url') for y in x['user']['social']],
            'image': lambda x: 'https://img.buzzfeed.com/buzzfeed-static' + x['user']['image'],
            'image_bg': lambda x: 'https://img.buzzfeed.com/buzzfeed-static' + x['user']['headerImage'],
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
            'social_links': lambda x: {(s['type'].lower() if not s['type'].startswith('EMAIL') else 'email'): s['url']
                                       for s in x.get('socialLinks', [])},
            'links': lambda x: [y.get('url') for y in x.get('account', {}).get('links', [])],
        }
    },
    'Twitch': {
        'flags': ['crossorigin="anonymous" href="https://gql.twitch.tv/gql"'],
        'regex': r'id="__NEXT_DATA__" type="application\/json">(.+?)<\/script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['props']['relayQueryRecords'],
            lambda x: [v for k, v in x.items() if k.startswith('User') or k.endswith('followers')],
            lambda x: dict(list(x[-1].items()) + list(x[0].items())),
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x.get('id').split('{')[-1],
            # 'views_count': lambda x: x.get('profileViewCount'),
            'username': lambda x: x.get('login'),
            'bio': lambda x: x.get('description'),
            'fullname': lambda x: x.get('displayName'),
            'image': lambda x: x.get('profileImageURL(width:150)'),
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
            'title': lambda x: x.find('div', {'class': 'title-group'}).find('span',
                                                                            {'class': 'description'}).text.strip(),
            'image': lambda x: x.find('a', {'class': 'user-avatar'}).find('img').get('src'),
            'image_bg': lambda x: x.find('a', {'class': 'header-image'}).get('data-bg-image'),
            'links': lambda x: [enrich_link(a.find('a').get('href')) for a in
                                x.find('div', {'class': 'nav-wrapper'}).find_all('li',
                                                                                 {'class': 'nav-item nav-item--page'})],
        }
    },
    '1x.com': {
        'flags': ['content="https://www.1x.com/'],
        'bs': True,
        'fields': {
            'fullname': lambda x:
            x.find('div', {'class': 'coveroverlay'}).find('td', {'valign': 'bottom'}).find('div').contents[0],
            'image': lambda x: 'https://1x.com/' + x.find('img', {'class': 'member_profilepic'}).get('src', ''),
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
            'username': lambda x: x.find('form', {'id': 'profileAnswersForm'}).get('action', '').split('/')[-2],
            'fullname': lambda x: x.find('span', {'class': 'userName'}).contents[0],
            'posts_count': lambda x: x.find('div', {'class': 'profileTabAnswerCount'}).contents[0],
            'likes_count': lambda x: x.find('div', {'class': 'profileTabLikeCount'}).contents[0],
            'image': lambda x:
            x.find('a', {'class': 'userAvatar-big'}).get('style').replace('background-image:url(', '').rstrip(
                ')').split(';')[1],
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
            'timezone': lambda x: re.sub(r'\s+', ' ',
                                         x.find('dl', {'id': 'timezone'}).find('dd').contents[0] or '').strip(),
            'openpgp_key': lambda x: x.find('dl', {'id': 'pgp-keys'}).find('dd').find('span').text.strip()
        }
    },
    'Xakep.ru': {
        'flags': ['https://xakep.ru/author/'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('div', {'class': 'authorBlock-header'}).find('h4').contents[0],
            'image': lambda x: x.find('div', {'class': 'authorBlock-avatar'}).find('img').get('src', ''),
            'bio': lambda x: '\n'.join(x.find('p', {'class': 'authorBlock-header-bio'}).contents),
            'links': lambda x: [a.get('href') for a in x.find('div', {'class': 'authorBlock-meta'}).findAll('a')],
            'joined_year': lambda x: extract_digits(
                x.find('div', {'class': 'authorBlock-header'}).find('h6').contents[0]),
        }
    },
    'Tproger.ru': {
        'flags': ['<meta property="og:url" content="https://tproger.ru/author/'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('h1', {'class': 'author-main__header'}).contents[0],
            'image': lambda x: x.find('div', {'class': 'author-main'}).find('img').get('data-src', ''),
        }
    },
    'Jsfiddle.net': {
        'flags': ['<meta name="author" edit="JSFiddle">'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('div', {'class': 'profileDetails'}).find('a').contents[0].strip(),
            'company': lambda x: x.find('div', {'class': 'profileDetails'}).find('div', {'class': 'company'}).contents[
                0].strip(),
            'links': lambda x: [a.get('href') for a in x.find('div', {'class': 'userDetails'}).findAll('a')],
            'image': lambda x: x.find('div', {'class': 'avatar'}).find('img').get('src', ''),
        }
    },
    'Disqus API': {
        'flags': ['https://disqus.com/api/users/'],
        'regex': r'^([\s\S]+)$',
        'url_mutations': [
            {
                'from': r'https?://disqus.com/by/(?P<username>[^/]+)/?',
                'to': 'https://disqus.com/api/3.0/users/details?user=username:{username}&attach=userFlaggedUser&api_key=E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F',
            }
        ],
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['response'],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x['id'],
            'fullname': lambda x: x['name'],
            'disqus_username': lambda x: x['username'],
            'bio': lambda x: x['about'],
            'reputation': lambda x: x['reputation'],
            'reputation_label': lambda x: x['reputationLabel'],
            'following_count': lambda x: x['numFollowers'],
            'follower_count': lambda x: x['numFollowing'],
            'location': lambda x: x['location'],
            'is_power_contributor': lambda x: x['isPowerContributor'],
            'is_anonymous': lambda x: x['isAnonymous'],
            'created_at': lambda x: x['joinedAt'],
            'upvotes_count': lambda x: x['numLikesReceived'],
            'website': lambda x: x['url'],
            'forums_count': lambda x: x['numForumsFollowing'],
            'image': lambda x: x['avatar']['large']['permalink'],
            'is_trackers_disabled': lambda x: x['response'],
            'forums_following_count': lambda x: x['numForumsFollowing'],
            'is_private': lambda x: x['isPrivate'],
            'comments_count': lambda x: x['numPosts'],
        }
    },
    'uCoz-like profile page': {
        'flags': ['UCOZ-JS-DATA'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('div', string='Имя:').next_sibling.split('[')[0].strip(),
            'url': lambda x: get_ucoz_userlink(x.find('div', string='Пользователь:')),
            'image': lambda x: get_ucoz_image(x),
            'gender': lambda x: x.find('div', string='Имя:').next_sibling.split(' ')[-2],
            'created_at': lambda x: x.find('div', string='Дата регистрации:').next_sibling.strip(),
            'last_seen_at': lambda x: x.find('div', string='Дата входа:').next_sibling.strip(),
            'link': lambda x: get_ucoz_uid_node(x).parent.get('href'),
            'uidme_uguid': lambda x: get_ucoz_uid_node(x).parent.get('href', '').split('/')[-1],
            'location': lambda x: x.find('div', string='Место проживания:').next_sibling.strip(),
            'country': lambda x: x.find('div', string='Страна:').next_sibling.strip(),
            'city': lambda x: x.find('div', string='Город:').next_sibling.strip(),
            'state': lambda x: x.find('div', string='Штат:').next_sibling.strip(),
            'email': lambda x: get_ucoz_email(x.find('div', string='E-mail:').next_sibling.strip()),
            'birthday_at': lambda x: x.find('div', string='Дата рождения:').next_sibling.split('[')[0].strip(),
        },
    },
    'uID.me': {
        'flags': [' - uID.me</title>'],
        'bs': True,
        'fields': {
            'username': lambda x: x.find('title').contents[0].split(' ')[0],
            'image': lambda x: 'https://uid.me' + x.find('img', {'id': 'profile_picture'}).get('src'),
            'headline': lambda x: x.find('h2', {'id': 'profile_headline'}).contents[0].strip(),
            'bio': lambda x: x.find('div', {'id': 'profile_bio'}).contents[0].strip(),
            'contacts': lambda x: [a.contents[0] for a in x.find('div', {'id': 'profile_contacts'}).find_all('a')],
            'email': lambda x: x.find('a', {'id': 'user-email'}).contents[0],
            'phone': lambda x: x.find('span', {'id': 'profile-phone'}).contents[0],
            'skype': lambda x: x.find('span', {'id': 'profile-skype'}).contents[0],
            'location': lambda x: ','.join(
                [a.contents[0] for a in x.find('ul', {'id': 'profile_places'}).find_all('a')]),
            'links': lambda x: [a.get('href') for a in x.find('div', {'id': 'list_my-sites'}).find_all('a')] or None,
        },
    },
    'tapd': {
        'flags': ['{"_id"', 'userDetails":{"', '"sid":"'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://tapd.co/(?P<username>[^/]+).*',
                'to': 'https://tapd.co/api/user/getPublicProfile/{username}',
            }
        ],
        'fields': {
            'fullname': lambda x: x['name'],
            'username': lambda x: x['userDetails']['username'],
            'bio': lambda x: x['bio'],
            'views_count': lambda x: x['count'],
            'image': lambda x: 'https://distro.tapd.co/' + x['header']['picture'],
            'links': lambda x: [l['url'].strip() for l in x['links']],
        }
    },
    'freelancer.com': {
        'flags': ['{"status":"success","result":{"users":{'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www.)?freelancer\.com/u/(?P<username>[^/]+).*',
                'to': 'https://www.freelancer.com/api/users/0.1/users?usernames%5B%5D={username}&compact=true',
            }
        ],
        'transforms': [
            json.loads,
            lambda x: list(x['result']['users'].values())[0],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x['id'],
            'nickname': lambda x: x['display_name'],
            'username': lambda x: x['username'],
            'fullname': lambda x: x['public_name'],
            'company': lambda x: x['company'],
            'company_founder_id': lambda x: x['corporate']['founder_id'],
            'role': lambda x: x['role'],
            'location': lambda x: x['location']['city'] + ', ' + x['location']['country']['name'],
            'created_at': lambda x: parse_datetime(x['registration_date']),
        }
    },
    'Yelp': {
        'flags': ['yelp.www.init.user_details'],
        'bs': True,
        'fields': {
            # Lambda function to extract Yelp user ID from the meta tag with property 'og:url'
            'yelp_userid': lambda x: x.find('meta', {'property': 'og:url'}).get('content').split('=')[-1],

            # Lambda function to extract the user's full name from a span with itemprop 'name'
            'fullname': lambda x: x.find('h2', {'class': 'css-rlqqlq'}).text,

            # Lambda function to extract the user's location from a span with itemprop 'address'
            'location': lambda x: x.find('p', {'class': 'css-147vps'}).text,

            # Lambda function to extract the user's image URL from an img tag with itemprop 'image'
            'image': lambda x: x.find('img', {'class': 'css-1pz4y59'}).get('src'),

        }
    },
    'Trello API': {
        'flags': ['"aaId"', '"trophies":'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'fields': {
            'id': lambda x: x['id'],
            'username': lambda x: x['username'],
            'fullname': lambda x: x['fullName'],
            'email': lambda x: x['email'],
            'image': lambda x: x['avatarUrl'] + '/170.png',
            'bio': lambda x: x['bio'],
            'type': lambda x: x['memberType'],
            'gravatar_email_md5_hash': lambda x: x['gravatarHash'],
            'is_verified': lambda x: x['confirmed'],
        }
    },
    # TODO
    'Weibo': {
        'flags': ['$CONFIG = {"showAriaEntrance'],
        'regex': r'aria-label',
        'transforms': [
            lambda x: re.split('[\r\n]', x),
            lambda x: [r.split("'") for r in x if r],
            lambda x: {r[1]: r[-2] for r in x},
        ],
        'fields': {
            'weibo_id': lambda x: x['oid'],
            'fullname': lambda x: x['onick'],
            'nickname': lambda x: x['nick'],
            'image': lambda x: x['avatar_large'],
            'gender': lambda x: x['sex'],
            'language': lambda x: x['lang'],
        }
    },
    'ICQ': {
        'flags': ['a href="//icq.com/app" class="icq-prompt__banner-link"'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('h2', {'class': 'icq-profile__name'}).contents[0],
            'username': lambda x: x.find('p', {'class': 'icq-profile__subtitle'}).contents[0].strip('\n\t@'),
            'bio': lambda x: x.find('p', {'class': 'icq-profile__description box'}).contents[0].strip('\n\t'),
            'image': lambda x: x.find('meta', {'itemprop': 'image'}).get("content"),
        }
    },
    'Pastebin': {
        'flags': ['src="/themes/pastebin/js/'],
        'bs': True,
        'fields': {
            'image': lambda x: 'https://pastebin.com' + x.find('div', {'class': 'user-icon'}).find('img').get('src'),
            'website': lambda x: x.find('a', {'class': 'web'}).get('href'),
            'location': lambda x: x.find('span', {'class': 'location'}).contents[0],
            'views_count': lambda x: x.find('span', {'class': 'views'}).contents[0].replace(',', ''),
            'all_views_count': lambda x: x.find('span', {'class': 'views -all'}).contents[0].replace(',', ''),
            'created_at': lambda x: x.find('span', {'class': 'date-text'}).get("title"),
        }
    },
    'Periscope': {
        'flags': ['canonicalPeriscopeUrl', 'pscp://user/', 'property="og:site_name" content="Periscope"/>'],
        'regex': r'data-store="(.*)"><div id="PageView"',
        'extract_json': True,
        'transforms': [
            lambda x: x.replace('&quot;', '"'),
            json.loads,
            lambda x: list(x['UserCache']['users'].values())[0]['user'],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x['id'],
            'created_at': lambda x: x['created_at'],
            'periscope_username': lambda x: x['username'],
            'fullname': lambda x: x['display_name'],
            'bio': lambda x: x['description'],
            'follower_count': lambda x: x['n_followers'],
            'following_count': lambda x: x['n_following'],
            'hearts_count': lambda x: x['n_hearts'],
            'is_beta_user': lambda x: x['is_beta_user'],
            'is_employee': lambda x: x['is_employee'],
            'isVerified': lambda x: x['isVerified'],
            'is_twitter_verified': lambda x: x['is_twitter_verified'],
            'twitterUserId': lambda x: x.get('twitterUserId'),
            'twitter_screen_name': lambda x: x.get('twitter_screen_name'),
            'image': lambda x: x['profile_image_urls'][0]['url'],
        }
    },
    'Imgur API': {
        'flags': ['"reputation_count"', '"reputation_name"'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://imgur.com/user/(?P<username>[^/]+)',
                'to': 'https://api.imgur.com/account/v1/accounts/{username}?client_id=546c25a59c58ad7',
            }
        ],
        'fields': {
            'id': lambda x: x['id'],
            'imgur_username': lambda x: x['username'],
            'bio': lambda x: x['bio'],
            'reputation_count': lambda x: x['reputation_count'],
            'reputation_name': lambda x: x['reputation_name'],
            'image': lambda x: x['avatar_url'],
            'created_at': lambda x: x['created_at'],
        }
    },
    'PayPal': {
        'flags': ["indexOf('qa.paypal.com')", 'PayPalSansSmall-Regular'],
        'regex': r'application/json" id="client-data">(.*)</script><script type="application/json" id="l10n-content">',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['recipientSlugDetails']['slugDetails'],
            json.dumps,
        ],
        'fields': {
            'fullname': lambda x: x['userInfo']['displayName'],
            'alternative_fullname': lambda x: x['userInfo'].get('alternateFullName'),
            'username': lambda x: x['paypalmeSlugName'],
            'payerId': lambda x: x['payerId'],
            'address': lambda x: x['userInfo']['displayAddress'],
            'isProfileStatusActive': lambda x: x['isProfileStatusActive'],
            'primaryCurrencyCode': lambda x: x['userInfo']['primaryCurrencyCode'],
            'image': lambda x: x['userInfo']['profilePhotoUrl'],
        }
    },
    'Tinder': {
        'flags': ['<html id="Tinder"', 'content="tinder:'],
        'regex': r'window.__data=(.*);</script><script>window.__intlData=JSON.parse',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['webProfile'],
            json.dumps,
        ],
        'fields': {
            'tinder_username': lambda x: x['username'],
            'birth_date': lambda x: x['user']['birth_date'],
            'id': lambda x: x['user']['_id'],
            'badges_list': lambda x: [badge['type'] for badge in x['user']['badges']],
            'company': lambda x: x['user'].get('jobs')[0]['company']['name'],
            'position_held': lambda x: x['user'].get('jobs')[0]['title']['name'],
            'fullname': lambda x: x['user']['name'],
            'image': lambda x: x['user']['photos'][0]['url'],
            'images': lambda x: [photo['url'] for photo in x['user']['photos']],
            'education': lambda x: [school['name'] for school in x['user']['schools']],

        }
    },
    'ifunny.co': {
        'flags': ["gtag('config', 'G-5FQ9GH4QMZ');"],
        'regex': r'window.__INITIAL_STATE__=(.+?);',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['user']['data'],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x['id'],
            'username': lambda x: x['nick'],
            'bio': lambda x: x['about'],
            'image': lambda x: x['avatar']['url'],
            'follower_count': lambda x: x['num']['subscriptions'],
            'following_count': lambda x: x['num']['subscribers'],
            'post_count': lambda x: x['num']['total_posts'],
            'created_count': lambda x: x['num']['created'],
            'featured_count': lambda x: x['num']['featured'],
            'smile_count': lambda x: x['num']['total_smiles'],
            'achievement_count': lambda x: x['num']['achievements'],
            'is_verified': lambda x: x['isVerified'],
        }
    },
    'Wattpad API': {
        'flags': ['{"username":"'],
        'regex': r'^({"username":"(.+)})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www.|a.)?wattpad.com/user/(?P<username>[^/]+).*',
                'to': 'https://www.wattpad.com/api/v3/users/{username}',
            }
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'image': lambda x: x.get('avatar'),
            'image_bg': lambda x: x.get('backgroundUrl'),
            'fullname': lambda x: x.get('name'),
            'description': lambda x: x.get('description'),
            'status': lambda x: x.get('status'),
            'gender': lambda x: x.get('gender'),
            'locale': lambda x: x.get('locale'),
            'created_at': lambda x: x.get('createDate'),
            'updated_at': lambda x: x.get('modifyDate'),
            'location': lambda x: x.get('location'),
            'isPrivate': lambda x: x.get('isPrivate'),
            'verified': lambda x: x.get('verified'),
            'verified_email': lambda x: x.get('verified_email'),
            'ambassador': lambda x: x.get('ambassador'),
            'isMuted': lambda x: x.get('isMuted'),
            'allowCrawler': lambda x: x.get('allowCrawler'),
            'follower_count': lambda x: x.get('numFollowers'),
            'following_count': lambda x: x.get('numFollowing'),
            'facebook': lambda x: 'https://www.facebook.com/' + x.get('facebook') if x.get('facebook') else None,
            'twitter': lambda x: 'https://twitter.com/' + x.get('twitter') if x.get('twitter') else None,
            'website': lambda x: x.get('website'),
            'lulu': lambda x: x.get('lulu'),
            'smashwords': lambda x: x.get('smashwords'),
            'bubok': lambda x: x.get('bubok'),
        }
    },
    'Kik': {
        'flags': ['{"firstName":"'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://kik.me/(?P<username>[^/]+).*',
                'to': 'https://ws2.kik.com/user/{username}',
            }
        ],
        'fields': {
            'fullname': lambda x: x.get('firstName') + ' ' + x.get('lastName'),
            'image': lambda x: x.get('displayPic'),
            'update_pic_at': lambda x: parse_datetime(x.get('displayPicLastModified')),
        }
    },
    'Docker Hub API': {
        'flags': ['{"id":"', '"type":"User"}'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://hub.docker.com/u/(?P<username>[^/]+).*',
                'to': 'https://hub.docker.com/v2/users/{username}/',
            }
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'full_name': lambda x: x.get('full_name'),
            'location': lambda x: x.get('location'),
            'company': lambda x: x.get('company'),
            'created_at': lambda x: x.get('data_joined'),
            'type': lambda x: x.get('type'),
            'image': lambda x: x.get('gravatar_url'),
        }
    },
    'Mixcloud API': {
        'flags': ['"key": "'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www.)?mixcloud.com/(?P<username>[^/]+).*',
                'to': 'https://api.mixcloud.com/{username}/',
            }
        ],
        'fields': {
            'fullname': lambda x: x.get('fullname'),
            'username': lambda x: x.get('username'),
            'country': lambda x: x.get('country'),
            'city': lambda x: x.get('city'),
            'created_at': lambda x: x.get('created_time'),
            'updated_at': lambda x: x.get('updated_time'),
            'description': lambda x: x.get('blog'),
            'image': lambda x: x['pictures'].get('640wx640h'),
            'follower_count': lambda x: x.get('follower_count'),
            'following_count': lambda x: x.get('following_count'),
            'cloudcast_count': lambda x: x.get('cloudcast_count'),
            'favorite_count': lambda x: x.get('favorite_count'),
            'listen_count': lambda x: x.get('listen_count'),
            'is_pro': lambda x: x.get('is_pro'),
            'is_premium': lambda x: x.get('is_premium'),
        }
    },
    'binarysearch API': {
        'flags': [',"preferredSubmissionPrivacy":'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://binarysearch.com/@/(?P<username>[^/]+).*',
                'to': 'https://binarysearch.com/api/users/{username}/profile',
            }
        ],
        'fields': {
            'uid': lambda x: x['user'].get('id'),
            'username': lambda x: x['user'].get('username'),
            'image': lambda x: x['user'].get('profilePic'),
            'location': lambda x: x['user'].get('location'),
            'created_at': lambda x: parse_datetime(x['user'].get('createTime')),
            'updated_at': lambda x: parse_datetime(x['user'].get('updateTime')),
            'bio': lambda x: x['user'].get('bio'),
            'work': lambda x: x['user'].get('work'),
            'college': lambda x: x['user'].get('college'),
            'Role': lambda x: x['user'].get('preferredRole'),
            'github_url': lambda x: x['user'].get('githubHandle'),
            'twitter_url': lambda x: x['user'].get('twitterHandle'),
            'linkedin_url': lambda x: x['user'].get('linkedinHandle'),
            'links': lambda x: x['user'].get('personalWebsite'),
            'isAdmin': lambda x: x['user'].get('isAdmin'),
            'isVerified': lambda x: x['user'].get('isVerified'),
            'HistoryPublic': lambda x: x['user'].get('preferredHistoryPublic'),
            'RoomPublic': lambda x: x['user'].get('preferredRoomPublic'),
            'InviteOnly': lambda x: x['user'].get('preferredInviteOnly'),
        }
    },
    'pr0gramm API': {
        'flags': [',"likesArePublic":'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://pr0gramm.com/user/(?P<username>[^/]+).*',
                'to': 'https://pr0gramm.com/api/profile/info?name={username}',
            }
        ],
        'fields': {
            'uid': lambda x: x['user'].get('id'),
            'username': lambda x: x['user'].get('name'),
            'created_at': lambda x: parse_datetime(x['user'].get('registered')),
            'uploadCount': lambda x: x.get('uploadCount'),
            'commentCount': lambda x: x.get('commentCount'),
            'tagCount': lambda x: x.get('tagCount'),
            'likesArePublic': lambda x: x.get('likesArePublic'),
        }
    },
    'Aparat API': {
        'flags': ['ProfileMore', 'aparat.com'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www.)?aparat.com/(?P<username>[^/]+)$',
                'to': 'https://www.aparat.com/api/fa/v1/user/user/information/username/{username}',
            }
        ],
        'fields': {
            'uid': lambda x: x['data']['id'],
            'hashed_user_id': lambda x: x['data']['attributes']['hash_user_id'],
            'username': lambda x: x['data']['attributes']['username'],
            'fullname': lambda x: x['data']['attributes']['name'],
            'image': lambda x: x['data']['attributes']['pic_b'],
            'image_bg': lambda x: x['data']['attributes']['cover_src'],
            'follower_count': lambda x: x['data']['attributes']['follower_cnt'],  # not really a number
            'following_count': lambda x: x['data']['attributes']['follow_cnt'],  # not really a number
            'is_official': lambda x: x['data']['attributes']['official'],
            'is_banned': lambda x: x['data']['attributes']['banned'] != "no",
            'links': lambda x: [x['data']['attributes']['url']] + [i['link'] for i in
                                                                   x['included'][0]['attributes']['social']],
            'video_count': lambda x: x['data']['attributes']['video_cnt'],
            'bio': lambda x: x['data']['attributes']['description'],
            'created_at': lambda x: parse_datetime(x['data']['attributes']['start_date']),
        }
    },
    'UnstoppableDomains': {
        'flags': ['reservedForUserId', 'DomainProduct'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x['searchQuery'],
            'registered_domains': lambda x: [i["productCode"] for i in x["exact"] if i["status"] == "registered"],
            'protected_domains': lambda x: [i["productCode"] for i in x["exact"] if i["status"] == "protected"],
        }
    },
    'memory.lol': {
        'flags': ['{"accounts":[{'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'fields': {
            'id': lambda x: x['accounts'][0]['id'],
            'known_usernames': lambda x: [i for i in x['accounts'][0]['screen_names']],
        }
    }
}

