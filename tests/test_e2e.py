#!/usr/bin/env python3
import pytest

from socid_extractor.activation import get_twitter_headers
from socid_extractor.main import parse, extract, mutate_url, HEADERS


def test_vk_user_profile_full():
    """VK user profile"""
    info = extract(parse('https://vk.com/idsvyatoslavs')[0])

    assert info.get('vk_id') == '134173165'
    assert info.get('vk_username') == 'idsvyatoslavs'
    assert info.get('fullname') in ('Святослав Степанов', 'Svyatoslav Stepanov')


def test_vk_user_profile_no_username():
    """
    VK user profile
    VK user profile foaf page
    """
    info = extract(parse('https://vk.com/id568161939')[0])

    assert info.get('vk_id') == '568161939'
    assert info.get('vk_username') is None
    assert info.get('fullname') in ('Юля Заболотная', 'Yulya Zabolotnaya')


def test_vk_closed_user_profile():
    """VK user profile"""
    info = extract(parse('https://vk.com/alex')[0])

    assert info.get('fullname') in ('Александр Чудаев', 'Alexander Chudaev')


def test_vk_blocked_user_profile():
    """VK user profile"""
    headers = {'User-Agent': 'Curl'}
    info = extract(parse('https://vk.com/alexaimephotography', headers=headers)[0])

    assert info.get('fullname') in ('Alex Aimé', 'Alex Aim&#233;')


def test_yandex_disk():
    """Yandex Disk file"""
    info = extract(parse('https://yadi.sk/d/xRJFp3s2QWYv8')[0])

    assert info.get('yandex_uid') == '225171618'
    assert info.get('name') == 'Trapl  Zdenek'


@pytest.mark.rate_limited
def test_yandex_reviews():
    """Yandex Reviews user profile"""
    info = extract(parse('https://reviews.yandex.ru/user/1a7dv00dqrdgjf6qkyn8kw37jw')[0])

    assert info.get('yandex_public_id') == '1a7dv00dqrdgjf6qkyn8kw37jw'
    assert info.get('fullname') == 'Darya Gindina'
    assert info.get('image') == 'https://avatars.mds.yandex.net/get-yapic/59871/oLXpnRHSVknK56vRAYx2Iuya6U-1/islands-200'
    assert info.get('is_verified') == 'False'
    assert info.get('reviews_count') == '1'
    assert info.get('following_count') == '0'
    assert info.get('follower_count') == '0'


@pytest.mark.github_failed
def test_instagram():
    """
    Instagram
    Instagram page JSON
    """
    URLs = [
        'https://www.instagram.com/zhanna/',
        'https://www.instagram.com/zhanna/?__a=1',
    ]
    for url in URLs:
        info = extract(parse(url, headers=HEADERS)[0])
        print(info)

        assert info.get("username") == "zhanna"
        assert info.get("fullname") == "Zhanna Shamis"
        assert info.get("id") == "105153"
        assert info.get("image") == "https://scontent-hel3-1.cdninstagram.com/v/t51.2885-19/11375383_434870180034484_1429353554_a.jpg?_nc_ht=scontent-hel3-1.cdninstagram.com&_nc_cat=104&_nc_ohc=25Ow2Br6xhwAX-ybdqd&edm=ABfd0MgBAAAA&ccb=7-4&oh=00_AT8c23cG3e2dwhT52s6pARMj_4Jhi9v7UWTt93jFJxNSyA&oe=61DE93D1&_nc_sid=7bff83"
        assert info.get("external_url") == "http://twitter.com/zhanna"
        assert info.get("facebook_uid") == "17841401234590001"
        assert info.get("is_business") == "False"
        assert info.get("is_joined_recently") == "False"
        assert info.get("is_private") == "False"
        assert info.get("is_verified") == "False"
        assert "follower_count" in info
        assert "following_count" in info


@pytest.mark.github_failed
def test_instagram_api():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-A102U Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 Instagram 155.0.0.37.107 Android (28/9; 320dpi; 720x1468; samsung; SM-A102U; a10e; exynos7885; en_US; 239490550)',
    }

    info = extract(parse('https://i.instagram.com/api/v1/users/6828488620/info', headers=headers)[0])

    assert info.get('id') == '6828488620'
    assert info.get('username') == 'alexaimephotography'
    assert 'image' in info


def test_medium():
    info = extract(parse('https://medium.com/@lys1n', timeout=10)[0])

    assert info.get('medium_id') == '4894fec6b289'
    assert info.get('medium_username') == 'lys1n'
    assert info.get('fullname') == 'Марк Лясин'
    # assert info.get('twitter_username') == 'lys1n'
    assert info.get('is_suspended') == 'False'
    assert 'follower_count' in info
    assert 'following_count' in info


def test_odnoklassniki():
    info = extract(parse('https://ok.ru/profile/46054003')[0])

    assert info.get('ok_id') == '46054003'

    info = extract(parse('https://ok.ru/andrey.ostashenya')[0])

    assert info.get('ok_user_name_id') == 'andrey.ostashenya'
    assert info.get('ok_id') == '576861363171'


@pytest.mark.github_failed
def test_habr():
    """Habrahabr JSON"""
    info = extract(parse('https://habr.com/ru/users/m1rko/')[0])

    assert info.get("username") == "m1rko"
    assert info.get("about") == "автор, переводчик, редактор"
    assert info.get("gender") == "0"
    assert info.get("rating") == "0"
    assert info.get("karma") == "1236.5"
    assert info.get("fullname") == "Анатолий Ализар"
    assert info.get("is_readonly") == "False"
    assert info.get("image") == "//habrastorage.org/getpro/habr/avatars/4ec/bd0/85d/4ecbd085d692835a931d03174ff19539.png"

@pytest.mark.github_failed
def test_habr_no_image():
    """Habrahabr JSON"""
    info = extract(parse('https://habr.com/ru/users/ne555/')[0])

    assert info.get('uid') == '1800409'
    assert info.get('username') == 'ne555'
    assert 'image' not in info


@pytest.mark.skip(reason="down")
def test_twitter_shadowban_no_account():
    info = extract(parse('https://shadowban.eu/.api/sgfrgrrr')[0])

    assert info.get('has_tweets') == 'False'
    assert info.get('is_exists') == 'False'
    assert info.get('username') == 'sgfrgrrr'
    assert 'is_protected' not in info
    assert 'has_ban' not in info
    assert 'has_search_ban' not in info
    assert 'has_banned_in_search_suggestions' not in info


@pytest.mark.skip(reason="down")
def test_twitter_shadowban():
    info = extract(parse('https://shadowban.eu/.api/trump')[0])

    assert info.get('has_tweets') == 'True'
    assert info.get('is_exists') == 'True'
    assert info.get('username') == 'Trump'
    assert info.get('is_protected') == 'False'
    assert info.get('has_ban') == 'False'
    assert info.get('has_search_ban') == 'False'
    assert info.get('has_banned_in_search_suggestions') == 'False'


