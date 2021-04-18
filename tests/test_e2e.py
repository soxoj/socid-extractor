#!/usr/bin/env python3
import pytest

from socid_extractor.activation import get_twitter_headers
from socid_extractor.main import parse, extract, HEADERS


def test_vk_user_profile_full():
    info = extract(parse('https://vk.com/idsvyatoslavs')[0])

    assert info.get('vk_id') == '134173165'
    assert info.get('vk_username') == 'idsvyatoslavs'
    assert info.get('fullname') in ('Святослав Степанов', 'Svyatoslav Stepanov')


def test_vk_user_profile_no_username():
    info = extract(parse('https://vk.com/id568161939')[0])

    assert info.get('vk_id') == '568161939'
    assert info.get('vk_username') == None
    assert info.get('fullname') in ('Юля Заболотная', 'Yulya Zabolotnaya')


def test_vk_closed_user_profile():
    info = extract(parse('https://vk.com/alex')[0])

    assert info.get('fullname') in ('Александр Чудаев', 'Alexander Chudaev')


def test_vk_blocked_user_profile():
    headers = {'User-Agent': 'Curl'}
    info = extract(parse('https://vk.com/alexaimephotography', headers=headers)[0])

    assert info.get('fullname') in ('Alex Aimé')


def test_yandex_disk():
    info = extract(parse('https://yadi.sk/d/xRJFp3s2QWYv8')[0])

    assert info.get('yandex_uid') == '225171618'
    assert info.get('name') == 'Trapl  Zdenek'


def test_yandex_reviews():
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
    URLs = [
        'https://www.instagram.com/alexaimephotography/',
        'https://www.instagram.com/alexaimephotography/?__a=1',
    ]
    for url in URLs:
        info = extract(parse(url, headers=HEADERS)[0])

        assert info.get('id') == '6828488620'
        assert info.get('username') == 'alexaimephotography'
        assert info.get('fullname') == 'Alexaimephotography'
        assert info.get('facebook_uid') == '17841406738613561'
        assert info.get('is_private') == 'False'
        assert info.get('is_verified') == 'False'


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
    assert info.get('twitter_username') == 'lys1n'
    assert info.get('is_suspended') == 'False'


def test_ok():
    info = extract(parse('https://ok.ru/profile/46054003')[0])

    assert info.get('ok_id') == '46054003'

    info = extract(parse('https://ok.ru/andrey.ostashenya')[0])

    assert info.get('ok_user_name_id') == 'andrey.ostashenya'
    assert info.get('ok_id') == '576861363171'


def test_habr():
    info = extract(parse('https://habr.com/ru/users/m1rko/')[0])

    assert info.get('uid') == '1371978'
    assert info.get('username') == 'm1rko'
    assert info.get('image') == 'http://habrastorage.org/getpro/habr/avatars/4ec/bd0/85d/4ecbd085d692835a931d03174ff19539.png'


@pytest.mark.skip(reason="failed from github CI infra IPs")
def test_habr_no_image():
    info = extract(parse('https://habr.com/ru/users/ne555/')[0])

    assert info.get('uid') == '1800409'
    assert info.get('username') == 'ne555'
    assert not 'image' in info


@pytest.mark.skip(reason="down")
def test_twitter_shadowban_no_account():
    info = extract(parse('https://shadowban.eu/.api/sgfrgrrr')[0])

    assert info.get('has_tweets') == 'False'
    assert info.get('is_exists') == 'False'
    assert info.get('username') == 'sgfrgrrr'
    assert not 'is_protected' in info
    assert not 'has_ban' in info
    assert not 'has_search_ban' in info
    assert not 'has_banned_in_search_suggestions' in info


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
    assert info.get('is_nsfw') == 'False'
    assert info.get('is_mod') == 'True'
    assert info.get('is_following') == 'True'
    assert info.get('has_user_profile') == 'True'
    assert info.get('created_at') in ('2018-01-06 04:22:05', '2018-01-06 01:22:05')
    assert info.get('hide_from_robots') == 'True'
    assert int(info.get('total_karma')) > int(30000)
    assert int(info.get('post_karma')) > int(7000)


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
    assert info.get('blog_url') == 'https://t.me/s/osint_mindset'

