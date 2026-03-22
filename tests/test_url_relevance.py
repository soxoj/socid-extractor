import sys

import pytest

from socid_extractor.url_relevance import STOPWORDS, _name_fallback_tokens, check_url_relevance


def test_check_url_relevance_linktree_hint():
    assert check_url_relevance('https://linktr.ee/example') is True


def test_check_url_relevance_odnoklassniki_hint():
    assert check_url_relevance('https://ok.ru/profile/1') is True


def test_check_url_relevance_habr_hint():
    assert check_url_relevance('https://habr.com/ru/users/x/') is True


def test_check_url_relevance_telegram_hint():
    assert check_url_relevance('https://t.me/durov') is True


def test_check_url_relevance_yandex_disk_yadisk():
    assert check_url_relevance('https://yadi.sk/d/abc') is True


def test_check_url_relevance_twitter_x_domain():
    assert check_url_relevance('https://x.com/elonmusk') is True


def test_check_url_relevance_instagram_hint():
    assert check_url_relevance('https://www.instagram.com/user/') is True


def test_check_url_relevance_no_match():
    assert check_url_relevance('https://example.com/anything') is False


def test_check_url_relevance_vk_fallback():
    assert check_url_relevance('https://vk.com/id1') is True


def test_name_fallback_respects_stopwords():
    toks = _name_fallback_tokens('GitHub API')
    assert 'api' not in toks
    assert 'github' in toks


def test_stopwords_is_expected_set():
    assert 'user' in STOPWORDS
    assert 'api' in STOPWORDS


def test_cli_skips_fetch_when_no_hint(monkeypatch):
    from socid_extractor.cli import run

    calls = []

    def fake_parse(*a, **k):
        calls.append(a[0])
        return '', 200

    monkeypatch.setattr('socid_extractor.cli.parse', fake_parse)
    monkeypatch.setattr(sys, 'argv', ['socid_extractor', '--url', 'https://example.com/nope', '--skip-fetch-if-no-url-hint'])
    run()
    assert calls == []


def test_cli_fetches_without_flag_even_if_no_hint(monkeypatch):
    from socid_extractor.cli import run

    calls = []

    def fake_parse(*a, **k):
        calls.append(a[0])
        return '', 200

    monkeypatch.setattr('socid_extractor.cli.parse', fake_parse)
    monkeypatch.setattr(sys, 'argv', ['socid_extractor', '--url', 'https://example.com/nope'])
    run()
    assert len(calls) >= 1


def test_cli_fetches_with_flag_when_hint_matches(monkeypatch):
    from socid_extractor.cli import run

    calls = []

    def fake_parse(*a, **k):
        calls.append(a[0])
        return '', 200

    monkeypatch.setattr('socid_extractor.cli.parse', fake_parse)
    monkeypatch.setattr(
        sys,
        'argv',
        ['socid_extractor', '--url', 'https://vk.com/id1', '--skip-fetch-if-no-url-hint'],
    )
    run()
    assert len(calls) >= 1