def test_twitter_api():
    _, headers = get_twitter_headers({})
    import logging
    logging.error(headers)
    info = extract(parse('https://twitter.com/i/api/graphql/ZRnOhhXPwue_JGILb9TNug/UserByScreenName?variables=%7B%22screen_name%22%3A%22cardiakflatline%22%2C%22withHighlightedLabel%22%3Atrue%7D', headers=headers)[0])

    assert info.get('uid') == 'VXNlcjo0NTkyNjgxNg=='
    assert info.get('fullname') == 'Cardiak'
    assert info.get('bio') == '#Jersey Multi Platinum Grammy Award Winning Producer for J.Cole, DrDre,KendrickLamar, Eminem,MeekMill,RickRoss,Drake,Wale,Ace Hood,T.I,LloydBanks,Kanye,Fabolous'
    assert info.get('created_at') == '2009-06-09 19:59:57+00:00'
    assert info.get('image') == 'https://pbs.twimg.com/profile_images/745944619213557760/vgapfpjV.jpg'
    assert info.get('image_bg') == 'https://pbs.twimg.com/profile_banners/45926816/1487198278'
    assert info.get('is_protected') == 'False'
    assert info.get('links') == "['http://www.flatlinekits.com']"
    assert info.get('location') == 'Los Angeles, CA'
    assert 'follower_count' in info
    assert 'following_count' in info
    assert 'favourites_count' in info


def test_reddit():
    info = extract(parse('https://www.reddit.com/user/Diascamara/', timeout=10)[0])

    assert info.get('reddit_id') == 't5_a8vxj'
    assert info.get('reddit_username') == 'Diascamara'
    assert info.get('fullname') == 'Diascamara'
    assert info.get('is_employee') == 'False'
    assert info.get('is_nsfw') == 'True'
    assert info.get('is_mod') == 'True'
    assert info.get('is_following') == 'True'
    assert info.get('has_user_profile') == 'True'
    assert info.get('created_at').startswith('2018-01-06')
    assert info.get('hide_from_robots') == 'True'
    assert int(info.get('total_karma')) > int(30000)
    assert int(info.get('post_karma')) > int(7000)


@pytest.mark.github_failed
def test_facebook_user_profile():
    info = extract(parse('https://ru-ru.facebook.com/anatolijsharij/')[0])

    assert info.get('uid') == '1486042157'
    assert info.get('username') == 'anatolijsharij'
    assert info.get('fullname') == 'Анатолий Шарий'
    assert info.get('is_verified') == 'True'
    assert 'image' in info
    assert 'image_bg' in info
    assert 'all' not in info


@pytest.mark.skip(reason="broken")
def test_facebook_group():
    info = extract(parse('https://www.facebook.com/discordapp/')[0])

    assert info.get('uid') == '858412104226521'
    assert info.get('username') == 'discord'
    assert 'all' not in info


def test_github_html():
    info = extract(parse('https://github.com/soxoj')[0])

    assert info.get('uid') == '31013580'
    assert info.get('username') == 'soxoj'


def test_github_api():
    info = extract(parse('https://api.github.com/users/soxoj')[0])

    assert info.get('uid') == '31013580'
    assert info.get('image') == 'https://avatars.githubusercontent.com/u/31013580?v=4'
    assert info.get('created_at') == '2017-08-14T17:03:07Z'
    assert 'follower_count' in info
    assert 'following_count' in info
    assert 'public_gists_count' in info
    assert 'public_repos_count' in info
    assert info.get('bio') == 'dev, infosec, osint'
    assert info.get('blog_url') == 'https://www.patreon.com/soxoj'


def test_yandex_disk_photos():
    info = extract(parse('https://yadi.sk/a/oiySK_wg3Vv5p4')[0])

    assert info.get('yandex_uid') == '38569641'
    assert info.get('name') == 'Вербочка'


def test_my_mail_main():
    info = extract(parse('https://my.mail.ru/mail/zubovo/')[0])

    assert info.get('mail_id') == '13425818'
    assert info.get('mail_uid') == '6667000454247668890'
    # there is no auId
    assert info.get('name') == 'Олег Зубов'
    assert info.get('username') == 'zubovo'
    assert info.get('email') == 'zubovo@mail.ru'
    assert info.get('is_vip') == 'False'
    assert info.get('is_community') == 'False'
    assert info.get('is_video_channel') == 'False'


def test_my_mail_communities():
    # also video, apps, photo
    info = extract(parse('https://my.mail.ru/mail/zubovo/communities/')[0])

    assert info.get('mail_id') == '13425818'
    assert info.get('mail_uid') == '6667000454247668890'
    assert info.get('au_id') == '6667000454247668890'
    assert info.get('name') == 'Олег Зубов'
    assert info.get('username') == 'zubovo'
    assert info.get('email') == 'zubovo@mail.ru'
    assert info.get('is_vip') == 'False'
    assert info.get('is_community') == 'False'
    assert info.get('is_video_channel') == 'False'


@pytest.mark.skip(reason="captcha")
def test_yandex_music_user_profile():
    """Yandex Music AJAX request"""
    headers = {'referer': 'https://music.yandex.ru/users/pritisk/playlists'}
    info = extract(parse('https://music.yandex.ru/handlers/library.jsx?owner=pritisk', headers=headers)[0])

    assert info.get('yandex_uid') == '16480689'
    assert info.get('username') == 'pritisk'
    assert info.get('name') == 'Юрий Притиск'
    assert info.get('image') == 'https://avatars.mds.yandex.net/get-yapic/29310/gK74BTyv8LrLRT0mQFIR2xcWv8-1/islands-200'
    assert info.get('is_verified') == 'False'
    assert info.get('liked_albums') == '0'
    assert info.get('liked_artists') == '0'
    assert info.get('email') == 'pritisk@yandex.ru'


@pytest.mark.skip(reason="failed from github CI infra IPs")
def test_yandex_zen_user_profile():
    info = extract(parse('https://zen.yandex.ru/user/uyawkukxyf60ud6hjrxr2rq130')[0])

    assert info.get('yandex_public_id') == 'uyawkukxyf60ud6hjrxr2rq130'
    assert info.get('fullname') == 'Нина Кравченко'
    assert info.get('image') == 'https://avatars.mds.yandex.net/get-yapic/51169/DKXVQdtL3tZ5cayBXnnicLaKcE-1/islands-200'
    assert info.get('messenger_guid') == 'e4615300-548b-9a46-73cf-527d47fe57ed'
    assert info.get('links') == '[]'
    assert info.get('type') == 'user'
    assert int(info.get('comments_count')) > 20
    assert info.get('status') == 'active'
    assert 'following_count' in info
    assert 'follower_count' in info


def test_yandex_o_user_profile():
    """Yandex O"""
    info = extract(parse('https://o.yandex.ru/profile/9q4zmvn5437umdqqyge3tp3vpr/')[0])

    assert info.get('yandex_public_id') == '9q4zmvn5437umdqqyge3tp3vpr'
    assert info.get('fullname') == 'ТВОЙ-СЕЙФ'
    assert info.get('image') == 'https://avatars.mds.yandex.net/get-yapic/64336/enc-0f3ec480eef5850e5ff4e08522ebb6639b998592a4246af4df656b59d2d95fd8/islands-retina-50'
    assert info.get('score') == 'Ten'