def test_yandex_disk_photos():
    info = extract(parse('https://yadi.sk/a/oiySK_wg3Vv5p4')[0])

    assert info.get('yandex_uid') == '38569641'
    assert info.get('name') == 'Вербочка'


def test_my_mail_main():
    info = extract(parse('https://my.mail.ru/mail/zubovo/')[0])

    assert info.get('uid') == '13425818'
    assert info.get('name') == 'Олег Зубов'
    assert info.get('username') == 'zubovo'
    # there is no auId
    assert info.get('email') == 'zubovo@mail.ru'
    assert info.get('isVip') == 'False'
    assert info.get('isCommunity') == 'False'
    assert info.get('isVideoChannel') == 'False'


def test_my_mail_communities():
    # also video, apps, photo
    info = extract(parse('https://my.mail.ru/mail/zubovo/communities/')[0])

    assert info.get('uid') == '13425818'
    assert info.get('name') == 'Олег Зубов'
    assert info.get('username') == 'zubovo'
    assert info.get('auId') == '6667000454247668890'
    assert info.get('email') == 'zubovo@mail.ru'
    assert info.get('isVip') == 'False'
    assert info.get('isCommunity') == 'False'
    assert info.get('isVideoChannel') == 'False'


@pytest.mark.skip(reason="captcha")
def test_yandex_music_user_profile():
    headers = {'referer': 'https://music.yandex.ru/users/pritisk/playlists'}
    info = extract(parse('https://music.yandex.ru/handlers/library.jsx?owner=pritisk', headers=headers)[0])

    assert info.get('yandex_uid') == '16480689'
    assert info.get('username') == 'pritisk'
    assert info.get('name') == 'Юрий Притиск'
    assert info.get('image') == 'https://avatars.mds.yandex.net/get-yapic/29310/gK74BTyv8LrLRT0mQFIR2xcWv8-1/islands-200'
    assert info.get('links') == '[]'
    assert info.get('is_verified') == 'False'
    assert info.get('liked_albums') == '0'
    assert info.get('liked_artists') == '0'


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
    assert info.get('teaser') == 'Люблю Nike, спорт и активный образ жизни. С 2013 года я изучаю все, что связано с брендом NIke, веду блог.'
    assert info.get('facebook_username') == 'nikefansru/'
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
    info = extract(parse('https://www.behance.net/Skyratov', 'ilo0=1')[0])

    assert info.get('uid') == '39065909'
    assert info.get('username') == 'Skyratov'
    assert info.get('last_name') == 'Skuratov'
    assert info.get('first_name') == 'Vasiliy'


@pytest.mark.github_failed
def test_500px():
    info = extract(parse('https://api.500px.com/graphql?operationName=ProfileRendererQuery&variables=%7B%22username%22%3A%22the-maksimov%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22105058632482dd2786fd5775745908dc928f537b28e28356b076522757d65c19%22%7D%7D')[0])

    assert info.get('uid') == 'dXJpOm5vZGU6VXNlcjoyMzg5Ng=='
    assert info.get('legacy_id') == '23896'
    assert info.get('username') == 'The-Maksimov'
    assert info.get('name') == 'Maxim Maximov'
    assert info.get('qq_uid') == None
    assert info.get('fb_uid') == None
    assert info.get('instagram_username') == 'the.maksimov'
    assert info.get('twitter_username') == 'The_Maksimov'
    assert info.get('website') == 'www.instagram.com/the.maksimov'
    assert info.get('facebook_link') == 'www.facebook.com/the.maksimov'


def test_google_documents_cookies():
    cookies = open('google.test.cookies').read()
    info = extract(
        parse('https://docs.google.com/spreadsheets/d/1HtZKMLRXNsZ0HjtBmo0Gi03nUPiJIA4CC4jTYbCAnXw/edit#gid=0',
              cookies)[0])

    assert info.get('org_domain') == 'breakoutcommerce.com'
    assert info.get('org_name') == 'Gooten'


