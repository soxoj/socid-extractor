# -*- coding: utf-8 -*-
"""
Regression and unit-style checks for Maigret / LLM improvement log items.

Each test documents *what* is verified (see docstrings on test functions and assertion comments).
"""
import json

from socid_extractor.main import extract
from socid_extractor.postprocessor import Gravatar, StripInvalidGravatarUrls
from socid_extractor.schemes import schemes
from socid_extractor.utils import (
    imgur_profile_avatar_url, is_bare_gravatar_root_url, is_valid_gravatar_email_hash,
    safe_deep_get, extract_next_data, next_data_page_props,
)


def test_tiktok_hydration_script_extracts_user_and_stats():
    """
    Verifies the **TikTok** scheme matches `__UNIVERSAL_DATA_FOR_REHYDRATION__` JSON (current web),
    merges `user` + `stats`, and maps ids, nickname, bio, avatar, secUid, and counters.

    **Check:** `tiktok_id`, `tiktok_username`, `fullname`, `bio`, `sec_uid`, `follower_count`,
    `following_count`, `heart_count`, `video_count`, `digg_count`, and `image` are present and
    match the embedded fixture values (legacy `SIGI_STATE` pages remain covered by a separate scheme).
    """
    user_blob = {
        'id': '9001',
        'uniqueId': 'fixtureuser',
        'nickname': 'Fixture Nick',
        'signature': 'Bio line',
        'avatarMedium': 'https://example.cdn/avatar.jpg',
        'verified': False,
        'secret': False,
        'secUid': 'MS4wLjABAAAAfixture',
    }
    stats_blob = {
        'followerCount': 10,
        'followingCount': 20,
        'heartCount': 30,
        'videoCount': 40,
        'diggCount': 50,
    }
    payload = {
        '__DEFAULT_SCOPE__': {
            'webapp.user-detail': {
                'userInfo': {
                    'user': user_blob,
                    'stats': stats_blob,
                }
            }
        }
    }
    html = (
        '<!DOCTYPE html><html><head></head><body>'
        '<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">'
        + json.dumps(payload)
        + '</script></body></html>'
    )
    info = extract(html)
    assert info.get('tiktok_id') == '9001'
    assert info.get('tiktok_username') == 'fixtureuser'
    assert info.get('fullname') == 'Fixture Nick'
    assert info.get('bio') == 'Bio line'
    assert info.get('sec_uid') == 'MS4wLjABAAAAfixture'
    assert info.get('follower_count') == '10'
    assert info.get('following_count') == '20'
    assert info.get('heart_count') == '30'
    assert info.get('video_count') == '40'
    assert info.get('digg_count') == '50'
    assert info.get('image') == 'https://example.cdn/avatar.jpg'


def test_picsart_api_json_maps_profile_fields():
    """
    Verifies **Picsart API** scheme on a full JSON body: success payloads expose `picsart_id`,
    username, display name, photo URL, and counters.

    **Check:** `flags` match real `api.picsart.com/users/show/{user}.json` responses; numeric id is
    stringified like other fields.
    """
    body = {
        'status': 'success',  # not used as a flag; matching uses remix_score + dashboard_visibility
        'id': 184924161000102,
        'name': 'Adam',
        'username': 'adam',
        'photo': 'https://example.com/p.jpg',
        'status_message': '',
        'followers_count': 3,
        'following_count': 5,
        'likes_count': 0,
        'photos_count': 0,
        'remix_score': 0,
        'dashboard_visibility': False,
        'is_verified': False,
    }
    info = extract(json.dumps(body))
    assert info.get('picsart_username') == 'adam'
    assert info.get('fullname') == 'Adam'
    assert info.get('picsart_id') == '184924161000102'
    assert info.get('image') == 'https://example.com/p.jpg'
    assert info.get('follower_count') == '3'
    assert info.get('following_count') == '5'


def test_imgur_api_adds_canonical_profile_avatar_url():
    """
    Verifies **Imgur API** field `imgur_profile_avatar_url`: stable `https://imgur.com/user/{user}/avatar`
    alongside CDN `avatar_url` (per improvement log).

    **Check:** helper `imgur_profile_avatar_url` matches the same string the scheme emits.
    """
    body = {
        'id': 123,
        'username': 'sardelkin',
        'bio': '',
        'reputation_count': 1,
        'reputation_name': 'Neutral',
        'avatar_url': 'https://i.imgur.com/x.png',
        'created_at': '2010-01-01',
    }
    info = extract(json.dumps(body))
    assert info.get('imgur_username') == 'sardelkin'
    assert info.get('imgur_profile_avatar_url') == imgur_profile_avatar_url('sardelkin')
    assert info.get('imgur_profile_avatar_url') == 'https://imgur.com/user/sardelkin/avatar'


def test_strip_invalid_gravatar_urls_clears_bare_homepage():
    """
    Verifies **StripInvalidGravatarUrls**: values that are only `https://gravatar.com` (no `/avatar/hash`)
    are cleared from `gravatar_url` and `image` so downstream tools do not treat them as images.

    **Check:** bare root URL is detected; valid avatar URLs are untouched.
    """
    assert is_bare_gravatar_root_url('https://gravatar.com') is True
    assert is_bare_gravatar_root_url('https://www.gravatar.com/') is True
    assert is_bare_gravatar_root_url('https://secure.gravatar.com/avatar/abc') is False

    cleared = StripInvalidGravatarUrls(
        {'gravatar_url': 'https://gravatar.com', 'image': 'https://www.gravatar.com'}
    ).process()
    assert cleared.get('gravatar_url') == ''
    assert cleared.get('image') == ''

    untouched = StripInvalidGravatarUrls(
        {'image': 'https://secure.gravatar.com/avatar/' + '0' * 32}
    ).process()
    assert untouched == {}


def test_gravatar_postprocessor_requires_md5_hash():
    """
    Verifies **Gravatar** postprocessor only emits `gravatar_url` / hash fields when the image URL
    contains a valid 32-char hex MD5 in `/avatar/{hash}` (avoids bogus homepage-derived output).

    **Check:** `is_valid_gravatar_email_hash` gates emission; hash helper consistency.
    """
    assert is_valid_gravatar_email_hash('0' * 32) is True
    assert is_valid_gravatar_email_hash('gg' * 16) is False

    good = Gravatar(
        {'username': 'me', 'image': 'https://www.gravatar.com/avatar/' + 'a' * 32 + '?d=retro'}
    ).process()
    assert good.get('gravatar_email_md5_hash') == 'a' * 32
    assert 'gravatar.com' in good.get('gravatar_url', '')

    bad = Gravatar({'username': 'me', 'image': 'https://gravatar.com'}).process()
    assert bad == {}


