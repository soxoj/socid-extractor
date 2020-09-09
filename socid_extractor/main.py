import html
import json
import logging
import sys
import re
from http.cookies import SimpleCookie

import requests

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
            'links': lambda x: [link for links in x['profiles'] for link in links['addresses']],
        }
    },
    'Yandex Znatoki user profile': {
        'flags': ['Ya.Znatoki'],
        'regex': r'id="restoreData" type="application/json">({.+?})</script>',
        'extract_json': True,
        'transforms': [
            html.unescape,
            # TODO: refactoring
            lambda x: json.dumps(list(json.loads(x)['store']['entities']['user'].values())[0]),
        ],
        'fields': {
            'name': lambda x: x['displayName'],
            'uid': lambda x: x['id'],
            'yandex_uid': lambda x: x['uuid'],
        }
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
            'sex': lambda x: x.get('sex'),
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
        'flags': ['channel_subscriptions', 'subscriptions_on_self_boards'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'fields': {
            'yandex_public_id': lambda x: x.get('public_id'),
            'fullname': lambda x: x.get('display_name'),
            'image': lambda x: get_yandex_profile_pic(x.get('default_avatar_id')),
            'sex': lambda x: x.get('sex'),
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
    'VK user profile': {
        'flags': ['var vk =', 'change_current_info'],
        'regex': r'Profile\.init\({"user_id":(?P<vk_id>\d+).*?(,"loc":"(?P<vk_username>.*?)")?,"back":"(?P<fullname>.*?)"'
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
            'username': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('username'),
            'full_name': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('full_name'),
            'id': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('id'),
            'biography': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('biography'),
            'business_email': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('business_email'),
            'external_url': lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'].get('external_url'),
        }
    },
    'EyeEm': {
        'flags': ['https://www.eyeem.com/node-static/img'],
        'regex': r'__APOLLO_STATE__ = ({.+?});\n',
        'extract_json': True,
        'fields': {
            'eyeem_id': lambda x: list(x.values())[0]['id'],
            'eyeem_username': lambda x: list(x.values())[0]['nickname'],
            'fullname': lambda x: list(x.values())[0]['fullname'],
            'bio': lambda x: list(x.values())[0]['description'],
            'followers': lambda x: list(x.values())[0]['totalFollowers'],
            'friends': lambda x: list(x.values())[0]['totalFriends'],
            'liked_photos': lambda x: list(x.values())[0]['totalLikedPhotos'],
            'photos': lambda x: list(x.values())[0]['totalPhotos'],
            'facebook_uid': lambda x: extract_facebook_uid(list(x.values())[0]['thumbUrl'])
        }
    },
    'Medium': {
        'flags': ['https://medium.com', 'com.medium.reader'],
        'regex': r'({"__typename":"User".+?}),"Collection',
        'extract_json': True,
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
        'regex': r'<div class="page-header page-header_full js-user_(?P<uid>\d+)">[\s\S]*?/users/(?P<username>.*?)/',
    },
    'Twitter': {
        'flags': ['abs.twimg.com', 'moreCSSBundles'],
        'regex': r'{&quot;id&quot;:(?P<uid>\d+),&quot;id_str&quot;:&quot;\d+&quot;,&quot;name&quot;:&quot;(?P<username>.*?)&quot;,&quot;screen_name&quot;:&quot;(?P<name>.*?)&quot;'
    },
    'Facebook user profile': {
        'flags': ['com.facebook.katana', 'scribe_endpoint'],
        'regex': r'{"imp_id":".+?","ef_page":.+?,"uri":".+?\/(?P<username>[^\/]+?)","entity_id":"(?P<uid>\d+)"}',
    },
    'Facebook group': {
        'flags': ['com.facebook.katana', 'XPagesProfileHomeController'],
        'regex': r'{"imp_id":".+?","ef_page":.+?,"uri":".+?\/(?P<username>[^\/]+?)","entity_id":"(?P<uid>\d+)"}',
    },
    'GitHub': {
        'flags': ['github.githubassets.com'],
        'regex': r'data-scope-id="(?P<uid>\d+)" data-scoped-search-url="/search\?user=(?P<username>.+?)"'
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
    '500px API': {
        'flags': ['{"data":{"profile":{"id"'],
        'regex': r'^{"data":({.+})}$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['profile']['id'],
            'legacy_id': lambda x: x['profile']['legacyId'],
            'username': lambda x: x['profile']['username'],
            'name': lambda x: x['profile']['displayName'],
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
        'flags': ['bitbucket.org/account'],
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
            'display_name': lambda x: x['displayName'],
            'is_employee': lambda x: x['isEmployee'],
            'is_nsfw': lambda x: x['isNSFW'],
            'is_mod': lambda x: x['isMod'],
            'is_following': lambda x: x['isFollowing'],
            'has_user_profile': lambda x: x['hasUserProfile'],
            'hide_from_robots': lambda x: x['hideFromRobots'],
            'created_utc': lambda x: x['createdUtc'],
            'total_karma': lambda x: x['totalKarma'],
            'post_karma': lambda x: x['postKarma'],
        },
    },
    'Steam': {
        'flags': ['store.steampowered.com'],
        'regex': r'({"url":".+?});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['steamid'],
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
        'regex': r'catch\(t\){}}\)},(\[{"id":.+?)\);',
        'extract_json': True,
        'message': 'Run with auth cookies to get your ids.',
        'fields': {
            'your_uid': lambda x: x[-2]['data'][0].get('id'),
            'your_name': lambda x: x[-2]['data'][0].get('full_name'),
            'your_username': lambda x: x[-2]['data'][0].get('username'),
            'uid': lambda x: x[-1]['data'][0]['id'],
            'name': lambda x: x[-1]['data'][0]['full_name'],
            'username': lambda x: x[-1]['data'][0]['username'],
        }
    },
    'TikTok': {
        'flags': ['tiktokcdn.com/tiktok/falcon/'],
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
            'followingCount': lambda x: x['stats']['followingCount'],
            'followerCount': lambda x: x['stats']['followerCount'],
            'heartCount': lambda x: x['stats']['heartCount'],
            'videoCount': lambda x: x['stats']['videoCount'],
            'diggCount': lambda x: x['stats']['diggCount'],
        }
    },
    'VC.ru': {
        'flags': ['property="og:site_name" content="vc.ru"'],
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
    'Vimeo': {
        'flags': ['i.vimeocdn.com', 'vimeo://app.vimeo.com/users/'],
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
            'registered_for_seconds': lambda x: x['deviantFor'],
            'gender': lambda x: x['gender'],
            'username': lambda x: x['username'],
            'twitter_username': lambda x: x['twitterUsername'],
            'website': lambda x: x['website'],
            'links': lambda x: [y['value'] for y in x['socialLinks']],
            'tagline': lambda x: x['tagline'],
        }
    }
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
}