def test_yandex_znatoki_user_profile():
    info = extract(parse('https://yandex.ru/q/profile/zftrw5fzczde6841qgmfn7d2ag/')[0])

    assert info.get('yandex_znatoki_id') == '39eec711-5675-56b1-beb5-a1f393d2ee66'
    assert info.get('bio') == 'Любитель Nike, вебмастер'
    assert info.get('name') == 'Александр Яковлев'
    assert info.get('yandex_uid') == '52839599'
    assert info.get('image') == 'https://avatars.mds.yandex.net/get-yapic/39460/jNPmWopVPkXtTzVHWtuLfPxLq0U-1/islands-200'
    assert info.get('is_org') == 'False'
    assert info.get('is_banned') == 'False'
    assert info.get('is_deleted') == 'False'
    assert info.get('created_at') == '2019-04-08T16:23:37.576163+00:00'
    assert 'last_answer_at' in info
    assert 'rating' in info
    assert info.get('gender') == 'm'
    assert info.get('links') == "['https://nikefans.ru']"
    assert info.get('verified_categories') == "['спорт']"
    assert info.get('is_from_q') == 'False'
    # assert info.get('is_bad_or_shock') == 'False'
    assert info.get('is_excluded_from_rating') == 'False'
    assert info.get('teaser') == 'Люблю Nike, спорт и активный образ жизни. С 2013 года я изучаю все, что связано с брендом Nike, веду блог.'
    assert info.get('facebook_username') == 'nikefansru'
    assert info.get('instagram_username') == 'nike.fans.russia'
    assert info.get('telegram_username') == 'nikefansru'
    assert info.get('vk_username') == 'nikejoy'


@pytest.mark.skip(reason="non-actual, yandex updated bugbounty pages")
def test_yandex_bugbounty():
    info = extract(parse('https://yandex.ru/bugbounty/researchers/canyoutestit/')[0])

    assert info.get('yandex_uid') == '690526182'
    assert info.get('firstname') == 'Артем'
    assert info.get('username') == 'canyoutestit'
    assert info.get('email') == 'artebel@mail.ru'
    assert info.get('url') == 'https://facebook.com/artembelch'

    info = extract(parse('https://yandex.ru/bugbounty/researchers/bdanyok/')[0])
    assert info.get('yandex_uid') == '65212420'
    assert info.get('firstname') == 'Данил'
    assert info.get('username') == 'bdanyok'
    assert info.get('email') == 'bdanyok@yandex.ru'

    info = extract(parse('https://yandex.ru/bugbounty/researchers/t-a-neo/')[0])
    assert info.get('yandex_uid') == '584521278'
    assert info.get('firstname') == 'taneo'
    assert info.get('username') == 't-a-neo'


def test_behance():
    info = extract(parse('https://www.behance.net/patrickseymour', 'gpv=behance.net:profile:appreciated; ilo0=true')[0])

    assert info.get('uid') == '376641'
    assert info.get('fullname') == 'Patrick Seymour'
    assert info.get('last_name') == 'Seymour'
    assert info.get('first_name') == 'Patrick'
    assert info.get('username') == 'patrickseymour'
    assert info.get('is_verified') == 'True'
    assert info.get('bio') == 'False'
    assert info.get('image').startswith('https://mir-s3-cdn-cf.behance.net/user/')
    assert info.get('city') == 'Montreal'
    assert info.get('country') == 'Canada'
    assert info.get('location') == 'Montreal, Quebec, Canada'
    assert info.get('created_at').startswith('2011-03-23')
    assert info.get('occupation') == 'Art director • Illustrator '
    assert info.get('links') == "['http://twitter.com/PatrickSeymour', 'http://facebook.com/patrickseymourillustrateur', 'http://linkedin.com/in/patrick-seymour-70334b2b?trk=hp-identity-photo', 'http://vimeo.com/user9401948', 'http://pinterest.com/patrickseymour', 'http://instagram.com/patrickseymour']"
    assert info.get('twitter_username') == 'PatrickSeymour'
    assert 'comments' in info
    assert 'followers_count' in info
    assert 'following_count' in info
    assert 'profile_views' in info
    assert 'project_views' in info
    assert 'appreciations' in info


@pytest.mark.skip(reason="non-actual, 500px requires POST requests for now")
def test_500px():
    """500px GraphQL API"""
    info = extract(parse('https://api.500px.com/graphql?operationName=ProfileRendererQuery&variables=%7B%22username%22%3A%22the-maksimov%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22105058632482dd2786fd5775745908dc928f537b28e28356b076522757d65c19%22%7D%7D')[0])

    assert info.get('uid') == 'dXJpOm5vZGU6VXNlcjoyMzg5Ng=='
    assert info.get('legacy_id') == '23896'
    assert info.get('username') == 'The-Maksimov'
    assert info.get('name') == 'Maxim Maximov'
    assert info.get('qq_uid') is None
    assert info.get('fb_uid') is None
    assert info.get('instagram_username') == 'the.maksimov'
    assert info.get('twitter_username') == 'The_Maksimov'
    assert info.get('website') == 'www.instagram.com/the.maksimov'
    assert info.get('facebook_link') == 'www.facebook.com/the.maksimov'


def test_google_documents():
    """Google Document API"""
    URL = 'https://docs.google.com/spreadsheets/d/1HtZKMLRXNsZ0HjtBmo0Gi03nUPiJIA4CC4jTYbCAnXw/edit#gid=0'
    info = extract(parse(URL)[0])

    assert info.get('org_name') == 'Gooten'
    assert info.get('mime_type') == 'application/vnd.google-apps.ritz'

    mutated_url = mutate_url(URL)

    assert len(mutated_url) == 1
    url, add_headers = mutated_url[0]

    info = extract(parse(url, headers=add_headers)[0])

    assert info.get("created_at") == "2016-02-16T18:51:52.021Z"
    assert info.get("updated_at") == "2019-10-23T17:15:47.157Z"
    assert info.get("fake_gaia_id") == "08262007110170219638"
    assert info.get("fullname") == "Andy Nied"
    assert info.get("email") == "andy@gooten.com"
    # assert info.get("image") == "https://lh3.googleusercontent.com/a-/AOh14GheZe1CyNa3NeJInWAl70qkip4oJ7qLsD8vDy6X=s64"
    assert info.get("email_username") == "andy"


def test_bitbucket():
    info = extract(parse('https://bitbucket.org/arny/')[0])

    assert info.get('uid') == '57ad342a-ec8f-42cb-af05-98175b72b8db'
    assert info.get('fullname') == 'arny'
    assert info.get('nickname') == 'arny'
    assert info.get('created_at') == '2009-11-23T10:41:04.355755+00:00'
    assert info.get('image') == 'https://bitbucket.org/account/arny/avatar/'
    assert info.get('is_service') == 'False'
    assert info.get('is_active') == 'True'


@pytest.mark.skip(reason="cloudflare")
def test_steam():
    info = extract(parse('https://steamcommunity.com/id/GabrielSantosMariano/')[0])

    assert info.get('uid') == '76561198315585536'
    assert info.get('username') == 'GabrielSantosMariano'
    assert info.get('nickname') == 'Gabriel! Santos, Mariano.'


@pytest.mark.skip(reason="cloudflare")
def test_steam_hidden():
    info = extract(parse('https://steamcommunity.com/id/Elvoc/')[0])

    assert info.get('uid') == '76561197976127725'
    assert info.get('username') == 'Elvoc'
    assert info.get('nickname') == 'Elvoc'


@pytest.mark.requires_cookies
def test_yandex_realty_offer_cookies():
    cookies = open('yandex.test.cookies').read()
    info = extract(parse('https://realty.yandex.ru/offer/363951114410351104/', cookies)[0])

    assert info.get('uid') == '86903473'
    assert info.get('name') == 'Севостьянова Мария Владимировна'