def test_twitchtracker_embedded_channel_script():
    """TwitchTracker: `window.channel` JS literal with id, login, created_at."""
    html = """<!DOCTYPE html><html><head>
<meta property="og:site_name" content="TwitchTracker">
</head><body>
<script>\n\t\twindow.channel = {\n\t\t\tid: 37402112,\n\t\t\tname: 'shroud',\n\t\t\tcreated_at: '2012-11-03'\n\t\t}\n\t</script>
</body></html>"""
    info = extract(html)
    assert info.get('twitchtracker_channel_id') == '37402112'
    assert info.get('twitchtracker_username') == 'shroud'
    assert info.get('twitchtracker_created_at') == '2012-11-03'


def test_chess_com_pub_api_json():
    """Chess.com API: public `/pub/player/{user}` JSON (optional mutate from /member/)."""
    body = (
        '{"avatar":"https://images.chesscomfiles.com/uploads/v1/user/15448422.x.png",'
        '"player_id":15448422,"username":"hikaru","name":"Hikaru Nakamura","title":"GM",'
        '"followers":100,"country":"https://api.chess.com/pub/country/US",'
        '"location":"Florida","last_online":1774140579,"joined":1389043258,'
        '"status":"premium","is_streamer":true,"verified":false,"twitch_url":"https://twitch.tv/gmhikaru"}'
    )
    info = extract(body)
    assert info.get('chess_user_id') == '15448422'
    assert info.get('username') == 'hikaru'
    assert info.get('fullname') == 'Hikaru Nakamura'
    assert info.get('country_code') == 'US'
    assert info.get('follower_count') == '100'
    assert info.get('is_verified') == 'False'
    assert info.get('created_at')
    assert info.get('latest_activity_at')


def test_roblox_user_api_json():
    """Roblox GET /v1/users/{id} envelope."""
    body = (
        '{"description":"x","created":"2006-02-27T21:06:40.3Z","isBanned":false,'
        '"externalAppDisplayName":null,"hasVerifiedBadge":true,"id":1,'
        '"name":"Roblox","displayName":"Roblox"}'
    )
    info = extract(body)
    assert info.get('roblox_user_id') == '1'
    assert info.get('username') == 'Roblox'
    assert info.get('is_verified') == 'True'


def test_roblox_username_lookup_api_json():
    """Roblox POST /v1/usernames/users first user object."""
    body = (
        '{"data":[{"requestedUsername":"Roblox","hasVerifiedBadge":true,"id":1,'
        '"name":"Roblox","displayName":"Roblox"}]}'
    )
    info = extract(body)
    assert info.get('roblox_user_id') == '1'
    assert info.get('username') == 'Roblox'


def test_myanimelist_profile_regex():
    """MAL profile: numeric uid from analytics param + username from og:url."""
    html = """<!DOCTYPE html><html><head>
<meta property="og:url" content="https://myanimelist.net/profile/Xinil">
</head><body>
<div class="user-profile">
<a href="#" data-ga-click-param="uid:1" title="msg"><i></i></a>
</div></body></html>"""
    info = extract(html)
    assert info.get('mal_username') == 'Xinil'
    assert info.get('mal_uid') == '1'


def test_xvideos_profile_full():
    """XVideos profile: extract user id, username, display name, gender, country, subscribers, signed up."""
    html = (
        '<html lang="en" class="xv-responsive"><body>'
        '<a href="https://www.xvideos.com/profiles/soxoj">p</a>'
        '<script>"id_user":613639497,"username":"soxoj","display":"Soxoj","profile_picture_small":"","profile_picture":"","sex":"Man","url":"/profiles/soxoj"</script>'
        '<div class="col-sm-4 col-xs-12 pfinfo-col" id="pfinfo-col-col1">'
        '<p id="pinfo-sex"><strong>Gender:</strong> <span>Man</span></p>'
        '<p id="pinfo-country"><strong>Country:</strong> <span>Honduras</span></p>'
        '<p id="pinfo-profile-hits"><strong>Profile hits:</strong> <span>1,768</span></p>'
        '<p id="pinfo-subscribers"><strong>Subscribers:</strong> <span>4</span></p>'
        '<p id="pinfo-signedup"><strong>Signed up:</strong> <span>July 16, 2022 (1,354 days ago)</span></p>'
        '</div></body></html>'
    )
    info = extract(html)
    assert info.get('uid') == '613639497'
    assert info.get('username') == 'soxoj'
    assert info.get('fullname') == 'Soxoj'
    assert info.get('gender') == 'Man'
    assert info.get('country') == 'Honduras'
    assert info.get('profile_hits') == '1,768'
    assert info.get('follower_count') == '4'
    assert 'July 16, 2022' in info.get('created_at', '')


def test_lnk_bio_next_data_fixture():
    """lnk.bio-style __NEXT_DATA__ with pageProps.profile (fixture; live HTML may differ)."""
    next_data = {
        'props': {
            'pageProps': {
                'profile': {
                    'username': 'fixture',
                    'displayName': 'Fixture User',
                    'bio': 'Hello',
                    'avatar': 'https://example.com/a.png',
                    'links': [{'title': 'Site', 'url': 'https://example.org'}],
                }
            }
        }
    }
    html = (
        '<!DOCTYPE html><html><head><title>lnk.bio</title></head><body>'
        '<link rel="canonical" href="https://lnk.bio/fixture" />'
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(next_data)
        + '</script>mention lnk.bio in body for flags</body></html>'
    )
    info = extract(html)
    assert info.get('username') == 'fixture'
    assert info.get('fullname') == 'Fixture User'
    assert 'example.org' in info.get('links', '')


def test_buzzfeed_next_data_extraction():
    """
    Verifies the **BuzzFeed** scheme matches pages containing `buzzfeed.com`
    and `__NEXT_DATA__`, extracts user profile fields from the embedded JSON,
    and correctly constructs image URLs.

    **Check:** `uuid`, `id`, `fullname`, `username`, `bio`, `posts_count`,
    `is_community_user`, `is_deleted`, `image`, and `social_links` are present.
    """
    next_data = {
        'props': {
            'pageProps': {
                'user_uuid': 'abc-123-def',
                'user': {
                    'id': 99999,
                    'displayName': 'TestUser',
                    'username': 'testuser',
                    'bio': 'Hello world',
                    'memberSince': 1261100829,
                    'isCommunityUser': True,
                    'deleted': False,
                    'social': [{'name': 'twitter', 'url': 'https://twitter.com/test'}],
                    'image': '/static/user_images/test.jpg',
                    'headerImage': '/static/enhanced/test_wide.jpg',
                },
                'buzz_count': 5,
            }
        },
        'page': '/[username]',
        'query': {'username': 'testuser'},
        'buildId': 'fixture123',
    }
    html = (
        '<!DOCTYPE html><html><head>'
        '<link rel="canonical" href="https://www.buzzfeed.com/testuser">'
        '</head><body>'
        '<div>Content from buzzfeed.com</div>'
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(next_data)
        + '</script></body></html>'
    )
    info = extract(html)
    assert info.get('uuid') == 'abc-123-def'
    assert info.get('id') == '99999'
    assert info.get('fullname') == 'TestUser'
    assert info.get('username') == 'testuser'
    assert info.get('bio') == 'Hello world'
    assert info.get('posts_count') == '5'
    assert info.get('is_community_user') == 'True'
    assert info.get('is_deleted') == 'False'
    assert 'buzzfeed-static' in info.get('image', '')
    assert 'twitter.com/test' in info.get('social_links', '')


