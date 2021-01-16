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

    assert info.get('fullname') in ('Александр Чудаев')


def test_vk_blocked_user_profile():
    headers = {'User-Agent': 'Curl'}
    info = extract(parse('https://vk.com/alexaimephotography', headers=headers)[0])

    assert info.get('fullname') in ('Alex Aimé')


def test_yandex_disk():
    info = extract(parse('https://yadi.sk/d/xRJFp3s2QWYv8')[0])

    assert info.get('yandex_uid') == '225171618'
    assert info.get('name') == 'Trapl  Zdenek'


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


# @pytest.mark.skip(reason="broken, https://github.com/soxoj/socid_extractor/issues/3")
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
    assert info.get('follower_count') == '46323'
    assert info.get('following_count') == '1469'
    assert info.get('location') == 'Los Angeles, CA'
    assert info.get('favourites_count') == '1180'


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


def test_github():
    info = extract(parse('https://github.com/soxoj')[0])

    assert info.get('uid') == '31013580'
    assert info.get('username') == 'soxoj'


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


@pytest.mark.skip(reason="empty result, additional header needed")
def test_yandex_music_user_profile():
    info = extract(parse('https://music.yandex.ru/handlers/library.jsx?owner=pritisk')[0])

    assert info.get('yandex_uid') == '16480689'
    assert info.get('username') == 'pritisk'
    assert info.get('name') == 'Юрий Притиск'


def test_yandex_znatoki_user_profile():
    info = extract(parse('https://yandex.ru/znatoki/user/e3795016-b18e-58ba-9112-21c301e53f37/')[0])

    assert info.get('uid') == 'e3795016-b18e-58ba-9112-21c301e53f37'
    assert info.get('yandex_uid') == '980797984'
    assert info.get('name') == 'Настя Рогозинская'


def test_behance():
    info = extract(parse('https://www.behance.net/Skyratov', 'ilo0=1')[0])

    assert info.get('uid') == '39065909'
    assert info.get('username') == 'Skyratov'
    assert info.get('last_name') == 'Skuratov'
    assert info.get('first_name') == 'Vasiliy'


def test_500px():
    info = extract(parse('https://api.500px.com/graphql?operationName=ProfileRendererQuery&variables=%7B%22username%22%3A%22the-maksimov%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%225a17a9af1830b58b94a912995b7947b24f27f1301c6ea8ab71a9eb1a6a86585b%22%7D%7D')[0])

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

    assert info.get('contribution_level') == 'Level 3 Local Guide | 132 Points'
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
    assert info.get('sex') == 'm'
    assert info.get('likes') == '0'
    assert info.get('cards') == '0'
    assert info.get('boards') == '0'
    assert info.get('is_passport') == 'True'
    assert info.get('is_restricted') == 'False'
    assert info.get('is_forbid') == 'False'
    assert info.get('is_km') == 'False'
    assert info.get('is_business') == 'False'


def test_tiktok():
    info = extract(parse('https://www.tiktok.com/@red')[0])

    assert info.get('tiktok_id') == '6667977707978850310'
    assert info.get('tiktok_username') == 'red'
    assert info.get('fullname') == '(RED)'
    assert info.get('bio') == 'Whether AIDS or COVID-19, we can’t beat pandemics without strong health systems.'
    assert 'tiktokcdn.com' in info.get('image')
    assert info.get('is_verified') == 'True'
    assert info.get('is_secret') == 'False'
    assert info.get('sec_uid') == 'MS4wLjABAAAAVAp3JR-xHP7UnaDt4S9T9eyPqRDwgGiBRnzdZRm63jIGWy5s39a027nKJlu_UjOZ'
    assert int(info.get('following_count')) > 300
    assert int(info.get('follower_count')) > 36000
    assert int(info.get('heart_count')) > 275900
    assert int(info.get('video_count')) > 50
    assert info.get('digg_count') == '0'


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
