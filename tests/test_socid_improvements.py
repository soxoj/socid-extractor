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
        'status': 'success',
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