def test_bitbucket():
    info = extract(parse('https://bitbucket.org/arny/')[0])

    assert info.get('uid') == '57ad342a-ec8f-42cb-af05-98175b72b8db'
    assert info.get('username') == 'arny'
    assert info.get('created_at') == '2009-11-23T10:41:04.355755+00:00'


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


def test_yandex_realty_offer_cookies():
    cookies = open('yandex.test.cookies').read()
    info = extract(parse('https://realty.yandex.ru/offer/363951114410351104/', cookies)[0])

    assert info.get('uid') == '86903473'
    assert info.get('name') == 'Севостьянова Мария Владимировна'


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
    info = extract(parse('https://d3.ru/user/deer00hunter')[0])

    assert info.get('uid') == '75504'


def test_stack_exchange():
    info = extract(parse('https://stackoverflow.com/users/198633/inspectorg4dget')[0])

    assert info.get('uid') == '198633'
    assert info.get('stack_exchange_uid') == '67986'
    assert info.get('gravatar_url') == 'https://gravatar.com/5b9c04999233026354268c2ee4237e04'
    assert info.get('gravatar_username') == 'inspectorg4dget'
    assert info.get('gravatar_email_hash') == '5b9c04999233026354268c2ee4237e04'


def test_soundcloud():
    info = extract(parse('https://soundcloud.com/danielpatterson')[0])

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

    assert info.get('contribution_level').startswith('Level 3 Local Guide')
    assert info.get('name') == 'Art NI'


def test_deviantart():
    info = extract(parse('https://www.deviantart.com/muse1908')[0])

    assert info.get('country') == 'France'
    assert '2005-06-16' in info.get('created_at')
    assert info.get('gender') == 'female'
    assert info.get('website') == 'www.purelymuse.com'
    assert info.get('username') == 'Muse1908'
    assert info.get(
        'links') == "['https://www.instagram.com/muse.mercier/']"
    assert info.get('tagline') == 'Nothing worth having is easy...'


def test_tumblr():
    info = extract(parse('https://alexaimephotography.tumblr.com/')[0])

    assert info.get('fullname') == 'Alex Aimé Photography'
    assert info.get('title') == 'My name is Alex Aimé, and i am a freelance photographer. Originally from Burgundy in France .I am a man of 29 years. Follow me on : www.facebook.com/AlexAimePhotography/'
    assert info.get('links') == "['https://www.facebook.com/AlexAimePhotography/', 'https://500px.com/alexaimephotography', 'https://www.instagram.com/alexaimephotography/', 'https://www.flickr.com/photos/photoambiance/']"


def test_eyeem():
    info = extract(parse('https://www.eyeem.com/u/blue')[0])

    assert info.get('eyeem_id') == '38760'
    assert info.get('eyeem_username') == 'blue'
    assert info.get('fullname') == 'Blue Lee'
    assert info.get('bio') == 'hello!^_^'
    assert info.get('follower_count') == '8'
    assert info.get('friends') == '0'
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


def test_pinterest_api():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'}
    info = extract(parse('https://www.pinterest.ru/resource/UserResource/get/?source_url=%2Fgergelysndorszendrenyi%2F_saved%2F&data=%7B%22options%22%3A%7B%22isPrefetch%22%3Atrue%2C%22field_set_key%22%3A%22profile%22%2C%22username%22%3A%22gergelysndorszendrenyi%22%2C%22no_fetch_context_on_resource%22%3Afalse%7D%2C%22context%22%3A%7B%7D%7D&_=1615737383499', headers=headers)[0])
    assert info.get('pinterest_id') == '730849983187756836'
    assert info.get('pinterest_username') == 'gergelysndorszendrenyi'
    assert info.get('fullname') == 'Gergely Sándor-Szendrenyi'
    assert info.get('type') == 'user'
    assert info.get('image') == 'https://s.pinimg.com/images/user/default_280.png'
    assert info.get('country') == None
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
    assert info.get('follower_count') == '2'
    assert info.get('group_board_count') == '0'
    assert info.get('following_count') == '16'
    assert info.get('board_count') == '11'
    assert int(info.get('pin_count')) > 100