@pytest.mark.requires_cookies
def test_gitlab_cookies():
    cookies = open('gitlab.test.cookies').read()
    info = extract(parse('https://gitlab.com/markglenfletcher', cookies)[0])

    assert info.get('uid') == '419655'


@pytest.mark.skip(reason='Failed in GitHub CI')
def test_blogger():
    info = extract(parse('https://b0ltay.blogspot.ru')[0])

    assert info.get('uid') == '10725121405978587846'
    assert info.get('blog_id') == '9057808199412143402'


def test_d3():
    """D3.ru"""
    info = extract(parse('https://d3.ru/user/nomad62')[0])

    assert info.get('uid') == '126836'


@pytest.mark.skip(reason="broken")
def test_stack_exchange():
    info = extract(parse('https://stackoverflow.com/users/198633/inspectorg4dget')[0])

    assert info.get('uid') == '198633'
    assert info.get('stack_exchange_uid') == '67986'
    assert info.get('gravatar_url') == 'https://gravatar.com/5b9c04999233026354268c2ee4237e04'
    assert info.get('gravatar_username') == 'inspectorg4dget'
    assert info.get('gravatar_email_md5_hash') == '5b9c04999233026354268c2ee4237e04'


def test_soundcloud():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'}
    info = extract(parse('https://soundcloud.com/danielpatterson', headers=headers)[0])

    assert info.get('uid') == '78365'
    assert info.get('username') == 'danielpatterson'
    assert info.get('name') == 'Daniel Patterson'
    assert info.get('following_count') == '23'
    assert info.get('follower_count') == '36'
    assert info.get('is_verified') == 'False'
    assert info.get('image') == 'https://i1.sndcdn.com/avatars-000222811304-x9f1ao-large.jpg'
    assert info.get('location') == 'Baton Rouge'
    assert info.get('country_code') == 'US'
    assert info.get('created_at') == '2009-02-27T16:08:17Z'


def test_vcru():
    info = extract(parse('https://vc.ru/u/6587-pavel-stolyarov')[0])

    assert info.get('uid') == '6587'
    assert info.get('username') == '6587-pavel-stolyarov'
    assert info.get('name') == 'Павел Столяров'


def test_livejournal():
    info = extract(parse('https://julia-klay.livejournal.com/')[0])

    assert info.get('uid') == '83505610'
    assert info.get('name') == 'julia_klay'
    assert info.get('username') == 'julia_klay'
    assert info.get('is_personal') == 'True'
    assert info.get('is_community') == 'False'


@pytest.mark.skip(reason="doesnt work without proxy, 503 error")
def test_myspace():
    info = extract(parse('https://myspace.com/katelynryry')[0])

    assert info.get('uid') == '8158005'
    assert info.get('username') == 'katelynryry'


@pytest.mark.skip(reason="youtube remove google+ links from channel pages")
def test_youtube():
    info = extract(parse('https://www.youtube.com/channel/UCbeOQiPo5SjX8Q_IoSooBig')[0])

    assert info.get('gaia_id') == '117503292148966883754'
    assert info.get('name') == 'Art NI'


def test_google_maps():
    info = extract(parse('https://www.google.com/maps/contrib/117503292148966883754')[0])

    # assert info.get('contribution_level').startswith('Level 3 Local Guide')
    assert info.get('name') == 'Art NI'
    assert int(info.get('contributions_count')) >= 100


def test_deviantart():
    info = extract(parse('https://www.deviantart.com/muse1908')[0])

    assert info.get('country') == 'France'
    assert info.get('gender') == 'female'
    assert info.get('website') == 'www.purelymuse.com'
    assert info.get('username') == 'MuseMercier'
    assert info.get(
        'links') == "['https://www.instagram.com/muse.mercier/', 'https://twitter.com/musenews']"
    assert info.get('tagline') == 'Nothing worth having is easy...'
    assert info.get('bio').startswith('Hi! My name is Muse Mercier,') is True
    assert info.get('created_at').startswith('2005-06-16')


def test_tumblr():
    info = extract(parse('https://alexaimephotography.tumblr.com/')[0])

    assert info.get('fullname') == 'Alex Aimé Photography'
    assert info.get('title') == 'My name is Alex Aimé, and i am a freelance photographer. Originally from Burgundy in France .I am a man of 29 years. Follow me on : www.facebook.com/AlexAimePhotography/'
    assert info.get('links') == "['https://www.facebook.com/AlexAimePhotography/', 'https://500px.com/alexaimephotography', 'https://www.instagram.com/alexaimephotography/', 'https://www.flickr.com/photos/photoambiance/']"
    assert 'image' in info
    assert 'image_bg' in info


def test_eyeem():
    info = extract(parse('https://www.eyeem.com/u/blue')[0])

    assert info.get('eyeem_id') == '38760'
    assert info.get('eyeem_username') == 'blue'
    assert info.get('fullname') == 'Blue Lee'
    assert info.get('bio') == 'hello!^_^'
    assert info.get('follower_count') == '8'
    assert info.get('friends_count') == '0'
    assert info.get('liked_photos') == '0'
    assert info.get('photos') == '3'
    assert info.get('facebook_uid') == '1610716256'


@pytest.mark.skip(reason="Broken, now API only: https://api.vimeo.com/users/alexaimephotography")
def test_vimeo():
    info = extract(parse('https://vimeo.com/alexaimephotography')[0])

    assert info.get('uid') == '75857717'
    assert info.get('name') == 'AlexAimePhotography'
    assert info.get('username') == 'alexaimephotography'
    assert info.get('location') == 'France'
    assert info.get('created_at') == '2017-12-06 06:49:28'
    assert info.get('is_staff') == 'False'
    assert info.get(
        'links') == "['https://500px.com/alexaimephotography', 'https://www.flickr.com/photos/photoambiance/', 'https://www.instagram.com/alexaimephotography/', 'https://www.youtube.com/channel/UC4NiYV3Yqih2WHcwKg4uPuQ', 'https://flii.by/alexaimephotography/']"


def test_gravatar():
    info = extract(parse('https://en.gravatar.com/kostbebix.json')[0])

    assert info.get('gravatar_id') == '17467145'
    assert info.get('username') == 'kostbebix'
    assert info.get('fullname') == 'kost BebiX'
    assert info.get('location') == 'Kiev, Ukraine'
    assert info.get('emails') == "['k.bx@ya.ru']"
    assert info.get('image') == 'https://secure.gravatar.com/avatar/d6ac4c55425d6f9d28db9068dbb49e09'
    assert info.get('links') == "['http://twitter.com/kost_bebix']"
    assert 'emails_username' not in info


