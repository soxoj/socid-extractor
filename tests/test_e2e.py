#!/usr/bin/env python3
import pytest

from socid_extractor.activation import get_twitter_headers
from socid_extractor.main import parse, extract


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


@pytest.mark.skip(reason="failed from github CI infra IPs")
def test_instagram():
    info = extract(parse('https://www.instagram.com/alexaimephotography/')[0])

    assert info.get('uid') == '6828488620'
    assert info.get('username') == 'alexaimephotography'
    assert info.get('fullname') == 'Alexaimephotography'
    assert info.get('biography') == """🇮🇹 🇲🇫 🇩🇪
Amateur photographer
Follow me @street.reality.photography
Sony A7ii"""
    assert info.get('external_url') == 'https://www.flickr.com/photos/alexaimephotography2020/'


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
    assert info.get('image') == '//habrastorage.org/getpro/habr/avatars/4ec/bd0/85d/4ecbd085d692835a931d03174ff19539.png'


def test_habr_no_image():
    info = extract(parse('https://habr.com/ru/users/ne555/')[0])

    assert info.get('uid') == '1800409'
    assert info.get('username') == 'ne555'
    assert not 'image' in info


def test_twitter_shadowban_no_account():
    info = extract(parse('https://shadowban.eu/.api/sgfrgrrr')[0])

    assert info.get('has_tweets') == 'False'
    assert info.get('is_exists') == 'False'
    assert info.get('username') == 'sgfrgrrr'
    assert not 'is_protected' in info
    assert not 'has_ban' in info
    assert not 'has_search_ban' in info
    assert not 'has_banned_in_search_suggestions' in info

def test_twitter_shadowban():
    info = extract(parse('https://shadowban.eu/.api/trump')[0])

    assert info.get('has_tweets') == 'True'
    assert info.get('is_exists') == 'True'
    assert info.get('username') == 'Trump'
    assert info.get('is_protected') == 'False'
    assert info.get('has_ban') == 'False'
    assert info.get('has_search_ban') == 'False'
    assert info.get('has_banned_in_search_suggestions') == 'False'


def test_twitter():
    _, headers = get_twitter_headers({})
    info = extract(parse('https://twitter.com/i/api/graphql/ZRnOhhXPwue_JGILb9TNug/UserByScreenName?variables=%7B%22screen_name%22%3A%22cardiakflatline%22%2C%22withHighlightedLabel%22%3Atrue%7D', headers=headers)[0])

    assert info.get('uid') == 'VXNlcjo0NTkyNjgxNg=='
    assert info.get('fullname') == 'Cardiak'
    assert info.get('bio') == '#Jersey Multi Platinum Grammy Award Winning Producer for J.Cole, DrDre,KendrickLamar, Eminem,MeekMill,RickRoss,Drake,Wale,Ace Hood,T.I,LloydBanks,Kanye,Fabolous'
    assert info.get('created_at') == '2009-06-09 19:59:57+00:00'
    assert info.get('image') == 'https://pbs.twimg.com/profile_images/745944619213557760/vgapfpjV.jpg'
    assert info.get('image_bg') == 'https://pbs.twimg.com/profile_banners/45926816/1487198278'
    assert info.get('is_protected') == 'False'
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


def test_facebook_group():
    info = extract(parse('https://www.facebook.com/discordapp/')[0])

    assert info.get('uid') == '858412104226521'
    assert info.get('username') == 'discord'


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
    assert info.get('is_bad_or_shock') == 'False'
    assert info.get('is_excluded_from_rating') == 'False'
    assert info.get('teaser') == 'Люблю Nike, спорт и активный образ жизни. С 2013 года я изучаю все, что связано с брендом NIke, веду блог.'
    assert info.get('facebook_username') == 'nikefansru/'
    assert info.get('instagram_username') == 'nikefans.ru'
    assert info.get('telegram_username') == 'nikefansru'
    assert info.get('vk_username') == 'nikejoy'
    assert 'answers_count' in info
    assert 'following_count' in info


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


def test_steam():
    info = extract(parse('https://steamcommunity.com/id/GabrielSantosMariano/')[0])

    assert info.get('uid') == '76561198315585536'
    assert info.get('username') == 'GabrielSantosMariano'
    assert info.get('nickname') == 'Gabriel! Santos, Mariano.'


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
    info = extract(parse('https://stackoverflow.com/users/758202/zzart')[0])

    assert info.get('uid') == '758202'
    assert info.get('stack_exchange_uid') == '395311'


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
    assert info.get('website') == 'www.patreon.com/musemercier'
    assert info.get('username') == 'Muse1908'
    assert info.get(
        'links') == "['https://www.facebook.com/musemercier', 'https://www.instagram.com/muse.mercier/', 'https://www.patreon.com/musemercier']"
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
    assert info.get('gravatar_username') == 'kostbebix'
    assert info.get('fullname') == 'kost BebiX'
    assert info.get('location') == 'Kiev, Ukraine'
    assert info.get('emails') == "['k.bx@ya.ru']"
    assert info.get('links') == "['http://twitter.com/kost_bebix']"


def test_pinterest_api():
    info = extract(parse('https://www.pinterest.ru/resource/UserResource/get/?source_url=%2Fgergelysndorszendrenyi%2Fboards%2F&data=%7B%22options%22%3A%7B%22isPrefetch%22%3Afalse%2C%22username%22%3A%22gergelysndorszendrenyi%22%2C%22field_set_key%22%3A%22profile%22%7D%2C%22context%22%3A%7B%7D%7D&_=1599342485938')[0])

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
    assert info.get('about').startswith('ICO Ольги Бузовой - Платформа BUZAR')

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