def test_fandom_mediawiki_api_json():
    """Fandom MediaWiki API: extract userid and canonical username from user query response."""
    body = json.dumps({
        "batchcomplete": "",
        "query": {
            "users": [
                {"userid": 22693, "name": "Red"}
            ]
        }
    })
    info = extract(body)
    assert info.get('uid') == '22693'
    assert info.get('username') == 'Red'


def test_fandom_mediawiki_api_missing_user():
    """Fandom MediaWiki API: missing user has no userid — scheme should still match but yield empty uid."""
    body = json.dumps({
        "batchcomplete": "",
        "query": {
            "users": [
                {"name": "NonexistentUser12345", "missing": ""}
            ]
        }
    })
    info = extract(body)
    # missing user has no userid → uid should be absent or empty
    assert info.get('username') == 'NonexistentUser12345'
    assert not info.get('uid')


def test_substack_public_profile_api_json():
    """Substack public profile API: extract user fields from JSON response."""
    body = json.dumps({
        "id": 188506911,
        "name": "Philip",
        "handle": "user23",
        "photo_url": "https://substack-post-media.s3.amazonaws.com/photo.jpg",
        "bio": "Been Internettin' since 1997",
        "profile_set_up_at": "2023-12-11T03:04:51.141Z",
    })
    info = extract(body)
    assert info.get('uid') == '188506911'
    assert info.get('username') == 'user23'
    assert info.get('fullname') == 'Philip'
    assert info.get('bio') == "Been Internettin' since 1997"
    assert 'substack-post-media' in info.get('image', '')


def test_hashnode_graphql_api_json():
    """hashnode GraphQL API: extract username and fullname from GraphQL response."""
    body = json.dumps({
        "data": {
            "user": {
                "name": "Melwin D'Almeida",
                "username": "melwinalm"
            }
        }
    })
    info = extract(body)
    assert info.get('username') == 'melwinalm'
    assert info.get('fullname') == "Melwin D'Almeida"


def test_hashnode_graphql_api_null_user():
    """hashnode GraphQL API: null user (unclaimed) should yield empty result."""
    body = json.dumps({
        "data": {
            "user": None
        }
    })
    info = extract(body)
    assert not info.get('username')
    assert not info.get('fullname')


def test_rarible_api_json():
    """Rarible API: extract user ownership info from marketplace API response."""
    body = json.dumps({
        "createDate": "2020-07-21T15:18:51.758+00:00",
        "id": "blue",
        "owner": "0x0000000000000000000000000000000000000000",
        "ref": "0x65d472172e4933aa4ddb995cf4ca8bef72a46576",
        "type": "USER",
        "version": 0,
    })
    info = extract(body)
    assert info.get('rarible_id') == 'blue'
    assert info.get('rarible_owner') == '0x0000000000000000000000000000000000000000'
    assert info.get('rarible_ref') == '0x65d472172e4933aa4ddb995cf4ca8bef72a46576'
    assert info.get('rarible_type') == 'USER'
    assert info.get('created_at') == '2020-07-21T15:18:51.758+00:00'


def test_cssbattle_next_data_fixture():
    """CSSBattle: extract player stats from __NEXT_DATA__ embedded JSON."""
    next_data = {
        "props": {
            "pageProps": {
                "player": {
                    "id": "8wBrf63WLOOv8JuCeknfYk7t94B3",
                    "username": "beo",
                    "gamesPlayed": 55,
                    "score": 1234.56,
                }
            }
        }
    }
    html = (
        '<!DOCTYPE html><html><head><title>CSSBattle</title></head><body>'
        '<link rel="canonical" href="https://cssbattle.dev/player/beo" />'
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(next_data)
        + '</script>cssbattle.dev footer</body></html>'
    )
    info = extract(html)
    assert info.get('cssbattle_id') == '8wBrf63WLOOv8JuCeknfYk7t94B3'
    assert info.get('cssbattle_username') == 'beo'
    assert info.get('cssbattle_games_played') == '55'
    assert info.get('cssbattle_score') == '1234.56'


def test_max_ru_sveltekit_profile():
    """Max (max.ru): extract channel info from SvelteKit hydration JS object."""
    html = (
        '<!DOCTYPE html><html><head></head><body>'
        '<script>__sveltekit_start({data:[null,{type:"data",data:'
        '{channel:{title:"Ирина Волк",description:"Канал генерал-лейтенанта",'
        'icon:"https://i.oneme.ru/i?r=abc123",participantsCount:15599}}'
        ',uses:{url:1}},null]})</script>'
        '</body></html>'
    )
    info = extract(html)
    assert info.get('max_title') == 'Ирина Волк'
    assert info.get('max_description') == 'Канал генерал-лейтенанта'
    assert 'oneme.ru' in info.get('max_icon', '')
    assert info.get('max_participants_count') == '15599'


