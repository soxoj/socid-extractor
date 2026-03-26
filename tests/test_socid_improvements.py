# -*- coding: utf-8 -*-
"""
Regression and unit-style checks for Maigret / LLM improvement log items.

Each test documents *what* is verified (see docstrings on test functions and assertion comments).
"""
import json

from socid_extractor.main import extract
from socid_extractor.postprocessor import Gravatar, StripInvalidGravatarUrls
from socid_extractor.utils import imgur_profile_avatar_url, is_bare_gravatar_root_url, is_valid_gravatar_email_hash


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


def test_xvideos_profile_id_user_regex():
    """XVideos profile page JSON fragment with id_user + username."""
    html = (
        '<html lang="en" class="xv-responsive"><body>'
        '<a href="https://www.xvideos.com/profiles/xvideos">p</a>'
        '"id_user":1356961,"username":"xvideos","display":"Xvideos"'
        '</body></html>'
    )
    info = extract(html)
    assert info.get('xvideos_user_id') == '1356961'
    assert info.get('xvideos_username') == 'xvideos'


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