def test_pinterest_api():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'}
    info = extract(parse('https://www.pinterest.ru/resource/UserResource/get/?source_url=%2Fgergelysndorszendrenyi%2F_saved%2F&data=%7B%22options%22%3A%7B%22isPrefetch%22%3Atrue%2C%22field_set_key%22%3A%22profile%22%2C%22username%22%3A%22gergelysndorszendrenyi%22%2C%22no_fetch_context_on_resource%22%3Afalse%7D%2C%22context%22%3A%7B%7D%7D&_=1615737383499', headers=headers)[0])
    assert info.get('pinterest_id') == '730849983187756836'
    assert info.get('pinterest_username') == 'gergelysndorszendrenyi'
    assert info.get('fullname') == 'Gergely Sándor-Szendrenyi'
    assert info.get('type') == 'user'
    assert info.get('image') == 'https://s.pinimg.com/images/user/default_280.png'
    assert info.get('country') == 'HU'
    assert info.get('is_indexed') == 'True'
    assert info.get('is_partner') == 'False'
    assert info.get('is_tastemaker') == 'False'
    assert info.get('is_indexed') == 'True'
    assert info.get('has_board') == 'True'
    assert info.get('has_board') == 'True'
    assert info.get('is_verified_merchant') == 'False'
    assert info.get('website') == 'https://plus.google.com/106803550602898494752'
    assert info.get('last_pin_save_datetime') is not None
    assert info.get('is_website_verified') == 'False'
    assert info.get('group_board_count') == '0'
    assert 'follower_count' in info
    assert 'following_count' in info
    assert info.get('board_count') == '11'
    assert int(info.get('pin_count')) > 100


@pytest.mark.skip(reason="broken")
def test_pinterest_profile():
    info = extract(parse('https://www.pinterest.ru/gergelysndorszendrenyi/boards/')[0])

    assert info.get('pinterest_id') is None
    assert info.get('username') == 'gergelysndorszendrenyi'
    assert info.get('fullname') == 'Gergely Sándor-Szendrenyi'
    assert info.get('type') is None
    assert info.get('image') == 'https://s.pinimg.com/images/user/default_280.png'
    assert info.get('country') == 'HU'
    assert info.get('is_indexed') == 'True'
    assert info.get('is_partner') is None
    assert info.get('is_tastemaker') is None
    assert info.get('is_indexed') == 'True'
    assert info.get('is_website_verified') == 'False'
    assert info.get('follower_count') == '2'
    assert info.get('following_count') == '16'
    assert info.get('board_count') == '11'
    assert int(info.get('pin_count')) > 100


@pytest.mark.skip(reason="broken")
def test_pinterest_board():
    info = extract(parse('https://www.pinterest.ru/gergelysndorszendrenyi/garden-ideas/')[0])

    assert info.get('pinterest_id') == '730849983187756836'
    assert info.get('pinterest_username') == 'gergelysndorszendrenyi'
    assert info.get('fullname') == 'Gergely Sándor-Szendrenyi'
    assert info.get('type') == 'user'
    assert info.get('image') == 'https://s.pinimg.com/images/user/default_280.png'
    assert info.get('country') == 'HU'
    assert info.get('is_indexed') == 'True'
    assert info.get('is_partner') == 'False'
    assert info.get('is_tastemaker') == 'False'
    assert info.get('locale') == 'hu-HU'


def test_yandex_collections_api():
    info = extract(parse('http://yandex.uz/collections/api/users/gebial')[0])

    assert info.get('yandex_public_id') == '20vpvmmwpnwyb0dpbnjvy3k14c'
    assert info.get('fullname') == 'yellow_lolo'
    assert info.get('image') == 'https://avatars.mds.yandex.net/get-yapic/62162/enc-325ec489adfdc84e00cb76315a5e214dc95d51408754cd21321958be4b59647a/islands-200'
    assert info.get('gender') == 'm'
    assert info.get('likes') is None
    assert info.get('cards') == '0'
    assert info.get('boards') == '0'
    assert info.get('is_passport') == 'True'
    assert info.get('is_restricted') == 'False'
    assert info.get('is_forbid') == 'False'
    assert info.get('is_km') == 'False'
    assert info.get('is_business') == 'False'


@pytest.mark.skip(reason="failed from github CI infra IPs")
def test_yandex_market():
    info = extract(parse('https://market.yandex.ru/user/z16yy5a9ae7uh030t5bgpkgyqg/reviews')[0])

    assert info.get('username') == 'katerina.jaryschckina'
    assert info.get('yandex_uid') == '207757917'
    assert info.get('yandex_public_id') == 'z16yy5a9ae7uh030t5bgpkgyqg'
    assert info.get('fullname') == 'Екатерина Ярышкинa'
    assert info.get('image') == 'https://avatars.mds.yandex.net/get-yapic/15298/enc-b44c03912bc49d1ba01345b8a2a4facbf24874f4dc922b4eb50b455107676f1a/islands-200'
    assert info.get('reviews_count') == '2'
    assert info.get('is_deleted') == 'False'
    assert info.get('is_hidden_name') == 'True'
    assert info.get('is_verified') == 'False'
    assert info.get('linked_social') == "[{'type': 'vkontakte', 'uid': '137002953', 'username': None, 'profile_id': 12075972}]"
    assert info.get('links') == "['https://vk.com/id137002953']"


@pytest.mark.github_failed
def test_tiktok():
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
    info = extract(parse('https://www.tiktok.com/@red', headers=headers)[0])

    assert info.get('tiktok_id') == '6667977707978850310'
    assert info.get('tiktok_username') == 'red'
    assert info.get('fullname') == '(RED)'
    assert 'bio' in info
    assert 'tiktokcdn.com' in info.get('image')
    assert info.get('is_verified') == 'True'
    assert info.get('is_secret') == 'False'
    assert info.get('sec_uid') == 'MS4wLjABAAAAVAp3JR-xHP7UnaDt4S9T9eyPqRDwgGiBRnzdZRm63jIGWy5s39a027nKJlu_UjOZ'
    assert int(info.get('following_count')) > 300
    assert int(info.get('follower_count')) > 36000
    assert int(info.get('heart_count')) > 275900
    assert int(info.get('video_count')) > 50
    assert info.get('digg_count') == '0'


@pytest.mark.skip(reason="failed from github CI infra IPs")
def test_flickr():
    info = extract(parse('https://www.flickr.com/photos/alexaimephotography2020/')[0])

    assert info.get('flickr_id') == '187482857@N04'
    assert info.get('flickr_username') == 'alexaimephotography2020'
    assert info.get('flickr_nickname') == 'aaphotography2020'
    assert info.get('fullname') == 'alexaim%E9 photography'
    assert info.get('image') == 'https://farm66.staticflickr.com/65535/buddyicons/187482857@N04_r.jpg?1584445364#187482857@N04'
    assert int(info.get('photo_count')) > 140
    assert int(info.get('follower_count')) > 180
    assert int(info.get('following_count')) > 70
    assert info.get('created_at').startswith('2020-03-17')
    assert info.get('is_pro') == 'False'
    assert info.get('is_deleted') == 'False'


def test_telegram():
    info = extract(parse('https://t.me/buzovacoin')[0])

    assert info.get('fullname') == 'Buzovacoin'
    assert info.get('bio').startswith('ICO Ольги Бузовой - Платформа BUZAR')
    assert 'image' in info


def test_mssg_me():
    info = extract(parse('https://mssg.me/mr.adam')[0])

    assert info.get('fullname') == 'Mr.Adam'
    assert info.get('bio') == 'Бизнесмен'
    assert info.get('messengers') == "['whatsapp', 'messenger']"
    assert info.get('messenger_values') == "['+77026924715', 'adamcigelnik']"


def test_patreon():
    info = extract(parse('https://www.patreon.com/annetlovart')[0])

    assert info.get('patreon_id') == '33913189'
    assert info.get('patreon_username') == 'annetlovart'
    assert info.get('fullname') == 'Annet Lovart'
    assert info.get('links') == "['https://www.facebook.com/322598031832479', 'https://www.instagram.com/annet_lovart', 'https://twitter.com/annet_lovart', 'https://youtube.com/channel/UClDg4ntlOW_1j73zqSJxHHQ']"
    assert info.get('is_nsfw') == 'False'
    assert 'image' in info
    assert 'image_bg' in info
    assert info.get('created_at') == '2020-04-19T16:29:11.000+00:00'
    assert 'bio' in info


