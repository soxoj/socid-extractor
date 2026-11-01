"""Offline Lemmy response and URL-mutation regressions."""
import json
from pathlib import Path

import pytest

from socid_extractor.main import extract, mutate_url


@pytest.fixture
def lemmy_response():
    # Representative, minimized v3 response; optional profile values are neutral.
    return json.loads((Path(__file__).parent / 'fixtures' / 'lemmy-user.json').read_text())


def test_lemmy_profile_fields(lemmy_response):
    info = extract(json.dumps(lemmy_response))
    assert info['uid'] == '2'
    assert info['username'] == 'Dave'
    assert info['fullname'] == 'Dave'
    assert info['bio'] == 'A public profile biography'
    assert info['image'] == 'https://example.org/avatar.png'
    assert info['created_at'] == '2023-06-02T09:46:20.302035Z'


def test_lemmy_optional_fields(lemmy_response):
    person = lemmy_response['person_view']['person']
    for field in ['display_name', 'bio', 'avatar']:
        person.pop(field)
    info = extract(json.dumps(lemmy_response))
    assert info['uid'] == '2'
    assert info['username'] == 'Dave'
    assert not info.get('fullname')
    assert not info.get('bio')
    assert not info.get('image')


@pytest.mark.parametrize('body', [
    '{"error":"couldnt_find_person"}',
    '{"user":{"id":2,"name":"Dave"}}',
    '{"person":{"id":2},"counts":{}}',
    '<html><title>Unrelated site</title></html>',
    '{"person_view":null,"actor_id":"example","counts":{}}',
    '{"person_view":{"other":{"id":2}},"person":{},"actor_id":"example","counts":{},"published":"today"}',
])
def test_lemmy_does_not_extract_missing_or_unrelated_profiles(body):
    assert not extract(body).get('uid')


@pytest.mark.parametrize('username', ['Dave', 'test_user', 'test-user', 'Dave@lemmy.nz'])
def test_lemmy_profile_url_mutation(username):
    urls = [url for url, _ in mutate_url(f'https://lemmy.nz/u/{username}')]
    assert f'https://lemmy.nz/api/v3/user?username={username}' in urls


@pytest.mark.parametrize('url', ['https://example.org/u/Dave&admin=true', 'https://example.org/api/v4/user?username=Dave'])
def test_lemmy_does_not_mutate_unsafe_handles_or_other_api_versions(url):
    assert not any('/api/v3/' in mutated for mutated, _ in mutate_url(url))


def test_lemmy_api_url_is_not_mutated_again():
    assert not mutate_url('https://lemmy.nz/api/v3/user?username=Dave')
