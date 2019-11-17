#!/usr/bin/env python3
from socid_extractor import parse, extract


def test_vk_user_profile_full():
    info = extract(parse('https://vk.com/idsvyatoslavs'))

    assert info.get('uid') == '134173165'
    assert info.get('username') == 'idsvyatoslavs'
    assert info.get('name') == 'Святослав Степанов'


def test_vk_user_profile_no_username():
    info = extract(parse('https://vk.com/id568161939'))

    assert info.get('uid') == '568161939'
    assert info.get('username') == None
    assert info.get('name') == 'Юляшка Заболотная'


def test_yandex_disk():
    info = extract(parse('https://yadi.sk/d/KDk-D4vhGFbhb'))

    assert info.get('uid') == '106917461'
    assert info.get('name') == 'samografova.viktoria'


def test_instagram():
    info = extract(parse('https://www.instagram.com/xenia_sobchak/'))

    assert info.get('uid') == '21965519'
    assert info.get('username') == 'xenia_sobchak'

def test_medium():
    info = extract(parse('https://medium.com/@lys1n'))

    assert info.get('uid') == '4894fec6b289'
    assert info.get('username') == 'lys1n'
    assert info.get('twitter_username') == 'lys1n'
    assert info.get('name') == 'Марк Лясин'
    assert info.get('facebook_uid') == '1726256597385716'

def test_ok():
    info = extract(parse('https://ok.ru/profile/46054003'))

    assert info.get('uid') == '46054003'

def test_habr():
    info = extract(parse('https://habr.com/ru/users/m1rko/'))

    assert info.get('uid') == '1371978'
    assert info.get('username') == 'm1rko'

def test_twitter():
    info = extract(parse('https://twitter.com/esquireru'))

    assert info.get('uid') == '163060799'
    assert info.get('username') == 'Esquire Russia'
    assert info.get('name') == 'esquireru'

def test_reddit():
    info = extract(parse('https://www.reddit.com/user/sadlad111/'))

    assert info.get('uid') == 't2_4zmkfq8k'
    assert info.get('username') == 'sadlad111'

def test_facebook_user_profile():
    info = extract(parse('https://ru-ru.facebook.com/anatolijsharij/'))

    assert info.get('uid') == '1486042157'
    assert info.get('username') == 'anatolijsharij'

def test_facebook_group():
    info = extract(parse('https://www.facebook.com/discordapp/'))

    assert info.get('uid') == '858412104226521'
    assert info.get('username') == 'discordapp'

def test_github():
    info = extract(parse('https://github.com/soxoj'))

    assert info.get('uid') == '31013580'
    assert info.get('username') == 'soxoj'

def test_yandex_disk_photos():
    info = extract(parse('https://yadi.sk/a/oiySK_wg3Vv5p4'))

    assert info.get('uid') == '38569641'
    assert info.get('username') == 'nikitina-nm'
    assert info.get('name') == 'Вербочка'

def test_my_mail():
    info = extract(parse('https://my.mail.ru/mail/zubovo/'))

    assert info.get('uid') == '13425818'
    assert info.get('name') == 'Олег Зубов'
    assert info.get('username') == 'zubovo'