def test_last_fm():
    info = extract(parse('https://www.last.fm/user/alex')[0])

    assert info.get('fullname') == 'Alex'
    assert info.get('bio') == '• scrobbling since 21 Feb 2003'
    assert info.get('image') == 'https://lastfm.freetls.fastly.net/i/u/avatar170s/15e455555655c8503ed9ba6fce71d2d6.png'


def test_ask_fm():
    info = extract(parse('https://ask.fm/sasha')[0])

    assert info.get('username') == 'sasha'
    assert info.get('fullname') == 'Александр Чубаров'
    assert info.get('posts_count') == '18'
    assert info.get('likes_count') == '1.06 K'
    assert info.get('location') == 'Красноярск'
    assert 'image' in info


def test_launchpad():
    info = extract(parse('https://launchpad.net/~antony')[0])

    assert info.get('fullname') == 'Genelyk'
    assert info.get('username') == 'antony'
    assert info.get('languages') == 'Spanish'
    assert info.get('karma') == '0'
    assert info.get('created_at') == '2007-05-17'
    assert info.get('timezone') == 'America/Lima (UTC-0500)'
    assert info.get('openpgp_key') == '62FCE94A1E7871FBFE81F10AB9579C368DD41DF8'


def test_twitch():
    info = extract(parse('https://m.twitch.tv/johnwolfe/profile')[0])

    assert info.get('id') == '36536868'
    assert info.get('username') == 'johnwolfe'
    assert info.get('bio') == 'Horror games. Dead By Daylight. Charity streams. '
    assert info.get('fullname') == 'JohnWolfe'
    assert info.get('image') == 'https://static-cdn.jtvnw.net/jtv_user_pictures/johnwolfe-profile_image-61f8e374d34a8bbd-150x150.png'
    assert info.get('image_bg') == 'https://static-cdn.jtvnw.net/jtv_user_pictures/9d88705b5a305a7e-profile_banner-480.jpeg'
    # assert 'views_count' in info
    assert 'likes_count' in info


def test_linktree():
    info = extract(parse('https://linktr.ee/annetlovart')[0])

    assert info.get('id') == '5420275'
    assert info.get('username') == 'annetlovart'
    assert info.get('image') == 'https://d1fdloi71mui9q.cloudfront.net/MidfykWeQemDO5YVdRDv_35849b5fb49c69271d284ade7ffef659'
    assert info.get('is_active') == 'True'
    assert info.get('is_verified') == 'True'
    assert info.get('is_email_verified') == 'True'
    assert info.get('tier') == 'free'
    assert info.get('links') == "['https://uk.wikipedia.org/wiki/Annet_Lovart', 'https://www.patreon.com/annetlovart', 'https://creativemarket.com/annet_lovart/4945530-Trendy-Floral-Pattern', 'https://www.behance.net/gallery/96717659/Maya-flowers', 'https://www.facebook.com/annetlovart', 'https://youtu.be/mWU_Lyb9kw4', 'https://instagram.com/annet_lovart', 'https://www.pinterest.com/annet_lovart/one-stroke-tutorial-annet_lovart/']"


def test_xakep():
    info = extract(parse('https://xakep.ru/author/dmbaturin/')[0])

    assert info.get('fullname') == 'Даниил Батурин'
    assert info.get('image') == 'https://secure.gravatar.com/avatar/b1859c813547de1bba3c65bc4b1a217c?s=150&d=retro&r=g'
    assert info.get('bio') == 'Координатор проекта VyOS (https://vyos.io), «языковед», функциональщик,  иногда сетевой администратор'
    assert info.get('links') == "['https://www.baturin.org']"
    assert info.get('joined_year') == '2018'
    assert info.get('gravatar_url') == 'https://gravatar.com/b1859c813547de1bba3c65bc4b1a217c'
    assert info.get('gravatar_username') == 'dmbaturin'
    assert info.get('gravatar_email_md5_hash') == 'b1859c813547de1bba3c65bc4b1a217c'


@pytest.mark.skip(reason="no more author pages for now")
def test_tproger_ru():
    info = extract(parse('https://tproger.ru/author/NickPrice/')[0])

    assert info.get('fullname') == 'Никита Прияцелюк'
    assert info.get('image').startswith('https://secure.gravatar.com/avatar/b6c7803b43433349ff84b11093562594') is True


def test_jsfiddle():
    info = extract(parse('https://jsfiddle.net/user/john')[0])

    assert info.get('fullname') == 'John Michel'
    assert info.get('company') == 'Philadelphia, PA'
    assert info.get('links') == "['https://twitter.com/jhnmchl', 'https://github.com/johnmichel']"
    assert info.get('image') == 'https://www.gravatar.com/avatar/eca9f115bdefbbdf0c0381a58bcaf601?s=80'
    assert info.get('gravatar_url') == 'https://gravatar.com/eca9f115bdefbbdf0c0381a58bcaf601'
    assert info.get('gravatar_username') == 'cowbird'
    assert info.get('gravatar_email_md5_hash') == 'eca9f115bdefbbdf0c0381a58bcaf601'


def test_disqus_api():
    info = extract(parse('https://disqus.com/api/3.0/users/details?user=username%3Amargaret&attach=userFlaggedUser&api_key=E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F')[0])

    assert info.get('id') == '1593'
    assert info.get('fullname') == 'margaret'
    assert float(info.get('reputation')) > 1
    assert info.get('reputation_label') == 'Average'
    assert info.get('following_count') == '0'
    assert info.get('follower_count') == '0'
    assert info.get('is_power_contributor') == 'False'
    assert info.get('is_anonymous') == 'False'
    assert info.get('created_at') == '2007-11-06T01:14:28'
    assert info.get('upvotes_count') == '0'
    assert info.get('forums_count') == '0'
    assert info.get('image') == 'https://disqus.com/api/users/avatars/margaret.jpg'
    assert info.get("forums_following_count") == "0"
    assert info.get("is_private") == "False"
    assert info.get("comments_count") == "0"


def test_ucoz_1():
    info = extract(parse('https://av.3dn.ru/index/8-0-Maikl_401')[0])

    assert info.get('fullname') == 'Михаил ко'
    assert info.get('gender') == 'Мужчина'
    assert info.get('created_at') == 'Пятница, 23.01.2015, 15:02'
    assert info.get('last_seen_at') == 'Пятница, 23.01.2015, 15:07'
    assert info.get('link') == 'http://uid.me/uguid/176168901'
    assert info.get('uidme_uguid') == '176168901'
    assert info.get('location') == 'Российская Федерация'
    assert info.get('city') == 'Москва'
    assert info.get('state') == 'Москва'
    assert info.get('birthday_at') == '16 Декабря 1971'


def test_ucoz_2():
    info = extract(parse('http://www.thaicat.ru/index/8-0-koshka')[0])

    assert info.get('fullname') == 'natalya Myunster'
    assert info.get('url') == 'http://www.thaicat.ru/index/8-10419'
    assert info.get('image') == 'http://www.thaicat.ru/avatar/00/20/419858.jpg'
    assert info.get('gender') == 'Женщина'
    assert info.get('created_at') == 'Суббота, 14.01.2012, 17:41'
    assert info.get('last_seen_at') == 'Суббота, 14.01.2012, 17:41'
    assert info.get('country') == 'Италия'
    assert info.get('city') == 'l\'aquila'
    assert info.get('birthday_at') == '10 Июля 1975'


