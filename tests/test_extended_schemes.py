# -*- coding: utf-8 -*-
"""Offline tests for schemes merged in from the extended plugin pack."""
import json
from pathlib import Path

import pytest

from socid_extractor.main import extract, mutate_url


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


def test_vbulletin_v4_profile_identifiers():
    """vBulletin 4 profile pages expose id in RELPATH and username in the header."""
    html = '''
    <meta name="generator" content="vBulletin 4.2.5">
    <script>var RELPATH = "member.php?u=144363";</script>
    <div id="memberinfoheader">
      <a class="avatar" href="member.php?u=144363&amp;s=session">
        <span class="avatarcontainer"><img src="avatar.png"></span>
      </a>
      <div id="userinfo"><span class="member_username">Adam</span></div>
    </div>
    <a class="username" href="member.php?u=60945">visitor</a>
    '''
    info = extract(html)
    assert info.get('uid') == '144363'
    assert info.get('username') == 'Adam'
    assert info.get('image') == 'avatar.png'


def test_vbulletin_v3_profile_identifiers():
    """vBulletin 3 profile pages expose the id in finduser links."""
    html = '''
    <meta name="generator" content="vBulletin 3.8.8">
    <div id="username_box"><h1>Alex <img src="offline.gif"></h1></div>
    <div id="stats"><a href="search.php?do=finduser&amp;u=106">Find posts</a>
      <a href="search.php?do=finduser&amp;u=106&amp;starteronly=1">Find threads</a></div>
    '''
    info = extract(html)
    assert info.get('uid') == '106'
    assert info.get('username') == 'Alex'


def test_vbulletin_thread_with_multiple_participants_has_no_profile_id():
    """A thread with several participant ids must not identify one as the profile."""
    html = '''
    <meta name="generator" content="vBulletin 4.2.5">
    <a href="search.php?do=finduser&amp;u=106">Alex</a>
    <a href="search.php?do=finduser&amp;u=2835">Snejana191</a>
    '''
    info = extract(html)
    assert 'uid' not in info


def test_nodebb_api_json():
    """NodeBB API: extract a saved response without making a request."""
    # Captured 2026-09-13 from the public endpoint in issue #291:
    # https://bbs.aw-ol.com/api/user/username/whycan
    body = (Path(__file__).parent / 'fixtures' / 'nodebb_user.json').read_text(encoding='utf-8')
    info = extract(body)
    assert info.get('_extractor') == 'NodeBB API'
    assert info.get('uid') == '44'
    assert info.get('username') == 'whycan'
    assert info.get('fullname') == 'whycan晕哥'
    assert info.get('image') == '/assets/uploads/profile/44-profileavatar-1680058994111.jpeg'
    assert info.get('created_at') == '2021-05-17 15:16:25.374 UTC'
    assert info.get('latest_activity_at') == '2026-09-07 23:37:21.034 UTC'
    assert info.get('posts_count') == '2104'
    assert info.get('follower_count') == '76'
    assert info.get('following_count') == '0'


def test_nodebb_api_missing_optional_fields():
    body = json.dumps({
        'uid': 7, 'username': 'example', 'userslug': 'example',
        'joindate': None, 'lastonline': 0, 'postcount': 0,
        'icon:bgColor': '#009688', 'email:confirmed': False,
    })
    info = extract(body)
    assert info.get('uid') == '7'
    assert info.get('username') == 'example'
    assert info.get('posts_count') == '0'
    assert 'created_at' not in info
    assert 'latest_activity_at' not in info
    assert 'image' not in info


@pytest.mark.parametrize('body', [
    '{"status":{"code":"not-authorised","message":"Not authorised"}}',
    '{"error":"Forbidden"}',
    '<html><title>401 Unauthorized</title></html>',
    '<html><title>404 Not Found</title></html>',
    '{}',
    # Platform markers in a nested user/list do not identify a profile page.
    '{"users":[{"uid":7,"username":"example","userslug":"example",'
    '"joindate":1621264585374,"postcount":0,"icon:bgColor":"#009688","email:confirmed":false}]}',
    '{"userslug":"example","joindate":1621264585374,"postcount":0,'
    '"icon:bgColor":"#009688","email:confirmed":false}',
    '{"userslug":"example","joindate":1621264585374,"postcount":0,'
    '"icon:bgColor":"#009688","email:confirmed":false,}',
    # Other APIs can have usernames and post counts, without being NodeBB.
    '{"id":7,"username":"example","postcount":12}',
    '{"uid":7,"username":"example","userslug":"example","joindate":1621264585374}',
])
def test_nodebb_api_ignores_errors_and_unrelated_responses(body):
    assert extract(body) == {}