def test_periscope_profile_extraction():
    """Periscope (pscp.tv): extract user profile fields from data-store JSON."""
    user_data = {
        'id': 'abc123XYZ',
        'created_at': '2016-04-10T18:22:05.411012300+00:00',
        'username': 'Polina_Zograf',
        'display_name': '🌸',
        'description': 'Travel blogger',
        'n_followers': 1200,
        'n_following': 85,
        'n_hearts': 54320,
        'n_broadcasts': 42,
        'is_beta_user': False,
        'is_employee': False,
        'isVerified': False,
        'is_twitter_verified': True,
        'twitterUserId': '78901234',
        'twitter_screen_name': 'polina_z',
        'profile_image_urls': [
            {'url': 'https://pbs.twimg.com/profile_images/123/photo.jpg', 'width': 128, 'height': 128}
        ],
    }
    data_store = {
        'canonicalPeriscopeUrl': 'https://www.pscp.tv/Polina_Zograf',
        'UserCache': {
            'users': {
                'abc123XYZ': {
                    'user': user_data
                }
            }
        },
    }
    escaped = json.dumps(data_store).replace('"', '&quot;')
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:site_name" content="Periscope"/>'
        '<link rel="alternate" href="pscp://user/abc123XYZ"/>'
        '</head><body>'
        '<div data-store="' + escaped + '"><div id="PageView">'
        '<div>page content</div>'
        '</div></div></body></html>'
    )
    info = extract(html)
    assert info.get('id') == 'abc123XYZ'
    assert info.get('periscope_username') == 'Polina_Zograf'
    assert info.get('fullname') == '🌸'
    assert info.get('bio') == 'Travel blogger'
    assert info.get('image') == 'https://pbs.twimg.com/profile_images/123/photo.jpg'
    assert info.get('follower_count') == '1200'
    assert info.get('following_count') == '85'
    assert info.get('hearts_count') == '54320'
    assert info.get('broadcasts_count') == '42'
    assert info.get('is_beta_user') == 'False'
    assert info.get('is_employee') == 'False'
    assert info.get('isVerified') == 'False'
    assert info.get('is_twitter_verified') == 'True'
    assert info.get('twitterUserId') == '78901234'
    assert info.get('twitter_screen_name') == 'polina_z'
    assert info.get('created_at') == '2016-04-10T18:22:05.411012300+00:00'


def test_bluesky_api_json():
    """Bluesky API: extract profile fields from public AT Protocol API response."""
    body = json.dumps({
        "did": "did:plc:oky5czdrnfjpqslsw2a5iclo",
        "handle": "jay.bsky.team",
        "displayName": "Jay",
        "description": "Building the AT Protocol",
        "avatar": "https://cdn.bsky.app/img/avatar/plain/did:plc:oky5czdrnfjpqslsw2a5iclo/photo.jpg",
        "banner": "https://cdn.bsky.app/img/banner/plain/did:plc:oky5czdrnfjpqslsw2a5iclo/banner.jpg",
        "followersCount": 50000,
        "followsCount": 200,
        "postsCount": 1500,
        "createdAt": "2022-11-17T06:31:40.296Z",
        "labels": [],
    })
    info = extract(body)
    assert info.get('uid') == 'did:plc:oky5czdrnfjpqslsw2a5iclo'
    assert info.get('username') == 'jay.bsky.team'  # custom domain, no .bsky.social suffix
    assert info.get('fullname') == 'Jay'
    assert info.get('bio') == 'Building the AT Protocol'
    assert 'cdn.bsky.app' in info.get('image', '')
    assert info.get('follower_count') == '50000'
    assert info.get('following_count') == '200'
    assert info.get('posts_count') == '1500'
    assert info.get('created_at') == '2022-11-17T06:31:40.296Z'


def test_bluesky_api_strips_bsky_social_suffix():
    """Bluesky API: .bsky.social suffix is stripped from handle."""
    body = json.dumps({
        "did": "did:plc:abc123",
        "handle": "alice.bsky.social",
        "displayName": "Alice",
        "followersCount": 10,
        "followsCount": 5,
        "postsCount": 1,
    })
    info = extract(body)
    assert info.get('username') == 'alice'


def test_scratch_api_json():
    """Scratch API: extract user profile from scratch.mit.edu API response."""
    body = json.dumps({
        "id": 1882674,
        "username": "griffpatch",
        "scratchteam": False,
        "history": {"joined": "2012-11-20T16:43:15.000Z"},
        "profile": {
            "id": None,
            "images": {"90x90": "https://cdn2.scratch.mit.edu/get_image/user/1882674_90x90.png"},
            "status": "I make games!",
            "bio": "Hi, I'm griffpatch. I love coding in Scratch!",
            "country": "United Kingdom",
        },
    })
    info = extract(body)
    assert info.get('uid') == '1882674'
    assert info.get('username') == 'griffpatch'
    assert info.get('bio') == "Hi, I'm griffpatch. I love coding in Scratch!"
    assert info.get('status') == 'I make games!'
    assert info.get('country') == 'United Kingdom'
    assert 'scratch.mit.edu' in info.get('image', '')
    assert info.get('created_at') == '2012-11-20T16:43:15.000Z'
    assert info.get('is_scratchteam') == 'False'


def test_wikipedia_user_api_json():
    """Wikipedia user API: extract user info from MediaWiki user query with editcount."""
    body = json.dumps({
        "batchcomplete": "",
        "query": {
            "users": [{
                "userid": 24920566,
                "name": "Example",
                "editcount": 42,
                "registration": "2015-04-24T07:00:51Z",
                "gender": "male",
            }]
        }
    })
    info = extract(body)
    assert info.get('uid') == '24920566'
    assert info.get('username') == 'Example'
    assert info.get('edit_count') == '42'
    assert info.get('created_at') == '2015-04-24T07:00:51Z'
    assert info.get('gender') == 'male'


def test_dailymotion_api_json():
    """DailyMotion API: extract user profile from API response."""
    body = json.dumps({
        "id": "x23k8rz",
        "username": "cnn",
        "screenname": "CNN",
        "description": "CNN breaking news",
        "avatar_720_url": "https://s2.dmcdn.net/d/5000002HraHpp/720x720",
        "cover_250_url": "https://s2.dmcdn.net/d/cover/250",
        "followers_total": 150000,
        "following_total": 50,
        "videos_total": 3200,
        "country": "US",
        "created_time": 1518206261,
        "verified": True,
        "url": "https://www.dailymotion.com/cnn",
    })
    info = extract(body)
    assert info.get('uid') == 'x23k8rz'
    assert info.get('username') == 'cnn'
    assert info.get('fullname') == 'CNN'
    assert info.get('bio') == 'CNN breaking news'
    assert 'dmcdn.net' in info.get('image', '')
    assert info.get('follower_count') == '150000'
    assert info.get('videos_count') == '3200'
    assert info.get('country') == 'US'
    assert info.get('is_verified') == 'True'


def test_slideshare_next_data_user():
    """SlideShare: extract user from __NEXT_DATA__ embedded JSON."""
    next_data = {
        "props": {
            "pageProps": {
                "user": {
                    "id": 133494799,
                    "name": "Reed Hastings",
                    "login": "ReedHastings",
                    "photo": "https://public.slidesharecdn.com/v2/images/profile-picture.png",
                    "description": "Co-founder of Netflix",
                    "slideshowCount": 12,
                    "followersCount": 500,
                    "followingCount": 10,
                    "city": "San Francisco",
                    "country": "US",
                    "organization": "Netflix",
                    "occupation": "CEO",
                    "url": "https://netflix.com",
                    "suspended": False,
                    "isOrganization": False,
                }
            }
        }
    }
    html = (
        '<!DOCTYPE html><html><head></head><body>'
        '<link rel="stylesheet" href="https://public.slidesharecdn.com/v2/css/main.css">'
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(next_data)
        + '</script></body></html>'
    )
    info = extract(html)
    assert info.get('uid') == '133494799'
    assert info.get('fullname') == 'Reed Hastings'
    assert info.get('username') == 'ReedHastings'
    assert info.get('bio') == 'Co-founder of Netflix'
    assert info.get('slideshow_count') == '12'
    assert info.get('follower_count') == '500'
    assert info.get('organization') == 'Netflix'
    assert info.get('website') == 'https://netflix.com'
    assert info.get('is_suspended') == 'False'