def test_pinterest_profile():
    info = extract(parse('https://www.pinterest.ru/gergelysndorszendrenyi/boards/')[0])

    assert info.get('pinterest_id') == None
    assert info.get('pinterest_username') == 'gergelysndorszendrenyi'
    assert info.get('fullname') == 'Gergely Sándor-Szendrenyi'
    assert info.get('type') == None
    assert info.get('image') == 'https://s.pinimg.com/images/user/default_280.png'
    assert info.get('country') == 'HU'
    assert info.get('is_indexed') == 'True'
    assert info.get('is_partner') == None
    assert info.get('is_tastemaker') == None
    assert info.get('is_indexed') == 'True'
    assert info.get('is_website_verified') == 'False'
    assert info.get('follower_count') == '2'
    assert info.get('following_count') == '16'
    assert info.get('board_count') == '11'
    assert int(info.get('pin_count')) > 100


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
    assert info.get('likes') == '0'
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
    assert info.get('created_at') in ('2020-03-17 07:18:59', '2020-03-17 04:18:59')
    assert info.get('is_pro') == 'False'
    assert info.get('is_deleted') == 'False'


def test_telegram():
    info = extract(parse('https://t.me/buzovacoin')[0])

    assert info.get('fullname') == 'Buzovacoin'
    assert info.get('bio').startswith('ICO Ольги Бузовой - Платформа BUZAR')
    assert 'image' in info


def test_mssg():
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


def test_last_fm():
    info = extract(parse('https://www.last.fm/user/alex')[0])

    assert info.get('fullname') == 'Alex'
    assert info.get('bio') == '• scrobbling since 21 Feb 2003'
    assert info.get('image') == 'https://lastfm.freetls.fastly.net/i/u/avatar170s/15e455555655c8503ed9ba6fce71d2d6.webp'


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
    assert info.get('bio') == 'Playing horror games all the time for charity.'
    assert info.get('fullname') == 'JohnWolfe'
    assert info.get('image') == 'https://static-cdn.jtvnw.net/jtv_user_pictures/johnwolfe-profile_image-61f8e374d34a8bbd-300x300.png'
    assert info.get('image_bg') == 'https://static-cdn.jtvnw.net/jtv_user_pictures/9d88705b5a305a7e-profile_banner-480.jpeg'
    assert 'views_count' in info
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
    assert info.get('gravatar_email_hash') == 'b1859c813547de1bba3c65bc4b1a217c'


def test_tproger():
    info = extract(parse('https://tproger.ru/author/NickPrice/')[0])

    assert info.get('fullname') == 'Никита Прияцелюк'
    assert info.get('image').startswith('https://secure.gravatar.com/avatar/b6c7803b43433349ff84b11093562594') == True


def test_jsfiddle():
    info = extract(parse('https://jsfiddle.net/user/john')[0])

    assert info.get('fullname') == 'John Michel'
    assert info.get('company') == 'Philadelphia, PA'
    assert info.get('links') == "['https://twitter.com/jhnmchl', 'https://github.com/johnmichel']"
    assert info.get('image') == 'https://www.gravatar.com/avatar/eca9f115bdefbbdf0c0381a58bcaf601?s=80'
    assert info.get('gravatar_url') == 'https://gravatar.com/eca9f115bdefbbdf0c0381a58bcaf601'
    assert info.get('gravatar_username') == 'cowbird'
    assert info.get('gravatar_email_hash') == 'eca9f115bdefbbdf0c0381a58bcaf601'


def test_disqus_api():
    info = extract(parse('https://disqus.com/api/3.0/users/details?user=username%3Amargaret&attach=userFlaggedUser&api_key=E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F')[0])

    assert info.get('id') == '1593'
    assert info.get('fullname') == 'margaret'
    assert info.get('reputation') == '1.231755'
    assert info.get('reputation_label') == 'Average'
    assert info.get('following_count') == '0'
    assert info.get('follower_count') == '0'
    assert info.get('is_power_contributor') == 'False'
    assert info.get('is_anonymous') == 'False'
    assert info.get('created_at') == '2007-11-06T01:14:28'
    assert info.get('likes_count') == '0'
    assert info.get('forums_count') == '0'
    assert info.get('image') == 'https://disqus.com/api/users/avatars/margaret.jpg'


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