def test_ucoz_3():
    info = extract(parse('http://prenatal-club.ucoz.com/index/8-0-koshka')[0])

    assert info.get('url') == 'https://prenatal-club.ucoz.com/index/8-128'
    assert info.get('image') == 'https://425523249.uid.me/avatar.jpg'
    assert info.get('created_at') == 'Среда, 10.03.2010, 09:42'
    assert info.get('last_seen_at') == 'Среда, 10.03.2010, 09:42'
    assert info.get('link') == 'http://uid.me/uguid/425523249'
    assert info.get('uidme_uguid') == '425523249'
    assert info.get('location') == 'Российская Федерация'
    assert info.get('city') == 'Санкт-Петербург'
    assert info.get('state') == 'Санкт-Петербург'


def test_uidme():
    info = extract(parse('http://uid.me/koshka', timeout=10)[0])

    assert info.get('username') == 'koshka'
    assert info.get('image') == 'https://uid.me/img/avatar/w/z/n/medium_m38dkp68.jpg'
    assert info.get('headline') == '..Но в глубине души моей тоска по крови, ночи, дикости горит (Гессе).'
    assert info.get('bio') == 'Студентка ВНУ, факультет философии (4й курс). Ищу, жду, иду, пишу... Не слишком отличаюсь от большинства людей моего возраста.'
    assert info.get('contacts') == "['dariya-koshka@mail.ru']"
    assert info.get('email') == 'dariya-koshka@mail.ru'
    assert info.get('phone') == '380669243144'
    assert info.get('skype') == 'Dariya Koshka'
    assert info.get('location') == 'Луганск'
    assert info.get('links') == "['http://www.proza.ru/avtor/dahakot']"


def test_tapd():
    info = extract(parse('https://tapd.co/api/user/getPublicProfile/betsyalvarezz')[0])

    assert info.get('fullname') == 'Betsy Alvarez'
    assert info.get('username') == 'betsyalvarezz'
    assert int(info.get('views_count')) > 43124
    assert info.get('image') == 'https://distro.tapd.co/x3fwD79IdB0LqOqf.jpeg'
    assert info.get('links') == "['https://www.twitter.com/Betsyalvarezz', 'https://www.instagram.com/Betsyalvarezz', 'https://cash.app/$Betsyalvarezz', 'https://www.tiktok.com/@Betsyalvarezz', 'https://www.instagram.com/Brb.thelabel', 'https://www.youtube.com/c/BetsyAlvarezz', 'https://www.amazon.com/hz/wishlist/ls/2GNHXWNBBCIP0?ref_=wl_share', 'https://onlyfans.com/Betsyalvarezz']"


def test_buzzfeed():
    info = extract(parse('https://www.buzzfeed.com/lisa')[0])

    assert info.get('uuid') == '408a7d54-6af9-452e-8614-7f44216ed983'
    assert info.get('id') == '43876'
    assert info.get('fullname') == 'lisa'
    assert info.get('username') == 'lisa'
    assert info.get('bio') == 'If I&#39;m not me than who am I? And if I&#39;m somebody else, than why do I look like me?'
    assert info.get('posts_count') == '0'
    assert info.get('created_at').startswith('2009-12-17')
    assert info.get('is_community_user') == 'True'
    assert info.get('is_deleted') == 'False'
    assert info.get('image') == 'https://img.buzzfeed.com/buzzfeed-static/static/user_images/web02/2009/12/17/20/lisa-31169-1261100831-63.jpg'


def test_freelancer():
    info = extract(parse('https://www.freelancer.com/api/users/0.1/users?usernames%5B%5D=theDesignerz&compact=true')[0])

    assert info.get('id') == '6751536'
    assert info.get('nickname') == 'theDesignerz'
    assert info.get('username') == 'theDesignerz'
    assert info.get('fullname') == 'theDesignerz'
    assert info.get('company') == 'theDesignerz'
    assert info.get('company_founder_id') == '26684749'
    assert info.get('role') == 'freelancer'
    assert info.get('location') == 'Islamabad, Pakistan'
    assert info.get('created_at').startswith('2012-12-09')


def test_yelp_username():
    """Yelp"""
    info = extract(parse('http://dima.yelp.com')[0])

    assert info.get('yelp_userid') == 'b_a5icXGK-AXVYZKehgKLw'
    assert info.get('fullname') == 'Dima "ZOMG" M.'
    assert info.get('location') == 'Brooklyn, NY'
    assert info.get('image') == 'https://s3-media0.fl.yelpcdn.com/photo/bGiNMDL6FZAtPpMfljRGtg/ls.jpg'


def test_yelp_userid():
    """Yelp"""
    info = extract(parse('https://www.yelp.com/user_details?userid=b_a5icXGK-AXVYZKehgKLw')[0])

    assert info.get('yelp_userid') == 'b_a5icXGK-AXVYZKehgKLw'
    assert info.get('fullname') == 'Dima "ZOMG" M.'
    assert info.get('location') == 'Brooklyn, NY'
    assert info.get('image') == 'https://s3-media0.fl.yelpcdn.com/photo/bGiNMDL6FZAtPpMfljRGtg/ls.jpg'


def test_trello():
    """Trello API"""
    info = extract(parse('https://trello.com/1/Members/xFubuki')[0])

    assert info.get("id") == "5e78cae55d711a6382e239c1"
    assert info.get("username") == "xfubuki"
    assert info.get("fullname") == "xFubuki"
    assert info.get("type") == "normal"
    assert info.get("is_verified") == "True"
    assert 'image' in info


@pytest.mark.github_failed
@pytest.mark.requires_cookies
def test_weibo():
    headers = {"cookie": "SUB=_2AkMXyuc_f8NxqwJRmP8SyWPrbo13zAvEieKhlhbkJRMxHRl-123", "cache-control": "no-cache"}
    info = extract(parse('https://weibo.com/clairekuo?is_all=1', headers=headers, timeout=10)[0])

    assert info.get("weibo_id") == "1733299783"
    assert info.get("fullname") == "郭靜Claire"


def test_icq():
    info = extract(parse('https://icq.im/CaZaNoVa163')[0])

    assert info.get("fullname") == "Cazanova Haxor"
    assert info.get("username") == "CaZaNoVa163"
    assert info.get("image") == "https://ub.icq.net/api/v26/files/avatar/get/?targetNick=CaZaNoVa163&size=1024"


def test_pastebin():
    info = extract(parse('https://pastebin.com/u/GCCXGeneral')[0])

    assert info.get("image") == "https://pastebin.com/cache/img/1/2/20/726408.jpg"
    assert info.get("location") == "Eastern United States | Contact: GCCXGeneral@gmail.com"
    assert 'views_count' in info
    assert 'all_views_count' in info
    assert info.get("created_at") == "Monday 24th of June 2013 12:25:12 AM CDT"