def test_wordpress_org_profile():
    """WordPress.org Profile: extract username and fullname from og:title meta tag."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:title" content="WordPress (@wordpress) - WordPress user profile">'
        '<meta property="og:image" content="https://www.gravatar.com/avatar/834ffe?s=1024">'
        '<li id="user-member-since"><div>Member Since</div></li>'
        '<link rel="canonical" href="https://profiles.wordpress.org/wordpress/">'
        '</head><body></body></html>'
    )
    info = extract(html)
    assert info.get('fullname') == 'WordPress'
    assert info.get('username') == 'wordpress'
    assert 'gravatar.com' in info.get('image', '')


def test_weebly_js_vars():
    """Weebly: extract user_id and site_id from inline JS variables."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<link rel="stylesheet" href="https://cdn2.editmysite.com/css/main.css">'
        '</head><body>'
        '<script>com_currentSite = "183235046254098859"; com_userID = "125320777";</script>'
        '</body></html>'
    )
    info = extract(html)
    assert info.get('uid') == '125320777'
    assert info.get('weebly_site_id') == '183235046254098859'


def test_calendly_api_json():
    """Calendly: extract booking profile fields from API JSON response."""
    body = json.dumps({
        "id": 7723,
        "avatar_url": None,
        "description": "Welcome to my scheduling page.",
        "is_landing_page": False,
        "locale": "en",
        "logo_url": None,
        "name": "admin google",
        "organization_uuid": "DFBBGBHGHUHT7RGG",
        "owner_type": "User",
        "owning_user": {"id": 8173, "uuid": "27f70b874abf8cd45edcdb092001661b"},
        "slug": "google",
        "timezone": "America/New_York",
        "unavailability_reason": None,
        "unbranded": False,
    })
    info = extract(body)
    assert info.get('uid') == '7723'
    assert info.get('fullname') == 'admin google'
    assert info.get('username') == 'google'
    assert info.get('bio') == 'Welcome to my scheduling page.'
    assert info.get('owner_uuid') == '27f70b874abf8cd45edcdb092001661b'
    assert info.get('organization_uuid') == 'DFBBGBHGHUHT7RGG'
    assert info.get('timezone') == 'America/New_York'


def test_google_play_developer():
    """Google Play Developer: extract developer name from og:title."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:title" content="Android Apps by Google LLC on Google Play">'
        '<script>AF_initDataCallback({key:"ds:3"});</script>'
        '<link rel="canonical" href="https://play.google.com/store/apps/developer?id=Google+LLC">'
        '</head><body></body></html>'
    )
    info = extract(html)
    assert info.get('developer_name') == 'Google LLC'


def test_amazon_author_page():
    """Amazon Author: extract author name, id and store id from inline JSON."""
    html = (
        '<!DOCTYPE html><html><head></head><body>'
        '<div data-a-page-id="stores/author/B000AQ3RBI">'
        '<script>var config = {"widgetType":"AuthorSubHeader","content":{"authorName":"Richard Dawkins"},'
        '"pageContext":{"authorId":"B000AQ3RBI","storeId":"b55aba37-be09-3e56-80fb-da9cda3c406b"'
        ',"pageDescription":"Follow Richard Dawkins"'
        ',"brandLogo":{"image":"https://m.media-amazon.com/images/I/41viH8VtXtL.jpg"}'
        '}};</script>'
        '</body></html>'
    )
    info = extract(html)
    assert info.get('author_name') == 'Richard Dawkins'
    assert info.get('author_id') == 'B000AQ3RBI'
    assert info.get('store_id') == 'b55aba37-be09-3e56-80fb-da9cda3c406b'


def test_stack_overflow_user_init():
    """Stack Overflow: extract userId and accountId from StackExchange.user.init call."""
    html = (
        '<!DOCTYPE html><html><head></head><body>'
        '<script>StackExchange.user.init({ userId: 22656, accountId: 11683 });</script>'
        '</body></html>'
    )
    info = extract(html)
    assert info.get('uid') == '22656'
    assert info.get('stack_exchange_uid') == '11683'


def test_linktree_updated_flags():
    """Linktree: verify updated flags work with current page format."""
    next_data = {
        "props": {
            "pageProps": {
                "account": {
                    "id": 12345,
                    "uuid": "6ba1b72b-4009-11eb-85b8-0a26086d88df",
                    "isActive": True,
                    "tier": "free",
                    "links": [{"url": "https://example.com"}],
                },
                "username": "testuser",
                "profilePictureUrl": "https://ugc.production.linktr.ee/pic.jpg",
                "isProfileVerified": True,
                "description": "My bio",
                "socialLinks": [{"type": "TWITTER", "url": "https://twitter.com/test"}],
            }
        }
    }
    html = (
        '<!DOCTYPE html><html><head></head><body>'
        '<link rel="canonical" href="https://linktr.ee/testuser">'
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(next_data)
        + '</script></body></html>'
    )
    info = extract(html)
    assert info.get('id') == '12345'
    assert info.get('username') == 'testuser'
    assert info.get('is_verified') == 'True'
    assert info.get('bio') == 'My bio'


def test_picsart_facebook_uid_from_photo():
    """Picsart API: extract facebook_uid from graph.facebook.com photo URL."""
    body = {
        'id': 100,
        'name': 'FbUser',
        'username': 'fbuser',
        'photo': 'https://graph.facebook.com/999888777/picture',
        'followers_count': 0,
        'following_count': 0,
        'likes_count': 0,
        'photos_count': 0,
        'remix_score': 0,
        'dashboard_visibility': False,
        'is_verified': False,
    }
    info = extract(json.dumps(body))
    assert info.get('facebook_uid') == '999888777'


def test_picsart_no_facebook_uid_when_no_graph_url():
    """Picsart API: facebook_uid is absent when photo is not a graph.facebook.com URL."""
    body = {
        'id': 101,
        'name': 'NormalUser',
        'username': 'normaluser',
        'photo': 'https://example.com/pic.jpg',
        'followers_count': 0,
        'following_count': 0,
        'likes_count': 0,
        'photos_count': 0,
        'remix_score': 0,
        'dashboard_visibility': False,
        'is_verified': False,
    }
    info = extract(json.dumps(body))
    assert not info.get('facebook_uid')


def test_habr_profile_extraction():
    """Habr: extract fullname, username, and profile URL from og meta tags."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:site_name" content="Хабр">'
        '<meta property="og:title" content="Иван Петров aka ipetrov  '
        '\n- "'
        '<meta property="og:url" content="https://habr.com/ru/users/ipetrov/">'
        '</head><body>habr.com/ru/users/ipetrov</body></html>'
    )
    info = extract(html)
    assert info.get('fullname') == 'Иван Петров'
    assert info.get('username') == 'ipetrov'
    assert 'habr.com/ru/users/ipetrov' in info.get('website', '')