@pytest.mark.parametrize(('profile', 'api'), [
    ('https://forum.example/user/alice', 'https://forum.example/api/user/alice'),
    ('http://forum.example/user/alice/', 'http://forum.example/api/user/alice'),
    ('https://forum.example/community/user/alice-smith', 'https://forum.example/community/api/user/alice-smith'),
    ('https://forum.example/user/alice/posts?sort=newest#top', 'https://forum.example/api/user/alice'),
    ('https://forum.example/user/%E7%94%A8%E6%88%B7?lang=en', 'https://forum.example/api/user/%E7%94%A8%E6%88%B7'),
])
def test_nodebb_profile_url_mutation(profile, api):
    assert (api, set()) in mutate_url(profile)


@pytest.mark.parametrize('url', [
    'https://forum.example/api/user/alice',
    'https://forum.example/api/user/username/alice',
    'https://forum.example/community/api/user/alice',
    'https://forum.example/user/',
])
def test_nodebb_api_url_is_not_mutated_again(url):
    assert not any('/api/api/' in result or '/api/user/' in result for result, _ in mutate_url(url))


# phpBB fixtures are the relevant blocks of real pages, markup intact (tabs as spaces): the
# member list of forums.mozfr.org filtered by name, author searches on
# forum.scssoft.com (phpBB 3.3) and jeepspb.ru (phpBB 3.0), and the profile
# page of forums.mozfr.org. Every phpBB page carries the two flags the scheme
# keys on: the prosilver body id and a link to some member's profile.
PHPBB_BODY = '<body id="phpbb" class="nojs notouch section-memberlist ltr ">'

PHPBB_MEMBER_LIST = PHPBB_BODY + """
<table class="table1 memberlist" id="memberlist">
        <thead>
        <tr>
            <th class="name" data-dfn="Rang, Nom d’utilisateur"><span class="rank-img"><a href="./memberlist.php?username=geckozonefr&amp;mode=&amp;sid=af694c2f2629dd7ee97103fc1e7f3d28&amp;sk=m&amp;sd=d">Rang</a></span><a href="./memberlist.php?username=geckozonefr&amp;mode=&amp;sid=af694c2f2629dd7ee97103fc1e7f3d28&amp;sk=a&amp;sd=a">Nom d’utilisateur</a></th>
            <th class="posts"><a href="./memberlist.php?username=geckozonefr&amp;mode=&amp;sid=af694c2f2629dd7ee97103fc1e7f3d28&amp;sk=d&amp;sd=d#memberlist">Messages</a></th>
            <th class="info"></th>
            <th class="joined"><a href="./memberlist.php?username=geckozonefr&amp;mode=&amp;sid=af694c2f2629dd7ee97103fc1e7f3d28&amp;sk=c&amp;sd=d#memberlist">Inscription</a></th>
                                </tr>
        </thead>
        <tbody>

    <tr class="bg1">
        <td><span class="rank-img">Arias</span><a href="./memberlist.php?mode=viewprofile&amp;u=2&amp;sid=af694c2f2629dd7ee97103fc1e7f3d28" class="username">geckozonefr</a></td>
        <td class="posts"><a href="./search.php?author_id=2&amp;sr=posts&amp;sid=af694c2f2629dd7ee97103fc1e7f3d28" title="Rechercher les messages de l’utilisateur">4</a></td>
        <td class="info">&nbsp;</td>
        <td>10 juin 2003, 14:58</td>
                    </tr>
            </tbody>
    </table>
"""

