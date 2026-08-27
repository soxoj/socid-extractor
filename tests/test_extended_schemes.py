# -*- coding: utf-8 -*-
"""Offline tests for schemes merged in from the extended plugin pack."""
import json

from socid_extractor.main import extract


def test_gdbrowser_api_json():
    """GDBrowser API: extract Geometry Dash profile with social crosslinks."""
    body = json.dumps({
        "username": "RobTop",
        "playerID": "71",
        "accountID": "16",
        "rank": 1,
        "stars": 5000,
        "userCoins": 100,
        "youtube": "robtopgames",
        "twitter": "RobTopGames",
        "twitch": "robtopgames",
        "discord": None,
        "instagram": None,
        "tiktok": None,
        "customLink": None,
    })
    info = extract(body)
    assert info.get('username') == 'RobTop'
    assert info.get('uid') == '71'
    assert info.get('gd_account_id') == '16'
    assert info.get('youtube_username') == 'robtopgames'
    assert info.get('twitter_username') == 'RobTopGames'
    assert info.get('twitch_username') == 'robtopgames'
    assert info.get('discord_username') is None
    assert info.get('instagram_username') is None


def test_streamelements_api_json():
    """StreamElements API: extract channel with provider crosslink."""
    body = json.dumps({
        "_id": "5b02f77a398dff6c3fbd887d",
        "username": "teststreamer",
        "displayName": "Test Streamer",
        "avatar": "https://yt3.ggpht.com/avatar.jpg",
        "provider": "youtube",
        "providerId": "UC_j3Wd_7i1mgyoxnU7_yFfg",
        "broadcasterType": "",
        "isPartner": False,
        "suspended": False,
        "inactive": False,
        "profile": {"social": {}},
    })
    info = extract(body)
    assert info.get('uid') == '5b02f77a398dff6c3fbd887d'
    assert info.get('username') == 'teststreamer'
    assert info.get('fullname') == 'Test Streamer'
    assert info.get('provider') == 'youtube'
    assert info.get('provider_id') == 'UC_j3Wd_7i1mgyoxnU7_yFfg'
    assert info.get('is_partner') == 'False'


def test_streamlabs_api_json():
    """Streamlabs API: extract user with primary account crosslink."""
    body = json.dumps({
        "id": 4350278,
        "primary_account": {
            "type": "youtube_account",
            "id": "UCzzotlhxYmISG-HUidWa8VA",
            "username": "TestChannel",
        },
        "partnered": None,
        "logo": "https://yt3.ggpht.com/logo.jpg",
        "token": "abc123",
        "domain": None,
        "ab_test_group": "B",
    })
    info = extract(body)
    assert info.get('uid') == '4350278'
    assert info.get('image') == 'https://yt3.ggpht.com/logo.jpg'
    assert info.get('primary_account_type') == 'youtube_account'
    assert info.get('primary_account_id') == 'UCzzotlhxYmISG-HUidWa8VA'
    assert info.get('primary_account_username') == 'TestChannel'


def test_donatty_api_json():
    """Donatty API: extract user with Twitch crosslink."""
    body = json.dumps({
        "response": {
            "refId": "4a2ff929-d298-4e12-9fe9-b5b462002222",
            "name": "teststreamer",
            "displayName": "Test_Streamer",
            "picture": {"source": "https://static-cdn.jtvnw.net/avatar.png"},
            "registrationDate": "2025-03-12T17:54:26Z",
            "twitch": {"rewards": [], "url": "https://www.twitch.tv/test_streamer"},
            "favicon": {"source": "https://storage.donatty.com/favicon.ico"},
            "status": {"isBlocked": False},
        }
    })
    info = extract(body)
    assert info.get('uid') == '4a2ff929-d298-4e12-9fe9-b5b462002222'
    assert info.get('username') == 'teststreamer'
    assert info.get('fullname') == 'Test_Streamer'
    assert 'jtvnw.net' in info.get('image', '')
    assert info.get('created_at') == '2025-03-12T17:54:26Z'
    assert info.get('twitch_url') == 'https://www.twitch.tv/test_streamer'


def test_visnesscard_api_json():
    """VisnessCard API: extract digital business card with PII."""
    body = json.dumps({
        "active": False,
        "card_id": 6700,
        "end_point": "TESTUSER",
        "first_name": "JOHN",
        "last_name": "SMITH",
        "company_name": "ACME INC",
        "email": "john@example.com",
        "address": "123 Main St",
        "suite": "Apt 4B",
        "city": "Springfield",
        "state": "IL",
        "zip": "62701",
        "business_title": "CEO",
        "company_website_1": "https://acme.example.com",
        "company_website_2": "",
        "views": 42,
        "unique_views": 30,
        "android_icon_key": "https://s3.amazonaws.com/pro-visnesscard/logo.png",
        "icons": [{"image_key": "https://s3.amazonaws.com/pro-visnesscard/icon.png"}],
        "date_created": "2021-04-08T20:24:43.823",
    })
    info = extract(body)
    assert info.get('uid') == '6700'
    assert info.get('username') == 'TESTUSER'
    assert info.get('fullname') == 'JOHN SMITH'
    assert info.get('email') == 'john@example.com'
    assert info.get('company') == 'ACME INC'
    assert info.get('business_title') == 'CEO'
    assert '123 Main St' in info.get('location', '')
    assert 'Apt 4B' in info.get('location', '')
    assert 'Springfield' in info.get('location', '')
    assert info.get('website') == 'https://acme.example.com'
    assert 'icon.png' in info.get('image', '')
    assert info.get('views_count') == '30'
    assert info.get('created_at') == '2021-04-08T20:24:43.823'