def test_taplink_profile_extraction():
    """Taplink: extract image, fullname, and username from og meta tags."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:site_name" content="Taplink">'
        '<meta property="og:image" content="https://taplink.st/p/8/a/2/photo.jpg">'
        '<meta property="og:title" content="John Doe at Taplink">'
        '<meta property="og:url" content="https://taplink.cc/johndoe">'
        '</head><body>Welcome at Taplink</body></html>'
    )
    info = extract(html)
    assert info.get('fullname') == 'John Doe'
    assert info.get('username') == 'johndoe'
    assert 'taplink.st' in info.get('image', '')


def test_producthunt_profile_extraction():
    """Product Hunt: extract twitter_username and username from meta tags."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:site_name" content="Product Hunt">'
        '<meta property="og:type" content="profile">'
        '<meta name="twitter:creator" content="@rrhoover">'
        '<meta property="og:url" content="https://www.producthunt.com/@rrhoover">'
        '</head><body></body></html>'
    )
    info = extract(html)
    assert info.get('twitter_username') == 'rrhoover'
    assert info.get('username') == 'rrhoover'


def test_threads_profile_extraction():
    """Threads: extract fullname, username, follower/post counts, bio from OG tags."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:title" content="Mark Zuckerberg (@zuck) · Threads, Say more">'
        '<meta property="og:description" content="12,500 Followers · 340 Threads · &quot;CEO of Meta&quot;">'
        '</head><body>'
        '<div class="barcelona">content</div>'
        '</body></html>'
    )
    info = extract(html)
    assert info.get('fullname') == 'Mark Zuckerberg'
    assert info.get('username') == 'zuck'
    assert info.get('follower_count') == '12,500'
    assert info.get('posts_count') == '340'
    assert info.get('bio') == 'CEO of Meta'


# ---------------------------------------------------------------------------
# Structural / meta tests
# ---------------------------------------------------------------------------

def test_no_flag_subset_shadows():
    """Detect scheme pairs where one's flags are a subset of another's.

    If scheme A's flags ⊂ scheme B's flags and A appears *before* B in the
    dict, then B can never match because A always wins.  This test ensures
    every pair where one is a strict subset is ordered correctly (more specific
    first).
    """
    names = list(schemes.keys())
    for i, name_a in enumerate(names):
        flags_a = set(schemes[name_a]['flags'])
        for j, name_b in enumerate(names):
            if i == j:
                continue
            flags_b = set(schemes[name_b]['flags'])
            if flags_a < flags_b and i > j:
                # A has strictly fewer flags than B but comes AFTER B
                # This means the more specific B can never be reached
                # because less specific A matches first — that's fine.
                # The problem is the REVERSE: less specific before more specific.
                pass
            if flags_b < flags_a and i < j:
                # A (earlier) has MORE flags (more specific) than B (later) — correct order
                pass
            if flags_a < flags_b and i < j:
                # A (earlier) is LESS specific than B (later) — B is shadowed!
                raise AssertionError(
                    f'Scheme "{name_a}" (pos {i}, flags={flags_a}) shadows '
                    f'"{name_b}" (pos {j}, flags={flags_b}) because its flags '
                    f'are a strict subset and it appears earlier. '
                    f'Move "{name_b}" before "{name_a}".'
                )


def test_safe_deep_get():
    """Verify safe_deep_get traverses nested structures without raising."""
    data = {'a': {'b': [{'c': 42}]}}
    assert safe_deep_get(data, 'a', 'b', 0, 'c') == 42
    assert safe_deep_get(data, 'a', 'x') is None
    assert safe_deep_get(data, 'a', 'b', 99) is None
    assert safe_deep_get(None, 'a') is None
    assert safe_deep_get(data, 'a', 'b', 0, 'c', default='fallback') == 42
    assert safe_deep_get(data, 'z', default='fallback') == 'fallback'


def test_extract_next_data_helper():
    """Verify extract_next_data parses __NEXT_DATA__ from HTML."""
    html = '<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"x":1}}}</script>'
    result = extract_next_data(html)
    assert result == {"props": {"pageProps": {"x": 1}}}
    assert extract_next_data('no script here') == {}
    assert extract_next_data('') == {}


def test_next_data_page_props_helper():
    """Verify next_data_page_props extracts nested pageProps subkeys."""
    data = {"props": {"pageProps": {"user": {"name": "Alice"}}}}
    html = '<script id="__NEXT_DATA__" type="application/json">' + json.dumps(data) + '</script>'
    result = json.loads(next_data_page_props(html, 'user'))
    assert result == {"name": "Alice"}
    # Missing key returns empty dict serialized
    result2 = json.loads(next_data_page_props(html, 'nonexistent'))
    assert result2 == {}


def test_youtube_ytinitialdata():
    """YouTube ytInitialData: extract channel metadata from embedded JSON."""
    yt_data = {
        "metadata": {
            "channelMetadataRenderer": {
                "title": "Google",
                "externalId": "UCK8sQmJBp8GCxrOtXWBpyEA",
                "description": "Official Google channel",
                "vanityChannelUrl": "http://www.youtube.com/@Google",
                "avatar": {"thumbnails": [{"url": "https://yt3.googleusercontent.com/avatar.jpg"}]},
                "keywords": "Google Technology",
                "isFamilySafe": True,
                "facebookProfileId": "Google",
            }
        }
    }
    html = (
        '<!DOCTYPE html><html><head></head><body>'
        '<script>var ytInitialData = '
        + json.dumps(yt_data)
        + ';</script><script>var ytInitialPlayerResponse = {};</script>'
        '<div>channelMetadataRenderer present</div>'
        '</body></html>'
    )
    info = extract(html)
    assert info.get('youtube_channel_id') == 'UCK8sQmJBp8GCxrOtXWBpyEA'
    assert info.get('fullname') == 'Google'
    assert info.get('bio') == 'Official Google channel'
    assert 'yt3.googleusercontent.com' in info.get('image', '')
    assert info.get('channel_url') == 'http://www.youtube.com/@Google'
    assert info.get('keywords') == 'Google Technology'
    assert info.get('is_family_safe') == 'True'
    assert info.get('facebook_id') == 'Google'


def test_lesswrong_graphql_api():
    """Lesswrong GraphQL API: extract user profile from GQL response."""
    body = json.dumps({
        "data": {
            "user": {
                "result": {
                    "displayName": "Eliezer Yudkowsky",
                    "slug": "eliezer_yudkowsky",
                    "karma": 159624,
                    "createdAt": "2009-02-23T21:58:56.739Z",
                    "bio": "",
                }
            }
        }
    })
    info = extract(body)
    assert info.get('fullname') == 'Eliezer Yudkowsky'
    assert info.get('username') == 'eliezer_yudkowsky'
    assert info.get('karma') == '159624'
    assert info.get('created_at') == '2009-02-23T21:58:56.739Z'


def test_lesswrong_graphql_null_user():
    """Lesswrong GraphQL API: null user returns empty."""
    body = json.dumps({
        "data": {"user": None}
    })
    # Should not match — no "slug" or "karma" flags
    info = extract(body)
    assert not info.get('fullname')


def test_picsart_facebook_uid_from_image():
    """Picsart: extract facebook_uid from graph.facebook.com avatar URL."""
    body = json.dumps({
        "id": 12345,
        "username": "testuser",
        "name": "Test User",
        "photo": "https://graph.facebook.com/231008367325211/picture?type=normal",
        "status_message": "Hello",
        "followers_count": 10,
        "following_count": 5,
        "likes_count": 100,
        "photos_count": 50,
        "is_verified": False,
        "remix_score": 0,
        "dashboard_visibility": True,
    })
    info = extract(body)
    assert info.get('facebook_uid') == '231008367325211'
    assert info.get('picsart_id') == '12345'


def test_picsart_no_facebook_uid_for_regular_avatar():
    """Picsart: no facebook_uid when avatar is not from graph.facebook.com."""
    body = json.dumps({
        "id": 99,
        "username": "other",
        "name": "Other",
        "photo": "https://cdn.picsart.com/avatars/photo.jpg",
        "remix_score": 0,
        "dashboard_visibility": True,
    })
    info = extract(body)
    assert not info.get('facebook_uid')
    assert info.get('picsart_id') == '99'


def test_habr_og_profile():
    """Habr: extract fullname and username from og:title meta tag."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:site_name" content="Хабр">'
        '<meta property="og:title" content="Олег Бунин aka olegbunin\n     - ">'
        '<meta property="og:url" content="https://habr.com/ru/users/olegbunin/">'
        '</head><body></body></html>'
    )
    info = extract(html)
    assert info.get('fullname') == 'Олег Бунин'
    assert info.get('username') == 'olegbunin'
    assert 'habr.com' in info.get('website', '')