def parse_cookies(cookies_str):
    cookies = SimpleCookie()
    cookies.load(cookies_str)
    logging.debug(cookies)
    return {key: morsel.value for key, morsel in cookies.items()}


def parse(url, cookies_str='', timeout=3):
    cookies = parse_cookies(cookies_str)
    page = requests.get(url, headers=HEADERS, cookies=cookies, allow_redirects=True, timeout=(timeout, timeout))
    logging.debug(page.text)
    logging.debug(page.status_code)
    return page.text, page.status_code


def extract(page):
    for scheme_name, scheme_data in schemes.items():
        flags = scheme_data['flags']
        found = all([flag in page for flag in flags])

        if found:
            logging.info('%s has been detected' % scheme_name)
            if 'message' in scheme_data:
                print(scheme_data['message'])
        else:
            continue

        info = re.search(scheme_data['regex'], page)

        if info:
            if scheme_data.get('extract_json', False):
                values = {}
                extracted = info.group(1)

                logging.debug(extracted)

                transforms = scheme_data.get('transforms', [])
                if transforms:
                    for t in transforms:
                        logging.debug(t)
                        extracted = t(extracted)
                        logging.debug(extracted)

                json_data = json.loads(extracted)

                if json_data == {}:
                    continue

                loaded_json_str = json.dumps(json_data, indent=4, sort_keys=True)

                logging.debug(loaded_json_str)
                if logging.root.level == logging.DEBUG:
                    with open('debug_extracted.json', 'w') as f:
                        f.write(loaded_json_str)

                for name, get_field in scheme_data['fields'].items():
                    value = get_field(json_data)
                    values[name] = str(value) if value != None else ''
            else:
                values = info.groupdict()

            return {a: b for a, b in values.items() if b or type(b) == bool}
        else:
            logging.info('Could not extract!')
    return {}