PHPBB_SEARCH_POST = """<dl class="postprofile">
                        <dt class="author">by <a href="./memberlist.php?mode=viewprofile&amp;u=142&amp;sid=59ee3f2280248ea8f2d475af74b98e18" class="username">John</a></dt>
            <dd class="search-result-date">09 May 2020 10:21</dd>
            <dd>Forum: <a href="./viewforum.php?f=47&amp;sid=59ee3f2280248ea8f2d475af74b98e18">Screenshots</a></dd>
            <dd>Topic: <a href="./viewtopic.php?t=283868&amp;sid=59ee3f2280248ea8f2d475af74b98e18">Sam's Travels</a></dd>
                        <dd>Replies: <strong>12</strong></dd>
            <dd>Views: <strong>1484</strong></dd>
                    </dl>
"""

PHPBB_PROFILE = PHPBB_BODY + """
<h2 class="memberlist-title">Consulte le profil de geckozonefr</h2>
<div class="panel bg1">
    <div class="inner">


    <dl class="left-box details profile-details">
        <dt>Nom d’utilisateur :</dt>
        <dd>
            <span>geckozonefr</span>                                                        </dd>
                                <dt>Rang :</dt> <dd>Arias</dd>                                                        <dt>Groupes :</dt> <dd><select name="g"><option value="18190" selected="selected">Utilisateurs inscrits</option></select> <input type="submit" name="submit" value="Aller" class="button2" /></dd>                                                    </dl>
    </div>
</div>
<div class="panel bg2">
    <div class="inner">
    <dl class="details">
                        <dt>Inscription :</dt> <dd>10 juin 2003, 14:58</dd>
            <dt>Dernière visite :</dt> <dd>07 avr. 2004, 22:23</dd>
                        <dt>Nombre total de messages :</dt>
                <dd>4 | <strong><a href="./search.php?author_id=2&amp;sr=posts&amp;sid=8708b55892d0a9e904900209167bdeef">Rechercher les messages de l’utilisateur</a></strong>                    <br />(0.00 % de tous les messages / 0.00 messages par jour)                                    </dd>
                                </dl>
    </div>
</div>
<a href="./ucp.php?i=pm&amp;mode=compose&amp;u=2&amp;sid=8708b55892d0a9e904900209167bdeef" title="Envoyer un message privé">Envoyer un message privé</a>
<a href="./memberlist.php?mode=viewprofile&amp;u=2&amp;sid=8708b55892d0a9e904900209167bdeef">geckozonefr</a>
"""


def test_phpbb_member_list():
    """phpBB: the member list filtered by name answers with the one row that matches."""
    info = extract(PHPBB_MEMBER_LIST)

    assert info.get('_extractor') == 'phpBB'
    assert info.get('uid') == '2'
    assert info.get('username') == 'geckozonefr'
    assert info.get('posts_count') == '4'
    # the join date comes as the board renders it, in its own language
    assert info.get('created_at') == '10 juin 2003, 14:58'
    assert 'website' not in info

    # a row with a website and a grouped post count, coloured username (vw-bus.ru)
    row = ('<tr class="bg1">\n\t\t<td><span class="rank-img">Партнер Клуба</span>'
           '<a href="./memberlist.php?mode=viewprofile&amp;u=171&amp;sid=0942ed1bf9930b297032bace8805ab4f" '
           'style="color: #66CC00;" class="username-coloured">Alex</a></td>\n'
           '\t\t<td class="posts">1 396</td>\n'
           '\t\t<td class="info"><div><!-- m --><a class="postlink" href="https://www.nemanauto.com/">https://www.nemanauto.com/</a><!-- m --></div></td>\n'
           '\t\t<td>13.10.2006, 13:24:25</td>\n\t\t\t\t\t</tr>')
    info = extract(PHPBB_BODY + '<table class="table1 memberlist" id="memberlist"><tbody>' + row + '</tbody></table>')

    assert info.get('uid') == '171'
    assert info.get('username') == 'Alex'
    assert info.get('posts_count') == '1396'
    assert info.get('created_at') == '13.10.2006, 13:24:25'
    assert info.get('website') == 'https://www.nemanauto.com/'