def test_product_hunt_og_profile():
    """Product Hunt: extract twitter_username and username from meta tags."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:site_name" content="Product Hunt">'
        '<meta property="og:type" content="profile">'
        '<meta name="twitter:creator" content="@rrhoover">'
        '<meta property="og:url" content="https://www.producthunt.com/@rrhoover">'
        '</head><body></body></html>'
    )
    info = extract(html)
    assert info.get('twitter_username') == 'rrhoover'
    assert info.get('username') == 'rrhoover'


def test_taplink_og_profile():
    """Taplink: extract username, fullname and avatar from og:meta tags."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:image" content="https://taplink.st/a/0/5/e/e/c325e9.jpg?1">'
        '<meta property="og:type" content=website />'
        '<meta property="og:title" content="Selenagomez at Taplink"/>'
        '<meta property="og:url" content="https://taplink.cc/selenagomez"/>'
        '<meta property="og:site_name" content="Taplink"/>'
        '</head><body></body></html>'
    )
    info = extract(html)
    assert info.get('fullname') == 'Selenagomez'
    assert info.get('username') == 'selenagomez'
    assert 'taplink.st' in info.get('image', '')


def test_taplink_nonexistent_user_not_matched():
    """Taplink: homepage (redirect for non-existent user) should NOT match."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:title" content="Taplink - landing page that drives your sales on Instagram">'
        '<meta property="og:url" content="https://taplink.at/en/">'
        '<meta property="og:site_name" content="Taplink">'
        '</head><body></body></html>'
    )
    info = extract(html)
    # Should not match Taplink scheme — no "at Taplink" in og:title
    assert not info.get('username')


def test_threads_profile():
    """Threads: extract from OG tags with HTML entities (real SPA response format)."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:title" content="Marc Fuste&#xe9; (&#064;fusteee) &#x2022; Threads, Say more">'
        '<meta property="og:description" content="33 Followers &#x2022; 0 Threads &#x2022; &quot;Regalame tus mejores noches&quot;. See the latest conversations with &#064;fusteee.">'
        '</head><body>'
        '<div class="barcelona">content</div>'
        '</body></html>'
    )
    info = extract(html)
    assert info.get('username') == 'fusteee'
    assert info.get('fullname') == 'Marc Fuste&#xe9;'
    assert info.get('follower_count') == '33'
    assert info.get('posts_count') == '0'
    assert info.get('bio') == 'Regalame tus mejores noches'


def test_chess_com_html_profile():
    """Chess.com HTML: extract fullname, username and image from og:meta."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:title" content="John (John) - Chess Profile">'
        '<meta property="og:url" content="https://www.chess.com/member/john">'
        '<meta property="og:site_name" content="Chess.com">'
        '<meta property="og:image" content="https://www.chess.com/share/user/john">'
        '</head><body></body></html>'
    )
    info = extract(html)
    assert info.get('fullname') == 'John'
    assert info.get('username') == 'John'
    assert info.get('image') == 'https://www.chess.com/share/user/john'


def test_roblox_html_profile():
    """Roblox HTML: extract username, uid and avatar from og:meta after redirect."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta property="og:site_name" content="Roblox">'
        '<meta property="og:title" content="john&#x27;s Profile">'
        '<meta property="og:type" content="profile">'
        '<meta property="og:url" content="https://www.roblox.com/users/2191/profile">'
        '<meta property="og:image" content="https://tr.rbxcdn.com/30DAY-Avatar-A852E46C43BF1A5E01BD1FDA883FD398-Png/352/352/Avatar/Png/noFilter">'
        '</head><body></body></html>'
    )
    info = extract(html)
    assert info.get('username') == 'john'
    assert info.get('uid') == '2191'
    assert 'rbxcdn.com' in info.get('image', '')