def test_tinder():
    info = extract(parse('https://tinder.com/@john')[0])

    assert info.get("tinder_username") == "john"
    assert info.get("birth_date").startswith("2000")
    assert info.get("id") == "60c40ff58fb9ce01006d74ce"
    assert info.get("fullname") == "Mamk"
    assert eval(info.get("education"))[0] == "Mokpo National Maritime University"
    assert info.get("image") == "https://images-ssl.gotinder.com/60c40ff58fb9ce01006d74ce/original_30e5c835-c34f-447b-b346-8b539e7a7e07.jpeg"

    images_list = eval(info.get("images"))
    assert 'https://images-ssl.gotinder.com/60c40ff58fb9ce01006d74ce/original_30e5c835-c34f-447b-b346-8b539e7a7e07.jpeg' in images_list


def test_ifunny_co():
    info = extract(parse('https://ifunny.co/user/CuddleKinnz')[0])

    assert info.get("id") == "5ab1fd49a2cf59ac948b456e"
    assert info.get("username") == "CuddleKinnz"
    assert info.get("bio") == "Humor Some Like, Some Hate"
    assert info.get("image") == "https://imageproxy.ifunny.co/noop/user_photos/67ea0dc62b3d7a0a938d68b3c519e22b3d9d35f7_0.webp"
    # assert int(info.get("follower_count")) >= 0
    # assert int(info.get("following_count")) >= 70
    # assert int(info.get("post_count")) >= 127
    # assert int(info.get("created_count")) >= 127
    # assert info.get("featured_count") == "7"
    # assert int(info.get("smile_count")) > 32000
    # assert int(info.get("achievement_count")) >= 1
    assert info.get("is_verified") == "False"


def test_wattpad_api():
    # https://wattpad.com/user/JeniferBalanzar
    info = extract(parse('https://www.wattpad.com/api/v3/users/JeniferBalanzar')[0])
    
    assert info.get("username") == "JeniferBalanzar"
    assert info.get("fullname") == "Jenifer Balanzar"
    assert info.get("image") == "https://img.wattpad.com/useravatar/JeniferBalanzar.128.615375.jpg"
    assert info.get("image_bg") == "https://img.wattpad.com/userbg/JeniferBalanzar.36464.jpg"
    assert info.get("gender") == "Female"  
    assert info.get("locale") == "es_MX"    
    assert int(info.get("follower_count")) >= 266
    assert int(info.get("following_count")) >= 89
    assert info.get("created_at") == "2019-12-10T00:25:02Z"  
    assert info.get("updated_at") == "2020-09-08T08:24:38Z" 
    assert info.get("verified") == "False"  
    assert info.get("verified_email") == "True"


def test_kik():
    info = extract(parse('https://ws2.kik.com/user/mksyx')[0])
    
    assert info.get("fullname") == "experience true satisfaction"
    assert info.get("image") == "http://profilepics.cf.kik.com/QUwticPE8XU7qm7qrTXbWgCfSu4/orig.jpg"
  
    
def test_docker_hub_api():
    # https://hub.docker.com/u/adastra2ankudinov
    info = extract(parse('https://hub.docker.com/v2/users/adastra2ankudinov/')[0])
    
    assert info.get("uid") == "b4f92258ad95428ea88ba498a883b40a"  
    assert info.get("username") == "adastra2ankudinov" 
    assert info.get("type") == "User"  
    assert info.get("image") == "https://secure.gravatar.com/avatar/410bf05a8e85652a6b174d627dce4e3d.jpg?s=80&r=g&d=mm"  
    
    
def test_mixcloud_api():
    # https://www.mixcloud.com/savath69/
    info = extract(parse('https://api.mixcloud.com/savath69/')[0])

    assert info.get("username") == "savath69"
    assert info.get("country") == "France"
    assert info.get("city") == "Lyon" 
    assert info.get("created_at") == "2017-08-06T11:41:02Z" 
    assert info.get("updated_at") == "2017-08-06T11:41:02Z" 
    assert info.get("image") == "https://thumbnailer.mixcloud.com/unsafe/640x640/profile/d/1/c/a/0f1c-60ec-4f2c-9b04-5a9536c96d51"     
    assert int(info.get("follower_count")) >=  25
    assert int(info.get("following_count")) >= 6
    assert int(info.get("cloudcast_count")) >= 5
    assert int(info.get("favorite_count")) >= 0
    assert int(info.get("listen_count")) >= 15
    assert info.get("is_pro") == "False" 
    assert info.get("is_premium") == "False"    
   
    
def test_binarysearch_api():
    info = extract(parse('https://binarysearch.com/api/users/LarryNY/profile')[0])

    assert int(info.get("uid")) >= 10435
    assert info.get("username") == "LarryNY" 
    assert info.get("image") == "https://binarysearch.s3-us-west-2.amazonaws.com/LarryNY?hash=1599781403401" 
    assert info.get("location") == "New York, NY, USA" 
    assert info.get("bio") == "This is fun." 
    assert info.get("links") == "https://www.youtube.com/c/Algorithmist/" 
    assert info.get("isAdmin") == "False" 
    assert info.get("isVerified") == "True" 
    assert info.get("HistoryPublic") == "False" 
    assert info.get("RoomPublic") == "True" 
    assert info.get("InviteOnly") == "False" 
    

def test_pr0gramm_api():
    # https://pr0gramm.com/user/TheBorderCrash
    info = extract(parse('https://pr0gramm.com/api/profile/info?name=TheBorderCrash')[0])

    assert int(info.get("uid")) >= 323469  
    assert info.get("username") == "TheBorderCrash" 
    assert int(info.get("uploadCount")) >= 5859
    assert int(info.get("commentCount")) >= 2497
    assert int(info.get("tagCount")) >= 22900
    assert info.get("likesArePublic") == "False"     


def test_vk_foaf():
    """VK user profile foaf page"""
    info = extract(parse('https://vk.com/foaf.php?id=1')[0])

    assert info.get("is_private") == "True"
    assert info.get("state") == "verified"
    assert info.get("first_name") in ("Павел", "Pavel")
    assert info.get("last_name") in ("Дуров", "Durov")
    assert info.get("fullname") in ("Павел Дуров", "Pavel Durov")
    assert info.get("gender") == "male"
    assert info.get("created_at") == "2006-09-23 20:27:12+03:00"
    assert info.get("updated_at") == "2018-01-30 01:51:19+03:00"
    assert info.get("website") == "http://t.me/durov"


def test_aparat_api():
    info = extract(parse('https://www.aparat.com/api/fa/v1/user/user/information/username/BoHBiG')[0])

    assert info.get("uid") == "3935310"
    assert info.get("username") == "BoHBiG"
    assert info.get("fullname") == "عمو بیگ"
    assert info.get("image") == "https://static.cdn.asset.aparat.com/profile-photo/3935310-182645-b.jpg"
    assert 'follower_count' in info
    assert 'following_count' in info
    assert info.get("is_banned") == "False"
    assert info.get("links") == "['https://sibmo.ir/bigmj', 'http://www.telegram.me/amobig', 'http://www.instagram.com/amobigstream']"
    assert 'video_count' in info
    assert info.get("bio") == "چنل تلگرام:\r\nhttps://t.me/amobig"


def test_memory_lol():
    info = extract(parse('https://api.memory.lol/v1/tw/libsoftiktok')[0])

    assert info.get("id") == "1326229737551912960"
    assert info.get("known_usernames") == "['shaya69830552', 'shaya_ray', 'chayaraichik', 'chayathepatriot', 'cuomomustgo', 'houseplantpotus', 'libsoftiktok']"