def test_phpbb_author_search():
    """phpBB: an author search is headed by the same member on every post, and carries nothing else about them."""
    info = extract(PHPBB_BODY + PHPBB_SEARCH_POST + PHPBB_SEARCH_POST.replace('283868', '284658'))

    assert info.get('_extractor') == 'phpBB'
    assert info.get('uid') == '142'
    assert info.get('username') == 'John'
    assert 'posts_count' not in info
    assert 'created_at' not in info

    # phpBB 3.0 writes the header without "by" and without a class on the link
    info = extract(PHPBB_BODY + """<dl class="postprofile">
            <dt class="author"> <a href="./memberlist.php?mode=viewprofile&amp;u=2965&amp;sid=3a6895e9cdd8dc41bbe8501f3c768970">Red</a></dt>
            <dd>23 ноя 2014, 18:31</dd>
            <dd>&nbsp;</dd>

                <dd>Форум: <a href="./viewforum.php?f=3&amp;sid=3a6895e9cdd8dc41bbe8501f3c768970">Разборка - продам, подарю </a></dd>
                <dd>Тема: <a href="./viewtopic.php?f=3&amp;t=8093&amp;sid=3a6895e9cdd8dc41bbe8501f3c768970">комплект резины cooper st 30&quot;x9.5</a></dd>

            <dd>Ответов: <strong>9</strong></dd>
            <dd>Просмотров: <strong>2639</strong></dd>
        </dl>
""")

    assert info.get('uid') == '2965'
    assert info.get('username') == 'Red'

    # a URL-rewriting mod leaves both link forms on one page (4x4.tomsk.ru): the
    # name agrees across posts and the id comes from the posts that still carry it
    rewritten = PHPBB_SEARCH_POST.replace(
        './memberlist.php?mode=viewprofile&amp;u=142&amp;sid=59ee3f2280248ea8f2d475af74b98e18', 'https://forum.example/member142.html')
    info = extract(PHPBB_BODY + rewritten + PHPBB_SEARCH_POST)

    assert info.get('uid') == '142'
    assert info.get('username') == 'John'

    # a post whose author has no profile link names them but gives no id
    guest = PHPBB_SEARCH_POST.replace(
        'by <a href="./memberlist.php?mode=viewprofile&amp;u=142&amp;sid=59ee3f2280248ea8f2d475af74b98e18" class="username">John</a>',
        '<span> John</span>')
    assert extract(PHPBB_BODY + '<a href="./memberlist.php?mode=viewprofile&amp;u=1">Team</a>' + guest) == {}


def test_phpbb_profile_page():
    """phpBB: the profile names its owner first and carries the id in the search link."""
    info = extract(PHPBB_PROFILE)

    assert info.get('_extractor') == 'phpBB'
    assert info.get('uid') == '2'
    assert info.get('username') == 'geckozonefr'
    assert info.get('created_at') == '10 juin 2003, 14:58'
    assert info.get('posts_count') == '4'


def test_phpbb_ignores_pages_about_other_people():
    """A page with several members on it is a listing, not an answer about one of them."""
    # a keyword search lists posts by everyone
    search = PHPBB_BODY + PHPBB_SEARCH_POST + PHPBB_SEARCH_POST.replace('u=142', 'u=20027').replace('John', 'Jan_J')
    assert extract(search) == {}

    # an unfiltered member list is the whole board
    row = PHPBB_MEMBER_LIST[PHPBB_MEMBER_LIST.index('<tr class="bg1">'):PHPBB_MEMBER_LIST.index('</tbody>')]
    listing = PHPBB_MEMBER_LIST.replace(row, row + row.replace('u=2&amp;', 'u=1194&amp;').replace('geckozonefr', 'gecko'))
    assert extract(listing) == {}

    # a name that matches nobody leaves the table without a profile link
    empty = PHPBB_MEMBER_LIST.replace(row, '<tr class="bg1">\n\t\t<td colspan="4">Aucun membre ne correspond à ce critère.</td>\n\t</tr>\n')
    assert extract(empty) == {}

    # the login wall echoes the profile URL back in its redirect, which names nobody
    wall = (PHPBB_BODY + '<h2 class="login-title">The board requires you to be registered and logged in to view profiles.</h2>'
            '<input type="hidden" name="redirect" value="./memberlist.php?mode=viewprofile&amp;u=1743&amp;sid=567f6e931545fafe7608ab2f5c759534" />')
    assert extract(wall) == {}