def test_stack_exchange_api_json():
    """Stack Exchange API: extract user profile from /users?inname= JSON response."""
    body = json.dumps({
        "items": [{
            "account_id": 21543594,
            "reputation": 1,
            "user_id": 15880884,
            "user_type": "registered",
            "link": "https://stackoverflow.com/users/15880884/soxoj1",
            "profile_image": "https://www.gravatar.com/avatar/86d899547a5fce05b6a63e540878c69f",
            "display_name": "Soxoj1",
            "creation_date": 1620592473,
        }],
        "has_more": False,
    })
    info = extract(body)
    assert info.get('uid') == '15880884'
    assert info.get('account_id') == '21543594'
    assert info.get('username') == 'Soxoj1'
    assert 'gravatar.com' in info.get('image', '')
    assert info.get('reputation') == '1'
    assert info.get('link') == 'https://stackoverflow.com/users/15880884/soxoj1'
    assert info.get('created_at') == '1620592473'


def test_stack_exchange_api_empty_items():
    """Stack Exchange API: empty items array should not match."""
    body = json.dumps({"items": [], "has_more": False})
    info = extract(body)
    assert not info.get('uid')


def test_leetcode_graphql_api_json():
    """LeetCode GraphQL: extract user profile from matchedUser response."""
    body = json.dumps({
        "data": {
            "matchedUser": {
                "username": "soxoj",
                "profile": {
                    "realName": "Soxoj",
                    "aboutMe": "OSINT researcher",
                    "userAvatar": "https://assets.leetcode.com/users/soxoj/avatar_1561894548.png",
                    "countryName": "Russia",
                    "company": "Anthropic",
                    "school": "MIT",
                    "ranking": 5000001,
                },
            }
        }
    })
    info = extract(body)
    assert info.get('username') == 'soxoj'
    assert info.get('fullname') == 'Soxoj'
    assert info.get('bio') == 'OSINT researcher'
    assert 'leetcode.com' in info.get('image', '')
    assert info.get('country') == 'Russia'
    assert info.get('company') == 'Anthropic'
    assert info.get('school') == 'MIT'
    assert info.get('ranking') == '5000001'


def test_leetcode_graphql_empty_profile():
    """LeetCode GraphQL: empty realName/aboutMe should return None, not empty string."""
    body = json.dumps({
        "data": {
            "matchedUser": {
                "username": "emptyuser",
                "profile": {
                    "realName": "",
                    "aboutMe": "",
                    "userAvatar": "https://assets.leetcode.com/users/default.png",
                    "countryName": None,
                    "company": None,
                    "school": None,
                    "ranking": 999999,
                },
            }
        }
    })
    info = extract(body)
    assert info.get('username') == 'emptyuser'
    assert not info.get('fullname')
    assert not info.get('bio')
    assert not info.get('country')
    assert not info.get('company')


def test_boosty_api_json():
    """Boosty API: extract blog owner profile with telegram crosslink."""
    body = json.dumps({
        "id": 123,
        "title": "Организуем митапы",
        "description": "Канал про митапы",
        "owner": {
            "name": "OSINT mindset",
            "id": 10276482,
            "avatarUrl": "https://images.boosty.to/user/10276482/avatar",
            "externalApps": {
                "telegram": {"username": "soxoj", "hasAccount": True},
            },
        },
        "signedQuery": "abc123",
    })
    info = extract(body)
    assert info.get('uid') == '10276482'
    assert info.get('fullname') == 'OSINT mindset'
    assert 'boosty.to' in info.get('image', '')
    assert info.get('blog_title') == 'Организуем митапы'
    assert info.get('blog_description') == 'Канал про митапы'
    assert info.get('telegram_username') == 'soxoj'


def test_boosty_api_no_telegram():
    """Boosty API: missing telegram should return None, not crash."""
    body = json.dumps({
        "id": 456,
        "title": "Some Blog",
        "description": "",
        "owner": {
            "name": "Author",
            "id": 999,
            "avatarUrl": "https://images.boosty.to/user/999/avatar",
            "externalApps": {},
        },
        "signedQuery": "xyz",
    })
    info = extract(body)
    assert info.get('uid') == '999'
    assert info.get('fullname') == 'Author'
    assert not info.get('telegram_username')


def test_facebook_user_profile_meta_tags():
    """
    Verifies the **Facebook user profile** scheme extracts data from OG and app-link
    meta tags (the format served to crawlers by Facebook).

    **Check:** `uid`, `username`, `fullname`, `description`, and `image` are extracted
    from the meta tags in the HTML fixture.
    """
    html = (
        '<!DOCTYPE html>'
        '<html id="facebook" class="_9dls" lang="en" dir="ltr"><head>'
        '<title>Mark Zuckerberg</title>'
        '<meta property="al:android:app_name" content="Facebook" />'
        '<meta property="al:android:url" content="fb://profile/4" />'
        '<meta property="og:title" content="Mark Zuckerberg" />'
        '<meta property="og:description" content="Mark Zuckerberg. 121,000,000 likes" />'
        '<meta property="og:url" content="https://www.facebook.com/zuck/" />'
        '<meta property="og:image" content="https://lookaside.fbsbx.com/lookaside/crawler/media/?media_id=4" />'
        '</head><body></body></html>'
    )
    info = extract(html)
    assert info.get('uid') == '4'
    assert info.get('username') == 'zuck'
    assert info.get('fullname') == 'Mark Zuckerberg'
    assert 'likes' in info.get('description', '')
    assert 'lookaside' in info.get('image', '')


def test_facebook_user_profile_no_match_without_og_title():
    """
    Verifies the **Facebook user profile** scheme does NOT match pages that lack
    ``og:title`` meta tag (e.g. login/error pages).
    """
    html = (
        '<!DOCTYPE html>'
        '<html id="facebook" lang="en"><head>'
        '<title>Error</title>'
        '</head><body><h1>Sorry, something went wrong.</h1></body></html>'
    )
    info = extract(html)
    assert not info.get('uid')
    assert not info.get('fullname')


def test_smule_profile_extraction():
    """
    Verifies the **Smule** scheme extracts user data from the inline
    ``Profile: {"user": ...}`` JSON block found in Smule profile pages.
    """
    user_data = {
        "user": {
            "account_id": 173,
            "handle": "Blue",
            "pic_url": "https://c-sf.smule.com/rs-z0/account/icon/v4_defpic.png",
            "url": "/Blue",
            "followers": "155",
            "followees": "0",
            "num_performances": "0",
            "is_following": False,
        }
    }
    html = (
        '<!DOCTYPE html><html><head>'
        '<title>Blue on Smule</title>'
        '</head><body>'
        '<script>smule.com Profile: ' + json.dumps(user_data) + '\n</script>'
        '</body></html>'
    )
    info = extract(html)
    assert info.get('uid') == '173'
    assert info.get('username') == 'Blue'
    assert info.get('image') == 'https://c-sf.smule.com/rs-z0/account/icon/v4_defpic.png'
    assert info.get('follower_count') == '155'
    assert info.get('following_count') == '0'
