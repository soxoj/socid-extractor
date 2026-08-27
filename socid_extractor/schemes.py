from dateutil.parser import parse as parse_datetime_str
import html
import json
import itertools
from urllib.parse import unquote

from .utils import *


# Helpers for the Virgool RSC profile scheme (see "Virgool" entry below).
def _virgool_parse_rsc_rows(chunk_text):
    """Split an RSC push payload into ``{chunk_id: parsed_json}``.

    Each row in an RSC push has the shape ``"<hex_id>:<json>\\n"``;
    rows that do not parse as JSON are skipped silently (RSC bookkeeping
    rows like ``10:[[...]]`` whose body is a list, not the profile).
    """
    rows = {}
    for line in chunk_text.split('\n'):
        if ':' not in line:
            continue
        rid, _, body = line.partition(':')
        body = body.strip()
        if not body:
            continue
        try:
            rows[rid.strip()] = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            continue
    return rows


def _virgool_user_row_from_chunk(chunk_text):
    """Find the Virgool profile object inside an RSC push payload.

    Picks the first parsed row that *looks like* the profile object
    (must contain both ``username`` and ``followersCount``), then
    one-level-resolves any ``"$<chunk_id>"`` cross-row references in
    that object's top-level fields (e.g. ``socials``).
    """
    rows = _virgool_parse_rsc_rows(chunk_text)

    user_row = None
    for value in rows.values():
        if (isinstance(value, dict)
                and 'followersCount' in value
                and 'username' in value):
            user_row = value
            break

    if user_row is None:
        raise ValueError('virgool: no SSR user row found in RSC push payload')

    resolved = dict(user_row)
    for key, value in user_row.items():
        if isinstance(value, str) and len(value) > 1 and value.startswith('$'):
            ref = value[1:]
            if ref in rows:
                resolved[key] = rows[ref]
    return resolved


def _virgool_socials_dict(user_row):
    """Normalise ``socials`` to a flat ``{platform: handle}`` dict.

    Two shapes have been observed in the wild:

    * dict form (current SSR shape): ``{"twitter":"00397","linkedin":null}``
    * list form (older docs / API shape): ``[{"type":"twitter","url":"..."}]``

    Anything that is `None`/empty/missing is dropped so callers do not
    have to distinguish "field present but null" from "field absent".
    """
    socials = user_row.get('socials')
    out = {}
    if isinstance(socials, dict):
        for platform, handle in socials.items():
            if handle:
                out[str(platform).lower()] = str(handle)
    elif isinstance(socials, list):
        for item in socials:
            if not isinstance(item, dict):
                continue
            platform = item.get('type') or item.get('platform')
            url = item.get('url') or item.get('handle')
            if platform and url:
                out[str(platform).lower()] = str(url)
    return out


def _virgool_social(user_row, platform):
    return _virgool_socials_dict(user_row).get(platform.lower())


def _virgool_links(user_row):
    canonical = {
        'twitter': 'https://twitter.com/{}',
        'linkedin': 'https://www.linkedin.com/in/{}',
        'instagram': 'https://www.instagram.com/{}',
        'github': 'https://github.com/{}',
        'telegram': 'https://t.me/{}',
    }
    socials = _virgool_socials_dict(user_row)
    links = []
    for platform, handle in socials.items():
        if handle.startswith('http://') or handle.startswith('https://'):
            links.append(handle)
        elif platform in canonical:
            links.append(canonical[platform].format(handle))
        else:
            links.append(handle)
    return links


# Insert this entry inside the `schemes = { ... }` dict, after `Flickr`
# and before `Yandex Disk file`. Same shape as `Flickr` /
# `Yandex Q (Znatoki) user profile`: `extract_json` + `transforms` chain.


def _gh_handle_for(accounts, provider):
    for a in accounts:
        if a.get('provider') == provider:
            url = (a.get('url') or '').split('?')[0].split('#')[0].rstrip('/')
            handle = url.rsplit('/', 1)[-1].lstrip('@') or None
            if provider == 'bluesky' and handle:
                return handle.removesuffix('.bsky.social')
            return handle
    return None


def _bio_site_section(profile, section_type):
    for item in profile.get('body') or []:
        if item.get('type') == section_type:
            return item.get('section') or {}
    return {}


def _bio_site_social_handles(profile):
    return _bio_site_section(profile, 'section_social').get('handles') or []


def _bio_site_links(profile):
    urls = []
    for handle in _bio_site_social_handles(profile):
        if handle.get('url'):
            urls.append(handle.get('url'))

    links_section = _bio_site_section(profile, 'section_links')
    for link in links_section.get('links') or []:
        if link.get('url'):
            urls.append(link.get('url'))
    return urls


def _bio_site_social_value(profile, provider):
    for handle in _bio_site_social_handles(profile):
        if handle.get('type') == provider:
            return handle.get('value')
    return None


def _faceit_current_game(profile):
    games = profile.get('games') or {}
    game_key = profile.get('flag')
    if game_key and isinstance(games.get(game_key), dict):
        return games[game_key]
    for game in games.values():
        if isinstance(game, dict):
            return game
    return {}


def _faceit_streaming_links(profile):
    streaming = profile.get('streaming') or {}
    links = {}
    for platform, handle in streaming.items():
        if handle:
            links[platform.removesuffix('_id')] = handle
    return links


def _yt_redirect_urls(data):
    """Collect external destination URLs from youtube.com/redirect?...q= links in ytInitialData."""
    urls = set()
    for u in re.findall(r'youtube\.com/redirect\?[^"]*?q=([^"&]+)', json.dumps(data)):
        decoded = unquote(u)
        if 'youtube.com' not in decoded and 'google.com' not in decoded:
            urls.add(decoded)
    return list(urls)


def _yt_find_about(data):
    """Depth-first search for the aboutChannelViewModel dict, wherever YouTube nests it."""
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            about = node.get('aboutChannelViewModel')
            if isinstance(about, dict):
                return about
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return {}


def _yt_social_username(data, domain):
    """Extract a username from YouTube redirect URLs for a given social platform domain."""
    for url in data.get('_all_redirect_urls', []):
        if domain in url.lower():
            path = re.sub(r'https?://(www\.|[a-z]{2}\.)?', '', url).split('/')
            if len(path) >= 2 and path[1]:
                username = path[1].rstrip('/')
                if username and username not in ('invite',):
                    return username
            if 'invite' in url and len(path) >= 3:
                return path[2].rstrip('/')
    return None


def _lens_attr(attrs, *keys):
    """Return the first Lens metadata attribute value whose key matches any of `keys`."""
    if not attrs:
        return None
    wanted = {k.lower() for k in keys}
    for a in attrs:
        if isinstance(a, dict) and str(a.get('key', '')).lower() in wanted and a.get('value'):
            return a['value']
    return None


# ==========================================================================
#  Helpers for the schemes merged in from the extended plugin pack
# ==========================================================================

def _discourse_user_field(soup, field):
    """Extract a field from Discourse data-preloaded user JSON embedded in HTML.

    Falls back to <title> for username when user data is missing
    (e.g. on /summary pages where Discourse doesn't embed user JSON).
    """
    tag = soup.find(id='data-preloaded')
    if tag and tag.get('data-preloaded'):
        raw = tag['data-preloaded']
        m = re.search(r'"user_\w+":"(.*?)"(?:,"|\}$)', raw)
        if m:
            inner = m.group(1).replace('\\"', '"')
            try:
                data = json.loads(inner)
            except (json.JSONDecodeError, ValueError):
                data = {}
            user = data.get('user', {})
            val = user.get(field)
            if val is not None:
                return val

    # Fallback: extract username from <title>Profile - {username} - {site}</title>
    if field == 'username':
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            tm = re.match(r'\s*Profile\s*-\s*(.+?)\s*-\s*', title_tag.string)
            if tm:
                return tm.group(1)
    return None


def _osu_field(soup, field):
    """Extract a field from osu! data-initial-data JSON embedded in HTML."""
    tag = soup.find(attrs={'data-initial-data': True})
    if not tag:
        return None
    try:
        data = json.loads(tag['data-initial-data'])
    except (json.JSONDecodeError, ValueError, KeyError):
        return None
    return data.get('user', {}).get(field)


def _fl_ld(soup, *keys):
    """Extract a nested value from FL.ru JSON-LD (application/ld+json)."""
    tag = soup.find('script', type='application/ld+json')
    if not tag or not tag.string:
        return None
    try:
        data = json.loads(tag.string)
    except (json.JSONDecodeError, ValueError):
        return None
    for k in keys:
        if isinstance(data, dict):
            data = data.get(k)
        else:
            return None
    return data or None


def _meta(soup, prop, attr='content', tag_attr='property'):
    """Return value from <meta {tag_attr}="{prop}" {attr}="..."/> or None."""
    tag = soup.find('meta', {tag_attr: prop})
    if not tag:
        return None
    return tag.get(attr)


def _meta_re(soup, prop, pattern, group=1, tag_attr='property'):
    """Apply regex pattern to a meta tag's content; return capture group or None."""
    val = _meta(soup, prop, tag_attr=tag_attr)
    if not val:
        return None
    m = re.search(pattern, val)
    return m.group(group) if m else None


def _wikidot_field(soup, label):
    """Wikidot profile-box has <dl><dt>label:</dt><dd>value</dd></dl>.
    Find the <dt> matching the label and return the next <dd> text."""
    box = soup.find(class_='profile-box')
    if not box:
        return None
    for dt in box.find_all('dt'):
        if dt.get_text(strip=True).rstrip(':') == label:
            dd = dt.find_next_sibling('dd')
            if dd:
                return dd.get_text(' ', strip=True) or None
    return None


def _sc_value(soup, label, strip=None):
    """Star Citizen profile field lookup: find <p class="entry"> with given
    <span class="label">label</span> and return its <strong class="value">."""
    for entry in soup.select('p.entry'):
        label_tag = entry.find('span', class_='label')
        if label_tag and label_tag.get_text(strip=True) == label:
            value_tag = entry.find('strong', class_='value')
            if value_tag:
                text = ' '.join(value_tag.get_text(' ', strip=True).split())
                if strip:
                    text = text.lstrip(strip)
                return text or None
    return None


# ═══════════════════════════════════════════════════════════════════
#  Instance lists for platform families
# ═══════════════════════════════════════════════════════════════════

_MASTODON_INSTANCES = [
    'vmst.io',
    'tilde.zone',
    'masto.nyc',
    'graphics.social',
    'expressional.social',
    'federated.press',
    'libretooth.gr',
    'hostux.social',
    'mapstodon.space',
    'hcommons.social',
    'hometech.social',
    'nitecrew.rip',
    'poweredbygay.social',
    'vkl.world',
    'tooting.ch',
    'c.im',
    'masto.ai',
    'mastodon.online',
    'toot.community',
    'defcon.social',
    'social.bund.de',
    'toot.cat',
    'infosec.exchange',
]

_DISCOURSE_INSTANCES = [
    'community.openai.com',
    'blenderartists.org',
    'discourse.flathub.org',
    'discussions.unity.com',
    'forums.unrealengine.com',
    'community.shopify.com',
    'community.plotly.com',
    'discuss.streamlit.io',
    'forums.meteor.com',
    'forums.eveonline.com',
    'forums.comodo.com',
    'discuss.kde.org',
    'discuss.rubyonrails.org',
    'discuss.ai.google.dev',
    'discussion.fedoraproject.org',
    'twittercommunity.com',
    'forums.spongepowered.org',
    'community.e.foundation',
    'community.netdata.cloud',
    'community.norton.com',
    'community.trading212.com',
    'community.humanetech.com',
    'forum.djangoproject.com',
    'forum.crystal-lang.org',
    'forum.dfinity.org',
    'forum.hackthebox.com',
    'forums.powershell.org',
    'forum.polkadot.network',
    'forum.modular.com',
    'forum.shopware.com',
    'internals.rust-lang.org',
    'krita-artists.org',
    'root-forum.cern.ch',
    'erlangforums.com',
    'tosdr.community',
    'ziggit.dev',
    'community.bunpro.jp',
    'discuss.ray.io',
    'forum.jscourse.com',
    'forum.valuepickr.com',
]


schemes = {
    # IMPORTANT: extract() returns the FIRST matching scheme.
    # More specific schemes (more/stricter flags) must come BEFORE
    # generic ones to avoid shadowing. Example: 'Wikipedia user API'
    # (flags: "batchcomplete" + "editcount") before 'Fandom MediaWiki API'
    # (flags: "batchcomplete" + "query" + "users").

    # unactual
    'Twitter HTML': {
        'url_hints': ('twitter.com', 'x.com', 'twimg.com'),
        'flags': ['abs.twimg.com', 'moreCSSBundles'],
        'regex': r'{&quot;id&quot;:(?P<uid>\d+),&quot;id_str&quot;:&quot;\d+&quot;,&quot;name&quot;:&quot;(?P<username>.*?)&quot;,&quot;screen_name&quot;:&quot;(?P<name>.*?)&quot;'
    },
    # QQ Qzone portrait: users.qzone.qq.com/fcg-bin/cgi_get_portrait.fcg?uins={qq}
    # JSONP array: ["<avatar_url>",<size>,...,"<nickname>",0]; empty nickname = no such account
    'QQ Qzone portrait': {
        'url_hints': ('qzone.qq.com', 'cgi_get_portrait'),
        'flags': ['portraitCallBack('],
        'regex': r'portraitCallBack\(\{"\d+":\["(?P<image>[^"]*)"(?:,-?\d+)+,"(?P<fullname>[^"]+)"',
    },
    # Bilibili user card: api.bilibili.com/x/web-interface/card?mid={uid}
    'Bilibili card': {
        'url_hints': ('api.bilibili.com', 'web-interface/card'),
        'flags': ['"card":{', '"mid":'],
        'regex': r'^({.+})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['data']['card'].get('mid'),
            'fullname': lambda x: x['data']['card'].get('name'),
            'image': lambda x: x['data']['card'].get('face'),
            'bio': lambda x: x['data']['card'].get('sign'),
            'sex': lambda x: x['data']['card'].get('sex'),
            'fans': lambda x: x['data']['card'].get('fans'),
        },
    },
    # https://shadowban.eu/.api/user
    # https://gist.github.com/superboum/ab31bc4c85c731b9e89ebda5eaed9a3a
    'Twitter Shadowban': {
        'url_hints': ('twitter.com', 'x.com', 'shadowban.eu'),
        'flags': ['"timestamp"', '"profile": {', 'has_tweets'],
        'regex': r'^({.+?})$',
        'extract_json': True,
        'fields': {
            'has_tweets': lambda x: x['profile'].get('has_tweets'),
            'username': lambda x: x['profile'].get('screen_name'),
            'is_exists': lambda x: x['profile'].get('exists'),
            'is_suspended': lambda x: x['profile'].get('suspended'),
            'is_protected': lambda x: x['profile'].get('protected'),
            'has_ban': lambda x: x.get('tests', {}).get('ghost', {}).get('ban'),
            'has_banned_in_search_suggestions': lambda x: not x['tests']['typeahead'] if x.get('tests', {}).get('typeahead') else None,
            'has_search_ban': lambda x: not x['tests']['search'] if x.get('tests', {}).get('search') else None,
            'has_never_replies': lambda x: not x['tests']['more_replies']['tweet'] if x.get('tests', {}).get('more_replies', {}).get('tweet') else None,
            'is_deboosted': lambda x: x['tests']['more_replies']['ban'] if x.get('tests', {}).get('more_replies', {}).get('ban') else None,
        }
    },
    'Twitter GraphQL API': {
        # X API may emit fields before "id" inside user{...}; keep flags aligned with live JSON
        'url_hints': ('twitter.com', 'x.com', 'twimg.com'),
        'flags': ['{"data":{"user"', '"legacy":'],
        'regex': r'^{"data":{"user":({.+})}}$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www.)?twitter.com/(?P<username>[^/]+).*',
                'to': 'https://twitter.com/i/api/graphql/ZRnOhhXPwue_JGILb9TNug/UserByScreenName?variables=%7B%22screen_name%22%3A%22{username}%22%2C%22withHighlightedLabel%22%3Atrue%7D',
            }
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'fullname': lambda x: x.get('legacy', {}).get('name'),
            'bio': lambda x: x.get('legacy', {}).get('description'),
            'created_at': lambda x: parse_datetime_str(x.get('legacy', {}).get('created_at', '')),
            'image': lambda x: x.get('legacy', {}).get('profile_image_url_https', '').replace('_normal', ''),
            'image_bg': lambda x: x.get('legacy', {}).get('profile_banner_url'),
            'is_protected': lambda x: x.get('legacy', {}).get('protected'),
            'follower_count': lambda x: x.get('legacy', {}).get('followers_count'),
            'following_count': lambda x: x.get('legacy', {}).get('friends_count'),
            'location': lambda x: x.get('legacy', {}).get('location'),
            'favourites_count': lambda x: x.get('legacy', {}).get('favourites_count'),
            'links': lambda x: [y.get('expanded_url') for y in x.get('legacy', {}).get('entities', {}).get('url', {}).get('urls', [])],
        }
    },
    'Facebook user profile': {
        'url_hints': ('facebook.com', 'fb.com', 'm.facebook.com'),
        'flags': ['<html id="facebook"', 'property="og:title"'],
        'bs': True,
        'fields': {
            'uid': lambda x: x.find('meta', {'property': 'al:android:url'})['content'].replace('fb://profile/', ''),
            'username': lambda x: x.find('meta', {'property': 'og:url'})['content'].strip('/').split('/')[-1],
            'fullname': lambda x: x.find('meta', {'property': 'og:title'})['content'],
            'description': lambda x: x.find('meta', {'property': 'og:description'})['content'],
            'image': lambda x: x.find('meta', {'property': 'og:image'})['content'],
        },
        'url_mutations': [
            {
                'from': r'https?://(?:[\w-]+\.)?(?:facebook\.com|fb\.com)/(?P<username>[^/?#]+)',
                'to': 'https://www.facebook.com/{username}',
                'headers': {'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)'},
            },
        ],
    },
    'Facebook group': {
        'url_hints': ('facebook.com', 'fb.com'),
        'flags': ['com.facebook.katana', 'XPagesProfileHomeController'],
        'regex': r'{"imp_id":".+?","ef_page":.+?,"uri":".+?\/(?P<username>[^\/]+?)","entity_id":"(?P<uid>\d+)"}',
    },
    # https://api.github.com/users/torvalds
    'GitHub API': {
        'url_hints': ('api.github.com', 'github.com'),
        'flags': ['gists_url', 'received_events_url'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'^https?://(?:www\.)?github\.com/(?P<username>[^/?#]+)/?$',
                'to': 'https://api.github.com/users/{username}',
            }
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'image': lambda x: x.get('avatar_url'),
            'created_at': lambda x: x.get('created_at'),
            'location': lambda x: x.get('location'),
            'follower_count': lambda x: x.get('followers'),
            'following_count': lambda x: x.get('following'),
            'fullname': lambda x: x.get('name'),
            'public_gists_count': lambda x: x.get('public_gists'),
            'public_repos_count': lambda x: x.get('public_repos'),
            'twitter_username': lambda x: x.get('twitter_username'),
            'is_looking_for_job': lambda x: x.get('hireable'),
            'gravatar_id': lambda x: x.get('gravatar_id'),
            'bio': lambda x: x['bio'].strip() if x.get('bio', '') else None,
            'company': lambda x: x.get('company'),
            'blog_url': lambda x: x.get('blog'),
        }
    },
    # https://api.github.com/users/torvalds/social_accounts
    # Separate endpoint that lists Bluesky, Mastodon, LinkedIn, YouTube,
    # Twitch, etc. — fields the main /users/{u} response omits.
    'GitHub Social Accounts API': {
        'url_hints': ('api.github.com',),
        'flags': ['"provider":', '"url":', 'https://'],
        'regex': r'^(\[[\s\S]+\])$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: {'accounts': x},
            json.dumps,
        ],
        'url_mutations': [
            {
                'from': r'^https?://(?:www\.)?github\.com/(?P<username>[^/?#]+)/?$',
                'to': 'https://api.github.com/users/{username}/social_accounts',
            }
        ],
        'fields': {
            'links': lambda x: [a['url'] for a in x['accounts'] if a.get('url')] or None,
            'twitter_username': lambda x: _gh_handle_for(x['accounts'], 'twitter'),
            'bluesky_username': lambda x: _gh_handle_for(x['accounts'], 'bluesky'),
            'mastodon_username': lambda x: _gh_handle_for(x['accounts'], 'mastodon'),
            'linkedin_username': lambda x: _gh_handle_for(x['accounts'], 'linkedin'),
            'youtube_username': lambda x: _gh_handle_for(x['accounts'], 'youtube'),
            'twitch_username': lambda x: _gh_handle_for(x['accounts'], 'twitch'),
            'facebook_username': lambda x: _gh_handle_for(x['accounts'], 'facebook'),
            'instagram_username': lambda x: _gh_handle_for(x['accounts'], 'instagram'),
            'reddit_username': lambda x: _gh_handle_for(x['accounts'], 'reddit'),
        }
    },
    'Gitlab API': {
        'url_hints': ('gitlab.com',),
        'flags': ['avatar_url', 'https://gitlab.com', '"public_email"'],
        'regex': r'^\[({[\S\s]+?})\]$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https://gitlab.com/(?P<username>.+)/?',
                'to': 'https://gitlab.com/api/v4/users?username={username}',
            }
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'fullname': lambda x: x.get('name'),
            'username': lambda x: x.get('username'),
            'state': lambda x: x.get('state'),
            'image': lambda x: x.get('avatar_url'),
            'website': lambda x: x.get('web_url') or None,
            'email': lambda x: x.get('public_email') or None,
            'emails': lambda x: ([x['public_email']] if x.get('public_email') else None),
        }
    },
    'Patreon': {
        'url_hints': ('patreon.com',),
        'flags': ['www.patreon.com/api', 'pledge_url'],
        'regex': r'Object.assign\(window.patreon.bootstrap, ([\s\S]*)\);[\s\S]*Object.assign\(window.patreon.campaignFeatures, {}\);',
        'extract_json': True,
        'fields': {
            'patreon_id': lambda x: x['campaign']['included'][0]['id'],
            'patreon_username': lambda x: x['campaign']['included'][0]['attributes']['vanity'],
            'fullname': lambda x: x['campaign']['included'][0]['attributes']['full_name'],
            'links': lambda x: [y['attributes'].get('external_profile_url') for y in x['campaign']['included'] if
                                y['attributes'].get('app_name')],
            'image': lambda x: x['campaign']['data']['attributes']['avatar_photo_url'],
            'image_bg': lambda x: x['campaign']['data']['attributes']['cover_photo_url'],
            'is_nsfw': lambda x: x['campaign']['data']['attributes']['is_nsfw'],
            'created_at': lambda x: x['campaign']['data']['attributes']['published_at'],
            'bio': lambda x: x['campaign']['data']['attributes']['summary'],
        }
    },
    'Flickr': {
        'url_hints': ('flickr.com',),
        'flags': ['api.flickr.com', 'photostream-models', 'person-profile-models'],
        'regex': r'modelExport:(.*),[\s\S]*auth',
        'extract_json': True,
        'transforms': [
            lambda x: x.replace('%20', ' '),
            lambda x: x.replace('%2C', ','),
            json.loads,
            lambda x: x['main'],
            json.dumps,
        ],
        'fields': {
            'flickr_id': lambda x: x['photostream-models'][0]['owner']['id'],
            'flickr_username': lambda x: x['photostream-models'][0]['owner'].get('pathAlias'),
            'flickr_nickname': lambda x: x['photostream-models'][0]['owner']['username'],
            'fullname': lambda x: x['photostream-models'][0]['owner'].get('realname'),
            'location': lambda x: x['person-profile-models'][0].get('location'),
            'image': lambda x: 'https:' + x['photostream-models'][0]['owner']['buddyicon']['retina'],
            'photos_count': lambda x: x['person-profile-models'][0]['photoCount'],
            'follower_count': lambda x: x['person-contacts-count-models'][0]['followerCount'],
            'following_count': lambda x: x['person-contacts-count-models'][0]['followingCount'],
            'created_at': lambda x: parse_datetime(x['photostream-models'][0]['owner'].get('dateCreated', 0)),
            'is_pro': lambda x: x['photostream-models'][0]['owner'].get('isPro'),
            'is_deleted': lambda x: x['photostream-models'][0]['owner'].get('isDeleted'),
            'is_ad_free': lambda x: x['photostream-models'][0]['owner'].get('isAdFree'),
        }
    },
    'Virgool': {
        # https://virgool.io/@<username> — Persian blog platform; SSR is
        # Next.js 13/14 React Server Components. The profile JSON ships
        # inside `self.__next_f.push([1,"<chunk_id>:<escaped JSON>"])`,
        # so on the wire each `"` of the inner JSON is escape-quoted as
        # `\"`. Both flags are required: gating on `__next_f.push` alone
        # would catch every Next.js site, and `\"followersCount\"` keeps
        # the scheme from firing on Virgool 404 / JS-cookie-wall bodies
        # (none of those contain that substring).
        'url_hints': ('virgool.io',),
        'flags': ['__next_f.push', '\\"followersCount\\"'],
        'regex': r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*\\"followersCount\\"(?:[^"\\]|\\.)*")\]',
        'extract_json': True,
        'transforms': [
            # 1. The captured group is a JS string literal; json.loads
            #    decodes it into the multi-row RSC text.
            json.loads,
            # 2. Walk the rows, find the user object, resolve cross-row refs.
            _virgool_user_row_from_chunk,
            # 3. main.extract() will json.loads(transformed) next, so we
            #    have to hand it back a JSON string.
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name'),
            # Virgool exposes no numeric `id` on the SSR path; `hash` is
            # the stable public profile identifier.
            'uid': lambda x: x.get('hash'),
            'bio': lambda x: x.get('bio'),
            'image': lambda x: x.get('avatar'),
            'follower_count': lambda x: x.get('followersCount'),
            'following_count': lambda x: x.get('followingCount'),
            'feed_url': lambda x: x.get('feed'),
            'profile_url': lambda x: x.get('url'),
            'links': lambda x: _virgool_links(x),
            'twitter_username': lambda x: _virgool_social(x, 'twitter'),
            'linkedin_username': lambda x: _virgool_social(x, 'linkedin'),
            'instagram_username': lambda x: _virgool_social(x, 'instagram'),
            'github_username': lambda x: _virgool_social(x, 'github'),
            'telegram_username': lambda x: _virgool_social(x, 'telegram'),
        },
    },
    'Yandex Disk file': {
        'url_hints': ('yadi.sk', 'disk.yandex', 'yandex.ru'),
        'flags': ["project:'disk-public',page:'icon'", '@yandexdisk', 'yastatic.net'],
        'regex': r'"users":{.*?"uid":"(?P<yandex_uid>\d+)","displayName":"(?P<name>.+?)"',
    },
    'Yandex Disk photoalbum': {
        'url_hints': ('yadi.sk', 'disk.yandex', 'yandex.ru'),
        'flags': ["project:'disk-public',page:'album'"],
        'regex': r'"users":{.*?"uid":"(?P<yandex_uid>\d+)","displayName":"(?P<name>.+?)"',
    },
    'Yandex Music AJAX request': {
        'flags': ['{"success":true,"verified'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://music.yandex.ru/users/(?P<username>[^/]+).*',
                'to': 'https://music.yandex.ru/handlers/library.jsx?owner={username}',
                'headers': {"Referer": "https://music.yandex.ru/users/test/playlists"},
            }
        ],
        'fields': {
            'yandex_uid': lambda x: x['owner']['uid'],
            'username': lambda x: x['owner']['login'],
            'name': lambda x: x['owner']['name'],
            'image': lambda x: get_yandex_profile_pic(x['owner']['avatarHash']),
            'links': lambda x: [link for links in x['profiles'] for link in links['addresses']],
            'is_verified': lambda x: x['verified'],
            'liked_albums': lambda x: x['counts'].get('likedAlbums'),
            'liked_artists': lambda x: x['counts'].get('likedArtists'),
            'has_tracks': lambda x: x.get('hasTracks'),
        }
    },
    'Yandex Q (Znatoki) user profile': {
        'flags': ['Ya.Znatoki'],
        'regex': r'id="restoreData" type="application/json">({.+?})</script>',
        'extract_json': True,
        'transforms': [
            html.unescape,
            json.loads,
            lambda x: x['store']['entities'].get('user', {'':{}})[x['store']['page'].get('userStats', {}).get('id', '')],
            json.dumps,
        ],
        'fields': {
            'yandex_znatoki_id': lambda x: x['id'],
            'yandex_uid': lambda x: x['uuid'],
            'bio': lambda x: x['about'],
            'name': lambda x: x['displayName'],
            'image': lambda x: get_yandex_profile_pic(x.get('avatarId')),
            'is_org': lambda x: x.get('authOrg'),
            'is_banned': lambda x: x['banned'],
            'is_deleted': lambda x: x['deleted'],
            'created_at': lambda x: x['created'],
            'last_answer_at': lambda x: x.get('lastAnswerTime'),
            'rating': lambda x: x['rating'],
            'gender': lambda x: x['sex'],
            'links': lambda x: list(set(filter(lambda x: x, [x['url'], x.get('promoUrl'), x.get('socialContactUrl')]))),
            'verified_categories': lambda x: x.get('verifiedIn'),
            'is_from_q': lambda x: x.get('theqMerged'),
            'is_bad_or_shock': lambda x: x.get('badOrShock'),
            'is_excluded_from_rating': lambda x: x.get('excludeFromRating'),
            'teaser': lambda x: x.get('teaser'),
            'facebook_username': lambda x: x['socialFacebook'],
            'instagram_username': lambda x: x['socialInstagram'],
            'telegram_username': lambda x: x['socialTelegram'],
            'twitter_username': lambda x: x['socialTwitter'],
            'vk_username': lambda x: x['socialVkontakte'],
            'answers_count': lambda x: x.get('stats', {}).get('answersCount'),
            'following_count': lambda x: x.get('stats', {}).get('subscribersCount'),
        }
    },
    # TODO: rework
    'Yandex Market user profile': {
        'flags': ['MarketNode', '{"entity":"user"'],
        'regex': r'>{"widgets":{"@MarketNode/MyArticles/ArticlesGrid.+?"collections":({"publicUser":{"\d+".+?}}})}<',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: list(x['publicUser'].values())[0],
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('login'),
            'yandex_uid': lambda x: x.get('uid'),
            'yandex_public_id': lambda x: x.get('publicId'),
            'fullname': lambda x: x.get('publicDisplayName'),
            'image': lambda x: x.get('avatar').replace('//', 'https://').replace('retina-50', '200'),
            'reviews_count': lambda x: x.get('grades'),
            'is_deleted': lambda x: x.get('isDeleted'),
            'is_hidden_name': lambda x: x.get('isDisplayNameEmpty'),
            'is_verified': lambda x: x.get('verified'),
            'linked_social': lambda x: [{
                'type': a['provider']['name'],
                'uid': a['userid'],
                'username': a['username'],
                'profile_id': a['profile_id']
            } for a in x.get('social')],
            'links': lambda x: list(itertools.chain(*[l.get('addresses') for l in x.get('social', [])])),
        },
    },
    'Yandex Music API': {
        'flags': ['invocationInfo', 'req-id"'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('result', {}),
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('login'),
            'yandex_uid': lambda x: x.get('uid'),
            'yandex_public_id': lambda x: x.get('publicId'),
            'fullname': lambda x: x.get('fullName'),
            'links': lambda x: x.get('socialProfiles'),
            'is_verified': lambda x: x.get('verified'),
            'has_tracks': lambda x: x.get('statistics', {}).get('hasTracks'),
            'liked_users': lambda x: x.get('statistics', {}).get('likedUsers'),
            'liked_by_users': lambda x: x.get('statistics', {}).get('likedByUsers'),
            'liked_artists': lambda x: x.get('statistics', {}).get('likedArtists'),
            'liked_albums': lambda x: x.get('statistics', {}).get('likedAlbums'),
            'ugc_tracks_count': lambda x: x.get('statistics', {}).get('ugcTracks'),
            'is_private_statistics': lambda x: x.get('statistics') == 'private',
            'is_private_social_profiles': lambda x: x.get('socialProfiles') == 'private',
        },
    },
    'Yandex Realty offer': {
        'flags': ['realty.yandex.ru/offer'],
        'regex': r'({"routing":{"currentRoute".+?});',
        'extract_json': True,
        'fields': {
            'your_yuid': lambda x: x['user']['yuid'],
            'your_uid': lambda x: x['user']['uid'],
            'your_wallet_balance': lambda x: x['user']['walletInfo'].get('balance'),
            'your_emails': lambda x: ', '.join(x['user']['emails']),
            'your_name': lambda x: x['user'].get('displayName'),
            'your_username': lambda x: x['user'].get('defaultEmail'),
            'your_phone': lambda x: x['user'].get('defaultPhone'),
            'yandex_uid': lambda x: x['offerCard']['card']['author']['id'],
            'name': lambda x: decode_ya_str(x['offerCard']['card']['author']['profile']['name'])
        }
    },
    'Yandex Collections': {
        'flags': ['<meta name="collections"', '/collections'],
        'regex': r'(?:id="restoreData">)(.+?)<\/script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['entities']['users'].get(x['profileUser'].get('id'), {}),
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x.get('id'),
            'yandex_public_id': lambda x: x.get('public_id'),
            'fullname': lambda x: x.get('display_name'),
            'image': lambda x: get_yandex_profile_pic(x.get('default_avatar_id')),
            'gender': lambda x: x.get('sex'),
            'description': lambda x: x.get('description'),
            'phone_id': lambda x: x.get('phone_id'),
            'company_info': lambda x: x.get('company_info'),
            'likes': lambda x: x['stats'].get('likes'),
            'cards': lambda x: x['stats'].get('cards'),
            'boards': lambda x: x['stats'].get('boards'),
            # TODO: other stats
            'is_passport': lambda x: x.get('is_passport'),
            'is_restricted': lambda x: x.get('is_restricted'),
            'is_forbid': lambda x: x.get('is_forbid'),
            'is_verified': lambda x: x.get('is_verified'),
            'is_km': lambda x: x.get('is_km'),
            'is_business': lambda x: x.get('is_business'),

        }
    },
    'Yandex Collections API': {
        'flags': ['default_avatar_id', 'collections', 'is_passport'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'fields': {
            'id': lambda x: x.get('id'),
            'yandex_public_id': lambda x: x.get('public_id'),
            'fullname': lambda x: x.get('display_name'),
            'image': lambda x: get_yandex_profile_pic(x.get('default_avatar_id')),
            'gender': lambda x: x.get('sex'),
            'description': lambda x: x.get('description'),
            'phone_id': lambda x: x.get('phone_id'),
            'company_info': lambda x: x.get('company_info'),
            'likes': lambda x: x['stats'].get('likes'),
            'cards': lambda x: x['stats'].get('cards'),
            'boards': lambda x: x['stats'].get('boards'),
            # TODO: other stats
            'is_passport': lambda x: x.get('is_passport'),
            'is_restricted': lambda x: x.get('is_restricted'),
            'is_forbid': lambda x: x.get('is_forbid'),
            'is_verified': lambda x: x.get('is_verified'),
            'is_km': lambda x: x.get('is_km'),
            'is_business': lambda x: x.get('is_business'),
        }
    },
    'Yandex Reviews user profile': {
        'flags': ['isInternalYandexNet', 'ReviewFormContent'],
        'regex': r'window.__PRELOADED_DATA = ({[\s\S]+?})\n\s+}catch',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['pageData']['initialState'],
            json.dumps,
        ],
        'fields': {
            'yandex_public_id': lambda x: x.get('pkUser', {}).get('publicId'),
            'fullname': lambda x: decode_ya_str(x.get('pkUser', {}).get('name')),
            'image': lambda x: get_yandex_profile_pic(x.get('pkUser', {}).get('pic')),
            'is_verified': lambda x: x.get('pkUser', {}).get('verified'),
            'reviews_count': lambda x: len(x.get('reviews', {}).get('all', {}).keys()),
            'following_count': lambda x: x.get('subscription', {}).get('subscribersCount'),
            'follower_count': lambda x: x.get('subscription', {}).get('subscriptionsCount'),
        },
    },
    'Yandex Zen user profile': {
        'flags': ['https://zen.yandex.ru/user/', 'zen-lib'],
        'regex': r'\n\s+var data = ({"__[\s\S]+?});\n',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: list(filter(lambda y: '__serverState' in y[0], x.items())),
            lambda x: x[0][1]['channel']['source'],
            json.dumps,
        ],
        'fields': {
            'yandex_public_id': lambda x: x.get('publicId'),
            'fullname': lambda x: x.get('title'),
            'image': lambda x: x.get('logo'),
            'bio': lambda x: x.get('description'),
            'yandex_messenger_guid': lambda x: x.get('messengerGuid'),
            'links': lambda x: x.get('socialLinks'),
            'type': lambda x: x.get('type'),
            'comments_count': lambda x: x.get('userCommentsCount'),
            'status': lambda x: x.get('socialProfileStatus'),
            'following_count': lambda x: x.get('subscribers'),
            'follower_count': lambda x: x.get('subscriptions'),
        },
    },
    'Yandex messenger search API': {
        'flags': ['messages', 'matches', 'users_and_chats'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['data']['users_and_chats']['items'],
            lambda x: x if len(x) == 1 else list(filter(lambda y: y['matches'].get('nickname'), x)),
            lambda x: x[0] if x else {},
            json.dumps,
        ],
        'fields': {
            'fullname': lambda x: x['data']['display_name'],
            'username': lambda x: x['matches'].get('nickname', [None])[0],
            'yandex_messenger_guid': lambda x: x['data']['guid'],
            'registration_status': lambda x: x['data']['registration_status'],
            'image': lambda x: get_yandex_profile_pic(x['data'].get('avatar_id')),
            'yandex_phone_id': lambda x: x['data'].get('phone_id'),
            'yandex_uid': lambda x: x['data'].get('uid'),
        },
    },
    'Yandex messenger profile API': {
        'flags': ['guid', 'registration_status', 'contacts'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['data']['users'][0],
            json.dumps,
        ],
        'fields': {
            'fullname': lambda x: x['display_name'],
            'yandex_messenger_guid': lambda x: x['guid'],
            'registration_status': lambda x: x['registration_status'],
            'image': lambda x: get_yandex_profile_pic(x.get('avatar_id')),
            'yandex_phone_id': lambda x: x.get('phone_id'),
        },
    },
    'Yandex Bugbounty user profile': {
        'flags': ['yandex_bug_bounty_terms_conditions', 'user__pic'],
        'regex': r'upics\.yandex\.net\/(?P<yandex_uid>\d+)[\s\S]+<span>(?P<firstname>.+?)<\/span>\s+<em>(?P<username>.+?)<\/em>([\s\S]+?class="link">(?P<email>.+?)<\/a>)?([\s\S]+?<a href="(?P<url>.+?)" target="_blank" class="link link_social">)?',
    },
    'Yandex O': {
        'flags': ['<PLACEHOLDER>'],  # NOT PRESENT
        'regex': r'<script type="application/json" id="initial-state" nonce=".+?">(.+?)<\/script>',
        'extract_json': True,
        'fields': {
            'yandex_public_id': lambda x: x['publicProfile']['params']['publicUserId'],
            'fullname': lambda x: decode_ya_str(x['publicProfile']['data']['publicProfile']['seller']['name']),
            'image': lambda x: x['publicProfile']['data']['publicProfile']['seller']['avatar']['size_100x100'],
            'score': lambda x: x['publicProfile']['data']['publicProfile']['seller']['userBadge']['score'],
        }
    },
    'VK user profile foaf page': {
        'url_hints': ('vk.com',),
        'flags': ['<foaf:Person>', '<ya:publicAccess>'],
        'bs': True,
        'fields': {
            'is_private': lambda x: x.find('ya:publicaccess').contents[0] == 'allowed',
            'state': lambda x: x.find('ya:profilestate').contents[0],
            'first_name': lambda x: x.find('ya:firstname').contents[0],
            'last_name': lambda x: x.find('ya:secondname').contents[0],
            'fullname': lambda x: x.find('foaf:name').contents[0],
            'gender': lambda x: x.find('foaf:gender').contents[0],
            'created_at': lambda x: parse_datetime_str(x.find('ya:created').get('dc:date')),
            'updated_at': lambda x: parse_datetime_str(x.find('ya:modified').get('dc:date')),
            # 'following_count': lambda x: x.find('ya:subscribedToCount'),
            # 'follower_count': lambda x: x.find('ya:friendsCount'),
            # 'friends_count': lambda x: x.find('ya:subscribersCount'),
            # 'image': lambda x: x.find('foaf:Image'),
            'website': lambda x: x.find('foaf:homepage').contents[0],
            # 'links': lambda x: x.find('foaf:externalProfile'),
        },
    },
    'VK user profile': {
        'url_hints': ('vk.com',),
        'flags': ['<span class="ui_tab_content_new">', '"ownerId":'],
        'url_mutations': [
            {
                'from': r'https?://.*?vk.com/id(?P<vk_id>\d+)',
                'to': 'https://vk.com/foaf.php?id={vk_id}',
            }
        ],
        'regex': r'"ownerId":(?P<vk_id>\d+),"wall".*?"loc":"(?P<vk_username>.*?)","back":"(?P<fullname>.*?)"'
    },
    'VK closed user profile': {
        'url_hints': ('vk.com',),
        'flags': ['error_msg":"This profile is private', 'first_name_nom', 'last_name_gen'],
        'regex': r'<title>(?P<fullname>.*?)<\/title>'
    },
    'VK blocked user profile': {
        'url_hints': ('vk.com',),
        'flags': ['window.vk = {', 'User was deleted or banned'],
        'regex': r'<title>(?P<fullname>.*?)<\/title>'
    },
    'Gravatar': {
        'url_hints': ('gravatar.com', 'en.gravatar.com'),
        'flags': ['gravatar.com\\/avatar', 'thumbnailUrl'],
        'url_mutations': [
            {
                'from': r'https?://.*?gravatar.com/(?P<username>[^/]+)',
                'to': 'https://en.gravatar.com/{username}.json',
            }
        ],
        'regex': r'^(.+?)$',
        'extract_json': True,
        'fields': {
            'gravatar_id': lambda x: x['entry'][0]['id'],
            'image': lambda x: x['entry'][0]['thumbnailUrl'],
            'username': lambda x: x['entry'][0]['preferredUsername'],
            'fullname': lambda x: x['entry'][0].get('name', {}).get('formatted'),
            'name': lambda x: x['entry'][0]['displayName'],
            'location': lambda x: x['entry'][0].get('currentLocation'),
            'emails': lambda x: [y['value'] for y in x['entry'][0].get('emails', [])],
            'links': lambda x: [y['url'] for y in x['entry'][0].get('accounts', [])] + [y['value'] for y in
                                                                                        x['entry'][0].get('urls', [])],
            'bio': lambda x: x['entry'][0].get('aboutMe'),
        }
    },
    'Instagram': {
        'url_hints': ('instagram.com', 'cdninstagram.com'),
        'flags': ['instagram://user?username'],
        'regex': r'<script type="application/json" .*?>(.*?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['entry_data']['ProfilePage'][0]['graphql']['user'],
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('full_name'),
            'id': lambda x: x.get('id'),
            'image': lambda x: x.get('profile_pic_url_hd'),
            'bio': lambda x: x.get('biography'),
            'business_email': lambda x: x.get('business_email'),
            'external_url': lambda x: x.get('external_url'),
            'facebook_uid': lambda x: x.get('fbid'),
            'is_business': lambda x: x.get('is_business_account'),
            'is_joined_recently': lambda x: x.get('is_joined_recently'),
            'is_private': lambda x: x.get('is_private'),
            'is_verified': lambda x: x.get('is_verified'),
            'follower_count': lambda x: x.get('edge_followed_by', {}).get('count'),
            'following_count': lambda x: x.get('edge_follow', {}).get('count'),
        }
    },
    'Instagram API': {
        'url_hints': ('instagram.com', 'cdninstagram.com'),
        'flags': ['{"user":{"pk"', 'profile_pic_url'],
        'regex': r'^(.+?)$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x['user'].get('username'),
            'id': lambda x: x['user'].get('pk'),
            'image': lambda x: x['user'].get('profile_pic_url'),
        }
    },
    'Instagram page JSON': {
        'url_hints': ('instagram.com', 'cdninstagram.com'),
        'flags': ['"logging_page_id":"profilePage', 'profile_pic_url'],
        'regex': r'^(.+?)$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['graphql']['user'],
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('full_name'),
            'id': lambda x: x.get('id'),
            'image': lambda x: x.get('profile_pic_url_hd'),
            'bio': lambda x: x.get('biography'),
            'business_email': lambda x: x.get('business_email'),
            'external_url': lambda x: x.get('external_url'),
            'facebook_uid': lambda x: x.get('fbid'),
            'is_business': lambda x: x.get('is_business_account'),
            'is_joined_recently': lambda x: x.get('is_joined_recently'),
            'is_private': lambda x: x.get('is_private'),
            'is_verified': lambda x: x.get('is_verified'),
            'follower_count': lambda x: x.get('edge_followed_by', {}).get('count'),
            'following_count': lambda x: x.get('edge_follow', {}).get('count'),
        }
    },
    'Instagram GraphQL': {
        'url_hints': ('instagram.com', 'cdninstagram.com'),
        'flags': ['"biography"', '"edge_followed_by"', '"profile_pic_url_hd"'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: (x.get('data') or {}).get('user') or {},
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('full_name'),
            'id': lambda x: x.get('id'),
            'image': lambda x: x.get('profile_pic_url_hd'),
            'bio': lambda x: x.get('biography'),
            'business_email': lambda x: x.get('business_email'),
            'external_url': lambda x: x.get('external_url'),
            'facebook_uid': lambda x: x.get('fbid'),
            'is_business': lambda x: x.get('is_business_account'),
            'is_joined_recently': lambda x: x.get('is_joined_recently'),
            'is_private': lambda x: x.get('is_private'),
            'is_verified': lambda x: x.get('is_verified'),
            'follower_count': lambda x: (x.get('edge_followed_by') or {}).get('count'),
            'following_count': lambda x: (x.get('edge_follow') or {}).get('count'),
            'post_count': lambda x: (x.get('edge_owner_to_timeline_media') or {}).get('count'),
            'links': lambda x: [
                link['url'] for link in (x.get('bio_links') or []) if link.get('url')
            ] or None,
            'usernames': lambda x: [
                entity['user']['username']
                for entity in ((x.get('biography_with_entities') or {}).get('entities') or [])
                if (entity.get('user') or {}).get('username')
            ] or None,
        }
    },
    'Spotify API': {
        'url_hints': ('spotify.com', 'open.spotify.com'),
        'flags': ['"uri": "spotify:user:'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('name'),
            'follower_count': lambda x: x.get('followers_count'),
            'following_count': lambda x: x.get('following_count'),
            'image': lambda x: x.get('image_url', ''),
        }
    },
    'EyeEm': {
        'url_hints': ('eyeem.com',),
        'flags': ['window.__APOLLO_STATE__', 'cdn.eyeem.com/thumb'],
        'regex': r'__APOLLO_STATE__ = ({.+?});\n',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: list(filter(lambda x: 'User:' in x[0], x.items()))[0][1],
            json.dumps,
        ],
        'fields': {
            'eyeem_id': lambda x: x['id'],
            'eyeem_username': lambda x: x['nickname'],
            'fullname': lambda x: x['fullname'],
            'bio': lambda x: x['description'],
            'follower_count': lambda x: x['totalFollowers'],
            'friends_count': lambda x: x['totalFriends'],
            'liked_photos': lambda x: x['totalLikedPhotos'],
            'photos': lambda x: x['totalPhotos'],
            'facebook_uid': lambda x: extract_facebook_uid(x['thumbUrl'])
        }
    },
    'Medium RSS': {
        'url_hints': ('medium.com',),
        'flags': ['<rss', 'medium.com', 'Stories by'],
        'regex': r'<title><!\[CDATA\[Stories by (?P<fullname>[^\]]+?) on Medium\]\]></title>[\s\S]*?<link>https://medium\.com/@(?P<username>[^?/<\s]+)[\s\S]*?<image>\s*<url>(?P<image>[^<]+)</url>[\s\S]*?<lastBuildDate>(?P<latest_activity_at>[^<]+)</lastBuildDate>',
        'fields': {},
    },
    'Medium': {
        'url_hints': ('medium.com',),
        'flags': ['https://medium.com', 'com.medium.reader'],
        'regex': r'__APOLLO_STATE__ = ({.+})',
        'extract_json': True,
        'transforms': [
            lambda x: json.JSONDecoder().raw_decode(x)[0],
            lambda x: [v for k, v in x.items() if k.startswith('User:')][0],
            json.dumps,
        ],
        'fields': {
            'medium_id': lambda x: x.get('id'),
            'medium_username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name'),
            'bio': lambda x: x.get('bio'),
            'twitter_username': lambda x: x.get('twitterScreenName'),
            'is_suspended': lambda x: x.get('isSuspended'),
            'facebook_uid': lambda x: x.get('facebookAccountId'),
            'is_blocking': lambda x: x.get('isBlocking'),
            'is_muting': lambda x: x.get('isMuting'),
            'post_counts': lambda x: x.get('userPostCounts'),
            'follower_count': lambda x: x.get('socialStats', {}).get('followerCount'),
            'following_count': lambda x: x.get('socialStats', {}).get('followingCount'),
        }
    },
    'Odnoklassniki': {
        'url_hints': ('ok.ru',),
        'flags': ['OK.startupData'],
        'regex': r'path:"/(profile/)?(?P<ok_user_name_id>.+?)",state:".+?friendId=(?P<ok_id>\d+?)"',
    },
    'Habrahabr HTML (old)': {
        'url_hints': ('habr.com', 'habracdn'),
        'flags': ['habracdn.net'],
        'bs': True,
        'fields': {
            'uid': lambda x: x.find('div', {'class': 'user-info__stats'}).parent.attrs['class'][-1].split('_')[-1],
            'username': lambda x: x.find('a', {'class': 'media-obj__image'}).get('href').split('/')[-2],
            'image': lambda x: 'http:' + x.find('div', {'class': 'user-info__stats'}).find('img').get('src'),
        },
    },
    'Habrahabr JSON': {
        'url_hints': ('habr.com', 'habrastorage'),
        'flags': ['habrastorage.org', '"authorRefs":'],
        'regex': r'"authorRefs":(\{"__ALIAS_STORE__":true,"[^"]+":\{[\s\S]+?"reach":"[^"]*"\}\})(?=,"author)',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: next((v for k, v in x.items() if k != '__ALIAS_STORE__'), {}),
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('alias'),
            'about': lambda x: x.get('speciality') or None,
            'birthday': lambda x: x.get('birthday') or None,
            'gender': lambda x: x.get('gender'),
            'rating': lambda x: x.get('rating'),
            'karma': lambda x: (x.get('scoreStats') or {}).get('score'),
            'fullname': lambda x: x.get('fullname') or None,
            'is_readonly': lambda x: x.get('isReadonly'),
            'location': lambda x: x.get('location') or None,
            'image': lambda x: x.get('avatarUrl') or None,
            'follower_count': lambda x: (x.get('followStats') or {}).get('followersCount'),
            'following_count': lambda x: (x.get('followStats') or {}).get('followStats'),
        }
    },
    'My Mail.ru': {
        'url_hints': ('my.mail.ru', 'mail.ru'),
        'flags': ['my.mail.ru', 'models/user/journal">'],
        'regex': r'journal">\s+({\s+"name":[\s\S]+?})',
        'extract_json': True,
        'fields': {
            'mail_uid': lambda x: get_mymail_uid(x.get('dir').split('/')[-2] if x else ''),
            'mail_id': lambda x: x.get('id'),
            'username': lambda x: x.get('dir').split('/')[-2] if x else '',
            'au_id': lambda x: x.get('auId'),
            'email': lambda x: x.get('email'),
            'name': lambda x: x.get('name'),
            'is_vip': lambda x: x.get('isVip'),
            'is_community': lambda x: x.get('isCommunity'),
            'is_video_channel': lambda x: x.get('isVideoChannel'),
            'image': lambda x: 'https://filin.mail.ru/pic?email=' + x.get('email'),
        }
    },
    'Behance': {
        'url_hints': ('behance.net',),
        'flags': ['behance.net', 'beconfig-store_state'],
        'regex': r'<script type="application/json" id="beconfig-store_state">({.+?})</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('profile', {}).get('user') or x.get('profile', {}).get('owner') or {},
            json.dumps,
        ],
        'url_mutations': [
            {
                'from': r'https?://(www.)?behance.net/(?P<username>[^/]+).*',
                'to': 'https://www.behance.net/{username}/appreciated',
                'headers': {'Cookie': 'ilo0=true'},
            }
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('displayName') or x.get('display_name'),
            'website': lambda x: x.get('website') or None,
            'image': lambda x: next((i['url'] for i in (x.get('images', {}) or {}).get('allAvailable', []) if i.get('width') == 276), None) or (x.get('images', {}) or {}).get('276'),
            'image_bg': lambda x: x.get('bannerImageUrl') or x.get('banner_image_url') or None,
            'company': lambda x: x.get('company') or None,
            'city': lambda x: x.get('city') or None,
            'country': lambda x: x.get('country') or None,
            'location': lambda x: x.get('location') or None,
            'created_at': lambda x: parse_datetime(x.get('createdOn') or x.get('created_on')),
            'occupation': lambda x: x.get('occupation') or None,
            'follower_count': lambda x: (x.get('stats') or {}).get('followers'),
            'following_count': lambda x: (x.get('stats') or {}).get('following'),
            'views_count': lambda x: (x.get('stats') or {}).get('views'),
            'appreciations': lambda x: (x.get('stats') or {}).get('appreciations'),
        }
    },
    'Blogger': {
        'url_hints': ('blogspot.com', 'blogger.com'),
        'flags': ['www.blogger.com/static', 'blogspot.com/feeds/posts'],
        'regex': r'www.blogger.com\/feeds\/(?P<blog_id>\d+)\/posts\/default" \/>\n<link rel="me" href="https:\/\/www.blogger.com\/profile/(?P<uid>\d+)" \/>',
    },
    'D3.ru': {
        'url_hints': ('d3.ru',),
        'flags': ['feedSettingsHandler.subscribe(this', 'd3.ru/static'],
        'regex': r"feedSettingsHandler.subscribe\(this, 'users', '(?P<uid>\d+)'",
    },
    'Gitlab': {
        'url_hints': ('gitlab.com',),
        'flags': ['gitlab-static.net'],
        'regex': r'abuse_reports.+?user_id=(?P<uid>\d+)"',
    },
    '500px userByUsername API': {
        'url_hints': ('500px.com', 'api.500px.com'),
        'flags': ['{"data":{"userByUsername":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('data', {}).get('userByUsername', {}) or {},
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('legacyId') or x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('displayName') or ' '.join(filter(None, [x.get('firstName'), x.get('lastName')])) or None,
            'bio': lambda x: (x.get('userProfile') or {}).get('about') or None,
            'country': lambda x: (x.get('userProfile') or {}).get('country') or None,
            'city': lambda x: (x.get('userProfile') or {}).get('city') or None,
            'created_at': lambda x: x.get('registeredAt'),
            'website': lambda x: (x.get('socialMedia') or {}).get('website') or None,
            'twitter_username': lambda x: (x.get('socialMedia') or {}).get('twitter') or None,
            'facebook_username': lambda x: (x.get('socialMedia') or {}).get('facebook') or None,
            'instagram_username': lambda x: (x.get('socialMedia') or {}).get('instagram') or None,
        },
    },
    '500px GraphQL API': {
        'url_hints': ('500px.com', 'api.500px.com'),
        'flags': ['{"data":{"profile":{"id"'],
        'url_mutations': [
            {
                'from': r'https://500px.com/p/(?P<username>.+)/?',
                'to': 'https://api.500px.com/graphql?query=query%20ProfileRendererQuery%28%24username%3AString%21%29%7Bprofile%3AuserByUsername%28username%3A%24username%29%7Bid%20legacyId%20userType%3Atype%20username%20displayName%20registeredAt%20avatar%7Bimages%7Burl%7D%7D%20coverPhotoUrl%20userProfile%7Bcountry%20city%20about%7D%20socialMedia%7Bwebsite%20twitter%20instagram%20facebook%7D%20photoStats%7BlikeCount%20viewCount%7D%20followedBy%7BtotalCount%7D%20followingUsers%7BtotalCount%7D%7D%7D&variables=%7B%22username%22%3A%22{username}%22%7D',
            }
        ],
        'regex': r'^{"data":({.+})}$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['profile']['id'],
            'legacy_id': lambda x: x['profile']['legacyId'],
            'username': lambda x: x['profile']['username'],
            'fullname': lambda x: x['profile']['displayName'],
            'account_type': lambda x: x['profile'].get('userType'),
            'created_at': lambda x: x['profile']['registeredAt'],
            'image': lambda x: x['profile']['avatar']['images'][-1]['url'],
            'image_bg': lambda x: x['profile']['coverPhotoUrl'],
            'bio': lambda x: (x['profile'].get('userProfile') or {}).get('about'),
            'country': lambda x: (x['profile'].get('userProfile') or {}).get('country'),
            'city': lambda x: (x['profile'].get('userProfile') or {}).get('city'),
            'website': lambda x: (x['profile'].get('socialMedia') or {}).get('website'),
            'twitter_username': lambda x: (x['profile'].get('socialMedia') or {}).get('twitter'),
            'instagram_username': lambda x: (x['profile'].get('socialMedia') or {}).get('instagram'),
            'facebook_username': lambda x: (x['profile'].get('socialMedia') or {}).get('facebook'),
            'follower_count': lambda x: (x['profile'].get('followedBy') or {}).get('totalCount'),
            'following_count': lambda x: (x['profile'].get('followingUsers') or {}).get('totalCount'),
            'likes_count': lambda x: (x['profile'].get('photoStats') or {}).get('likeCount'),
            'views_count': lambda x: (x['profile'].get('photoStats') or {}).get('viewCount'),
        }
    },
    'Google Document API': {
        'url_hints': ('docs.google.com', 'drive.google.com', 'googleapis.com'),
        'flags': ['alternateLink', 'copyRequiresWriterPermission'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'url_mutations': [
            {
                # credits: https://github.com/Malfrats/xeuledoc
                'from': r'https://(docs|drive).google.com/(spreadsheets|document|presentation|drawings|file)/d/(?P<gdoc_id>[\w-]+)',
                'to': 'https://clients6.google.com/drive/v2beta/files/{gdoc_id}?fields=alternateLink%2CcopyRequiresWriterPermission%2CcreatedDate%2Cdescription%2CdriveId%2CfileSize%2CiconLink%2Cid%2Clabels(starred%2C%20trashed)%2ClastViewedByMeDate%2CmodifiedDate%2Cshared%2CteamDriveId%2CuserPermission(id%2Cname%2CemailAddress%2Cdomain%2Crole%2CadditionalRoles%2CphotoLink%2Ctype%2CwithLink)%2Cpermissions(id%2Cname%2CemailAddress%2Cdomain%2Crole%2CadditionalRoles%2CphotoLink%2Ctype%2CwithLink)%2Cparents(id)%2Ccapabilities(canMoveItemWithinDrive%2CcanMoveItemOutOfDrive%2CcanMoveItemOutOfTeamDrive%2CcanAddChildren%2CcanEdit%2CcanDownload%2CcanComment%2CcanMoveChildrenWithinDrive%2CcanRename%2CcanRemoveChildren%2CcanMoveItemIntoTeamDrive)%2Ckind&supportsTeamDrives=true&enforceSingleParent=true&key=AIzaSyC1eQ1xj69IdTMeii5r7brs3R90eck-m7k',
                'headers': {"X-Origin": "https://drive.google.com"},
            }
        ],
        'fields': {
            'created_at': lambda x: x.get('createdDate'),
            'updated_at': lambda x: x.get('modifiedDate'),
            'fake_gaia_id': lambda x: x.get('permissions')[1]['id'],
            'fullname': lambda x: x.get('permissions')[1]['name'],
            'email': lambda x: x.get('permissions')[1]['emailAddress'],
            'image': lambda x: x.get('permissions')[1]['photoLink'],
        }
    },
    'Google Document': {
        'url_hints': ('docs.google.com', 'drive.google.com'),
        'flags': ['_docs_flag_initialData'],
        'regex': r'({"docs-ails":"docs_\w+".+?});',
        'extract_json': True,
        'message': 'Auth cookies requires, add through --cookies in format "a=1;b=2"n\nTry to run twice to get result.',
        'fields': {
            'your_ls_uid': lambda x: x.get('docs-offline-lsuid'),
            'your_cpf': lambda x: x.get('docs-cpf'),
            'your_username': lambda x: x.get('docs-offline-ue') or x.get('docs-hue'),
            'viewer_uid': lambda x: x['docs-pid'],
            'org_name': lambda x: x['docs-doddn'],
            'org_domain': lambda x: x['docs-dodn'],
            'mime_type': lambda x: x.get('docs-dm'),
        }
    },
    'Google Maps contributions': {
        'url_hints': ('google.com/maps', 'maps.google.com'),
        'flags': ['/maps/preview/opensearch.xml', '<meta content="Contributions by'],
        'regex': r'"Contributions by (?P<name>.+?)",("(?P<contributions_count>\d+) Contribution|"(?P<contribution_level>.+?)")',
    },
    # Parses the /about page ytInitialData: channel metadata, social crosslinks decoded from
    # youtube.com/redirect URLs, and aboutChannelViewModel fields
    # (location/created_at/follower_count/views_count/videos_count). Social links and the
    # about panel only appear on /about — hence the url_mutation.
    'YouTube ytInitialData': {
        'url_hints': ('youtube.com', 'youtu.be'),
        'flags': ['ytInitialData', 'channelMetadataRenderer'],
        'regex': r'var ytInitialData = ({.+?});</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: {
                **x.get('metadata', {}).get('channelMetadataRenderer', {}),
                '_all_redirect_urls': _yt_redirect_urls(x),
                '_about': _yt_find_about(x),
            },
            json.dumps,
        ],
        'fields': {
            'youtube_channel_id': lambda x: x.get('externalId'),
            'fullname': lambda x: x.get('title'),
            'bio': lambda x: x.get('description'),
            'image': lambda x: (x.get('avatar', {}).get('thumbnails', [{}]) or [{}])[0].get('url'),
            'channel_url': lambda x: x.get('vanityChannelUrl') or x.get('channelUrl'),
            'keywords': lambda x: x.get('keywords'),
            'is_family_safe': lambda x: x.get('isFamilySafe'),
            'location': lambda x: (x.get('_about') or {}).get('country') or None,
            'created_at': lambda x: ((x.get('_about') or {}).get('joinedDateText') or {}).get('content', '').replace('Joined ', '') or None,
            'follower_count': lambda x: (x.get('_about') or {}).get('subscriberCountText') or None,
            'views_count': lambda x: (x.get('_about') or {}).get('viewCountText') or None,
            'videos_count': lambda x: (x.get('_about') or {}).get('videoCountText') or None,
            'facebook_id': lambda x: x.get('facebookProfileId') if x.get('facebookProfileId', '').isdigit() else None,
            'links': lambda x: json.dumps(x.get('_all_redirect_urls')) if x.get('_all_redirect_urls') else None,
            'instagram_username': lambda x: _yt_social_username(x, 'instagram.com'),
            'twitter_username': lambda x: _yt_social_username(x, 'twitter.com') or _yt_social_username(x, 'x.com'),
            'facebook_username': lambda x: _yt_social_username(x, 'facebook.com') or (x.get('facebookProfileId') if not x.get('facebookProfileId', '').isdigit() else None) or None,
            'tiktok_username': lambda x: _yt_social_username(x, 'tiktok.com'),
            'twitch_username': lambda x: _yt_social_username(x, 'twitch.tv'),
            'soundcloud_username': lambda x: _yt_social_username(x, 'soundcloud.com'),
            'pinterest_username': lambda x: _yt_social_username(x, 'pinterest.com') or _yt_social_username(x, 'pinterest.'),
            'discord_invite': lambda x: _yt_social_username(x, 'discord.gg') or _yt_social_username(x, 'discord.com/invite'),
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?youtube\.com/@(?P<username>[^/?#]+)$',
            'to': 'https://www.youtube.com/@{username}/about',
        }],
    },
    'Youtube Channel': {
        'url_hints': ('youtube.com', 'youtu.be'),
        'flags': ['<span itemprop="author" itemscope itemtype="http://schema.org/Person">'],
        'regex': r'itemtype="http:\/\/schema\.org\/Person"[\s\S]+?https:\/\/plus\.google\.com\/(?P<gaia_id>\d+)">[\s\S]+?itemprop="name" content="(?P<name>.+?)"'
    },
    'Bitbucket': {
        'url_hints': ('bitbucket.org', 'api.bitbucket.org'),
        'flags': ['https://api.bitbucket.org'],
        'regex': r'({.+?"section": {"profile.+?"repositories":.+?}});',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['global']['targetUser'],
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x['uuid'].strip('{}'),
            'id': lambda x: x['account_id'],
            'fullname': lambda x: x['display_name'],
            'nickname': lambda x: x['nickname'],
            'location': lambda x: x['location'],
            'image': lambda x: x['links']['avatar']['href'],
            'occupation': lambda x: x['job_title'],
            'created_at': lambda x: x['created_on'],
            'is_service': lambda x: x['is_staff'],
            'is_active': lambda x: x['is_active'],
            'has_2fa_enabled': lambda x: x['has_2fa_enabled'],
        }
    },
    'Pinterest profile/board page': {
        'url_hints': ('pinterest.com', 'pinimg.com'),
        'flags': ['pinterest.com', 'unauth_profile', '"node_id":"VXNlcjo'],
        'regex': r'\\"unauth_profile\\"[\s\S]+?"data":(\{"node_id":"VXNlcjo[\s\S]+?\}),"fetching":false',
        'extract_json': True,
        'transforms': [
            json.loads,
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('full_name') or None,
            'bio': lambda x: x.get('about') or None,
            'image': lambda x: x.get('image_xlarge_url') or x.get('image_medium_url') or None,
            'image_bg': lambda x: ((x.get('profile_cover') or {}).get('image_url')) or None,
            'website': lambda x: x.get('website_url') or x.get('domain_url') or None,
            'follower_count': lambda x: x.get('follower_count'),
            'following_count': lambda x: x.get('following_count'),
            'posts_count': lambda x: x.get('pin_count'),
            'board_count': lambda x: x.get('board_count'),
            'is_private': lambda x: x.get('is_private_profile'),
            'is_indexed': lambda x: x.get('indexed'),
            'is_partner': lambda x: x.get('is_partner'),
            'is_verified_merchant': lambda x: x.get('is_verified_merchant'),
            'is_website_verified': lambda x: x.get('domain_verified'),
            'created_at': lambda x: x.get('created_at'),
            'latest_activity_at': lambda x: x.get('last_pin_save_time') or None,
        }
    },
    'Reddit': {
        'url_hints': ('reddit.com', 'redditstatic.com'),
        'flags': ['https://www.redditstatic.com/'],
        'regex': r'___r = ({.+?});<\/script><script>',
        'extract_json': True,
        'transforms': [
            lambda x: json.dumps(list(json.loads(x)['users']['models'].values())[0]),
        ],
        'fields': {
            'reddit_id': lambda x: x['profileId'],
            'reddit_username': lambda x: x['username'],
            'fullname': lambda x: x['displayName'],
            'image': lambda x: x['accountIcon'],
            'is_employee': lambda x: x['isEmployee'],
            'is_nsfw': lambda x: x['isNSFW'],
            'is_mod': lambda x: x['isMod'],
            'is_following': lambda x: x['isFollowing'],
            'has_user_profile': lambda x: x['hasUserProfile'],
            'hide_from_robots': lambda x: x['hideFromRobots'],
            'created_at': lambda x: parse_datetime(x['createdUtc']),
            'total_karma': lambda x: x['karma']['total'],
            'post_karma': lambda x: x['karma']['fromPosts'],
            'comments_karma': lambda x: x['karma']['fromComments'],
            'awards_given_karma': lambda x: x['karma']['fromAwardsGiven'],
            'awards_got_karma': lambda x: x['karma']['fromAwardsReceived'],
        },
    },
    'Steam': {
        'url_hints': ('steamcommunity.com', 'steampowered.com'),
        'flags': ['store.steampowered.com', 'profile_header_bg_texture'],
        'regex': r'({"url":".+?});',
        'extract_json': True,
        'fields': {
            'steam_id': lambda x: x['steamid'],
            'nickname': lambda x: x['personaname'],
            'username': lambda x: [y for y in x['url'].split('/') if y][-1],
        }
    },
    'Steam Community Group': {
        'url_hints': ('steamcommunity.com',),
        'flags': ['steamcommunity.com', 'Steam Community :: Group ::'],
        'bs': True,
        'fields': {
            'username': lambda x: (lambda m: m.group(1) if m else None)(re.search(r'steamcommunity\.com/groups/([^/?#"\' ]+)', str(x))),
            'fullname': lambda x: _meta_re(x, 'og:title', r'Steam Community :: Group :: (.+)$'),
            'bio': lambda x: _meta(x, 'og:description'),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'Steam Addiction': {
        # TODO: добавить отображение предыдущих ников по ссылке /ajaxaliases/, например https://steamcommunity.com/profiles/76561198222448544/ajaxaliases/
        'url_hints': ('steamcommunity.com',),
        'flags': ['steamcommunity.com'],
        'regex': r'<bdi><span class="filtered_text">(?P<real_name>.+)<\/span><\/bdi>(\s*&nbsp;\s*<img class="profile_flag" src=".*">\s*(?P<country>.*)<\/div>)*',
    },
    'Stack Exchange API': {
        'url_hints': ('api.stackexchange.com', 'stackoverflow.com', 'stackexchange.com'),
        'flags': ['"items":', '"user_id":', '"account_id":', '"reputation":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: (x.get('items') or [{}])[0],
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('user_id'),
            'account_id': lambda x: x.get('account_id'),
            'username': lambda x: x.get('display_name'),
            'image': lambda x: x.get('profile_image'),
            'reputation': lambda x: x.get('reputation'),
            'link': lambda x: x.get('link'),
            'created_at': lambda x: x.get('creation_date'),
        },
    },
    'Stack Overflow & similar': {
        'url_hints': ('stackoverflow.com', 'stackexchange.com', 'askubuntu.com'),
        'flags': ['StackExchange.user.init'],
        'regex': r'StackExchange\.user\.init\(\{\s*userId:\s*(?P<uid>\d+),\s*accountId:\s*(?P<stack_exchange_uid>\d+)\s*\}\)',
    },
    'SoundCloud': {
        'url_hints': ('soundcloud.com',),
        'flags': ['eventlogger.soundcloud.com'],
        'regex': r'{"hydratable":"user","data":({.+?)}];',
        'extract_json': True,
        'message': 'Run with auth cookies to get your ids.',
        'transforms': [
            json.loads,
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x['id'],
            'name': lambda x: x['full_name'],
            'username': lambda x: x['username'].lstrip('@'),
            'following_count': lambda x: x['followings_count'],
            'follower_count': lambda x: x['followers_count'],
            'is_verified': lambda x: x['verified'],
            'image': lambda x: x['avatar_url'],
            'location': lambda x: x['city'],
            'country_code': lambda x: x['country_code'],
            'bio': lambda x: x['description'],
            'created_at': lambda x: x['created_at'],
            'updated_at': lambda x: x.get('last_modified'),
            'comments_count': lambda x: x.get('comments_count'),
            'likes_count': lambda x: x.get('likes_count')
        }
    },
    'TikTok': {
        # Modern web: __UNIVERSAL_DATA_FOR_REHYDRATION__ (SIGI_STATE is absent on current pages)
        'url_hints': ('tiktok.com', 'tiktokcdn.com'),
        'flags': ['__UNIVERSAL_DATA_FOR_REHYDRATION__', '"secUid"'],
        'regex': r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>([\s\S]*?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['__DEFAULT_SCOPE__']['webapp.user-detail']['userInfo'],
            lambda x: {**x['user'], **x['stats']},
            json.dumps,
        ],
        'fields': {
            'tiktok_id': lambda x: x['id'],
            'tiktok_username': lambda x: x['uniqueId'],
            'fullname': lambda x: x['nickname'],
            'bio': lambda x: x['signature'],
            'image': lambda x: x.get('avatarMedium') or x.get('avatarLarger'),
            'is_verified': lambda x: x['verified'],
            'is_secret': lambda x: x['secret'],
            'sec_uid': lambda x: x['secUid'],
            'following_count': lambda x: x['followingCount'],
            'follower_count': lambda x: x['followerCount'],
            'heart_count': lambda x: x.get('heartCount', x.get('heart')),
            'video_count': lambda x: x['videoCount'],
            'digg_count': lambda x: x['diggCount'],
        }
    },
    'TikTok (legacy SIGI_STATE)': {
        'url_hints': ('tiktok.com', 'tiktokcdn.com'),
        'flags': ['tiktokcdn.com', 'SIGI_STATE'],
        'regex': r'<script id="SIGI_STATE"[^>]+>(.+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: {**x['UserModule']['users'].get(x['UserPage']['uniqueId'], {}),
                       **x['UserModule']['stats'].get(x['UserPage']['uniqueId'], {})},
            json.dumps,
        ],
        'fields': {
            'tiktok_id': lambda x: x['id'],
            'tiktok_username': lambda x: x['uniqueId'],
            'fullname': lambda x: x['nickname'],
            'bio': lambda x: x['signature'],
            'image': lambda x: x['avatarMedium'],
            'is_verified': lambda x: x['verified'],
            'is_secret': lambda x: x['secret'],
            'sec_uid': lambda x: x['secUid'],
            'following_count': lambda x: x['followingCount'],
            'follower_count': lambda x: x['followerCount'],
            'heart_count': lambda x: x['heartCount'],
            'video_count': lambda x: x['videoCount'],
            'digg_count': lambda x: x['diggCount'],
        }
    },
    'Picsart API': {
        # API may serialize JSON with or without spaces; these keys appear in success payloads
        'url_hints': ('picsart.com', 'api.picsart.com'),
        'flags': ['remix_score', 'dashboard_visibility'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(?:www\.)?picsart\.com/u/(?P<username>[^/]+)/?',
                'to': 'https://api.picsart.com/users/show/{username}.json',
            }
        ],
        'fields': {
            'picsart_id': lambda x: x.get('id'),
            'picsart_username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name'),
            'image': lambda x: x.get('photo'),
            'bio': lambda x: x.get('status_message'),
            'follower_count': lambda x: x.get('followers_count'),
            'following_count': lambda x: x.get('following_count'),
            'likes_count': lambda x: x.get('likes_count'),
            'photos_count': lambda x: x.get('photos_count'),
            'is_verified': lambda x: x.get('is_verified'),
            'facebook_uid': lambda x: m.group(1) if x.get('photo') and (m := re.search(r'graph\.facebook\.com/(\d+)/picture', x.get('photo', ''))) else None,
        }
    },
    'VC.ru': {
        'url_hints': ('vc.ru',),
        'flags': ['property="og:site_name" content="vc.ru"', '"subsite":{"id"'],
        'regex': r'({"module.page":{.+});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['module.page']['subsite']['id'],
            'name': lambda x: x['module.page']['subsite']['name'],
            'username': lambda x: x['module.page']['subsite']['url'].split('/')[-1],
        }
    },
    'LiveJournal': {
        'url_hints': ('livejournal.com',),
        'flags': ['Site.journal'],
        'regex': r'Site.journal = ({.+?});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['id'],
            'is_paid': lambda x: x['is_paid'],
            'is_news': lambda x: x['is_news'],
            'is_identity': lambda x: x['is_identity'],
            'is_medius': lambda x: x['is_medius'],
            'is_permanent': lambda x: x['is_permanent'],
            'is_community': lambda x: x['is_community'],
            'is_personal': lambda x: x['is_personal'],
            'is_suspended': lambda x: x['is_suspended'],
            'is_bad_content': lambda x: x['is_bad_content'],
            'username': lambda x: x['username'],
            'name': lambda x: x['display_username'],
        }
    },
    'MySpace': {
        'url_hints': ('myspace.com',),
        'flags': ['myspacecdn.com'],
        'regex': r'context = ({.+?});',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['displayProfileId'],
            'username': lambda x: x['filterStreamUrl'].split('/')[2],
        }
    },
    'Keybase API': {
        'url_hints': ('keybase.io',),
        'flags': ['{"status":{"code":0,"name":"OK"},"them":'],
        'regex': r'^(.+?"them":\[{.+?}\]})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['them'][0]['id'],
            'username': lambda x: x['them'][0]['basics']['username'],
            'name': lambda x: x['them'][0].get('profile', {}).get('full_name'),
            'location': lambda x: x['them'][0].get('profile', {}).get('location'),
            'bio': lambda x: x['them'][0].get('profile', {}).get('bio'),
            'twitter_username': lambda x: x['them'][0]['proofs_summary']['by_presentation_group'].get('twitter', [{}])[
                0].get('nametag'),
            'github_username': lambda x: x['them'][0]['proofs_summary']['by_presentation_group'].get('github', [{}])[
                0].get('nametag'),
            'reddit_username': lambda x: x['them'][0]['proofs_summary']['by_presentation_group'].get('reddit', [{}])[
                0].get('nametag'),
            'hackernews_username': lambda x:
            x['them'][0]['proofs_summary']['by_presentation_group'].get('hackernews', [{}])[0].get('nametag'),
        }
    },
    'Wikimapia': {
        'url_hints': ('wikimapia.org',),
        'flags': ['src="/js/linkrouter.js', 'container-fluid inner-page'],
        'regex': r'<tr class="current">[\s\S]{10,100}a href="\/user\/(?P<wikimapia_uid>\d+)">\n\s+.{10,}\n\s+<strong>(?P<username>.+?)<\/strong>[\s\S]{50,200}<\/tr>',
    },
    # unactual
    'Vimeo HTML': {
        'url_hints': ('vimeo.com', 'vimeocdn.com'),
        'flags': ['ProfilePage', 'vimeo://app.vimeo.com/users/', 'vimeocdn.com'],
        'regex': r'<script type="application/ld\+json">\s*(\[\{[\s\S]*?\}\])\s*</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x[0] if isinstance(x, list) else x,
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x['mainEntity'].get('identifier'),
            'username': lambda x: x['mainEntity'].get('alternateName'),
            'fullname': lambda x: x['mainEntity'].get('name'),
            'bio': lambda x: html.unescape(x['mainEntity'].get('description', '') or '') or None,
            'image': lambda x: x['mainEntity'].get('image') or None,
            'created_at': lambda x: x.get('dateCreated'),
            'updated_at': lambda x: x.get('dateModified'),
            'follower_count': lambda x: (x['mainEntity'].get('interactionStatistic') or {}).get('userInteractionCount'),
            'videos_count': lambda x: (x['mainEntity'].get('agentInteractionStatistic') or {}).get('userInteractionCount'),
            'links': lambda x: ', '.join(
                link for link in (x['mainEntity'].get('sameAs') or [])
                if not link.startswith('https://vimeo.com/')
            ) or None,
            'twitter_url': lambda x: next(
                (link for link in (x['mainEntity'].get('sameAs') or [])
                 if 'twitter.com' in link or 'x.com' in link),
                None,
            ),
            'instagram_url': lambda x: next(
                (link for link in (x['mainEntity'].get('sameAs') or [])
                 if 'instagram.com' in link),
                None,
            ),
            'facebook_url': lambda x: next(
                (link for link in (x['mainEntity'].get('sameAs') or [])
                 if 'facebook.com' in link),
                None,
            ),
            'youtube_url': lambda x: next(
                (link for link in (x['mainEntity'].get('sameAs') or [])
                 if 'youtube.com' in link),
                None,
            ),
            'tiktok_url': lambda x: next(
                (link for link in (x['mainEntity'].get('sameAs') or [])
                 if 'tiktok.com' in link),
                None,
            ),
            'linkedin_url': lambda x: next(
                (link for link in (x['mainEntity'].get('sameAs') or [])
                 if 'linkedin.com' in link),
                None,
            ),
        }
    },
    'Vimeo GraphQL API': {
        'url_hints': ('vimeo.com', 'api.vimeo.com'),
        'flags': ['{\n    "uri": "/users/'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x['uri'].split('/')[-1],
            'gender': lambda x: x['gender'],
            'image': lambda x: x['pictures'].get('sizes', [{'link': ''}])[-1]['link'],
            'bio': lambda x: x.get('bio'),
            'location': lambda x: x['location_details'].get('formatted_address'),
            'username': lambda x: x['name'],
            'is_verified': lambda x: x['verified'],
            'skills': lambda x: ','.join(x['skills']),
            'created_at': lambda x: x['created_time'],
            'videos': lambda x: x['metadata']['public_videos']['total'],
            'is_looking_for_job': lambda x: x['available_for_hire'],
            'is_working_remotely': lambda x: x['can_work_remotely'],
        }
    },
    'DeviantArt': {
        'url_hints': ('deviantart.com',),
        'flags': ['window.deviantART = '],
        # Capture from `{"username":"...","country...` greedily — previous
        # `legacyTextEditUrl.+?})` terminator stopped at the first `})` and
        # broke for users whose object had extra fields after that key
        # (e.g. `isNewDeviant`). raw_decode below trims trailing garbage.
        'regex': r'({\\"username\\":\\"[^"]+\\",\\"country[\s\S]+)',
        'extract_json': True,
        'transforms': [
            lambda x: x.replace('\\"', '"'),
            lambda x: x.replace('\\\\"', '\''),
            lambda x: x.replace('\\\\u002F', '/'),
            lambda x: x.replace("\\'", "'"),
            # Trim to the first complete JSON object (the user record);
            # raw_decode finds the matching closing brace regardless of
            # whatever HTML/JS tail the regex pulled in after it.
            lambda x: json.dumps(json.JSONDecoder().raw_decode(x)[0]),
        ],
        'fields': {
            'country': lambda x: x['country'],
            'created_at': lambda x: parse_datetime(x['deviantFor']),
            'gender': lambda x: x['gender'],
            'username': lambda x: x['username'],
            'twitter_username': lambda x: x['twitterUsername'],
            'website': lambda x: x['website'],
            'links': lambda x: [y['value'] for y in x['socialLinks']],
            'tagline': lambda x: x['tagline'],
            'image': lambda x: x['devidDeviation']['author']['usericon'],
            'bio': lambda x: x['textContent']['excerpt'],
        }
    },
    'mssg.me': {
        'url_hints': ('mssg.me',),
        'flags': ['content="https://mssg.me/'],
        'regex': r'window.INITIAL_DATA = (.*);[\s\S]*window.LOCALES',
        'extract_json': True,
        'fields': {
            'fullname': lambda x: x['card']['profile']['fullname'],
            'bio': lambda x: x['card']['profile']['category'],
            'messengers': lambda x: [y.get('messenger') for y in x['card']['messengers']],
            'messenger_values': lambda x: [y.get('name') for y in x['card']['messengers']],
        }
    },
    'Telegram': {
        'url_hints': ('t.me',),
        'flags': ['tgme_page_title'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('div', {'class': 'tgme_page_title'}).find('span').text,
            'image': lambda x: x.find('img', {'class': 'tgme_page_photo_image'}).get('src'),
            'bio': lambda x: x.find('div', {'class': 'tgme_page_description'}).get_text(separator='\n'),
        }
    },
    'BuzzFeed': {
        'url_hints': ('buzzfeed.com',),
        'flags': ['buzzfeed.com', '__NEXT_DATA__'],
        'regex': r'id="__NEXT_DATA__" type="application\/json">(.+?)<\/script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['props']['pageProps'],
            json.dumps,
        ],
        'fields': {
            'uuid': lambda x: x['user_uuid'],
            'id': lambda x: x['user']['id'],
            'fullname': lambda x: x['user']['displayName'],
            'username': lambda x: x['user']['username'],
            'bio': lambda x: x['user']['bio'],
            'posts_count': lambda x: x['buzz_count'],
            'created_at': lambda x: parse_datetime(x['user']['memberSince']),
            'is_community_user': lambda x: x['user']['isCommunityUser'],
            'is_deleted': lambda x: x['user']['deleted'],
            'social_links': lambda x: [y.get('url') for y in x['user']['social']],
            'image': lambda x: 'https://img.buzzfeed.com/buzzfeed-static' + x['user']['image'],
            'image_bg': lambda x: 'https://img.buzzfeed.com/buzzfeed-static' + x['user']['headerImage'],
        }
    },
    'Linktree': {
        'url_hints': ('linktr.ee',),
        'flags': ['linktr.ee', '__NEXT_DATA__'],
        'regex': r'id="__NEXT_DATA__" type="application\/json"[^>]*>(.+?)<\/script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['props']['pageProps'],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x.get('account', {}).get('id'),
            'username': lambda x: x.get('username'),
            'image': lambda x: x.get('profilePictureUrl'),
            'is_active': lambda x: x.get('account', {}).get('isActive'),
            'is_verified': lambda x: x.get('isProfileVerified'),
            'facebook_pixel_id': lambda x: x.get('account', {}).get('facebookPixelId'),
            'google_analytics_id': lambda x: x.get('account', {}).get('googleAnalyticsId'),
            'is_email_verified': lambda x: x.get('account', {}).get('owner', {}).get('isEmailVerified'),
            'bio': lambda x: x.get('description'),
            'tier': lambda x: x.get('account', {}).get('tier'),
            'social_links': lambda x: {(s['type'].lower() if not s['type'].startswith('EMAIL') else 'email'): s['url']
                                       for s in x.get('socialLinks', [])},
            'links': lambda x: [y.get('url') for y in x.get('account', {}).get('links', [])],
        }
    },
    'Twitch': {
        'url_hints': ('twitch.tv', 'twitchcdn.net'),
        'flags': ['crossorigin="anonymous" href="https://gql.twitch.tv/gql"'],
        'regex': r'id="__NEXT_DATA__" type="application\/json">(.+?)<\/script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['props']['relayQueryRecords'],
            lambda x: [v for k, v in x.items() if k.startswith('User') or k.endswith('followers')],
            lambda x: dict(list(x[-1].items()) + list(x[0].items())),
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x.get('id').split('{')[-1],
            # 'views_count': lambda x: x.get('profileViewCount'),
            'username': lambda x: x.get('login'),
            'bio': lambda x: x.get('description'),
            'fullname': lambda x: x.get('displayName'),
            'image': lambda x: x.get('profileImageURL(width:150)'),
            'likes_count': lambda x: x.get('totalCount'),
            'image_bg': lambda x: x.get('bannerImageURL'),
        },
    },
    'vBulletinEngine': {
        'flags': ['vBulletin.register_control'],
        'bs': True,
        'fields': {
            'status': lambda x: x.find('span', {'class': 'online-status'}).findAll('span')[1].text,
            'country': lambda x: (x.find('span', {'class': 'sprite_flags'}) or {}).get('title'),
            'image': lambda x: x.find('span', {'class': 'avatarcontainer'}).find('img').get('src'),
        }
    },
    'Tumblr (default theme)': {
        'url_hints': ('tumblr.com',),
        'flags': ['https://assets.tumblr.com'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('h1', {'class': 'blog-title'}).find('a').text,
            'title': lambda x: x.find('div', {'class': 'title-group'}).find('span',
                                                                            {'class': 'description'}).text.strip(),
            'image': lambda x: x.find('a', {'class': 'user-avatar'}).find('img').get('src'),
            'image_bg': lambda x: x.find('a', {'class': 'header-image'}).get('data-bg-image'),
            'links': lambda x: [enrich_link(a.find('a').get('href')) for a in
                                x.find('div', {'class': 'nav-wrapper'}).find_all('li',
                                                                                 {'class': 'nav-item nav-item--page'})],
        }
    },
    '1x.com': {
        'url_hints': ('1x.com',),
        'flags': ['content="https://www.1x.com/'],
        'bs': True,
        'fields': {
            'fullname': lambda x:
            x.find('div', {'class': 'coveroverlay'}).find('td', {'valign': 'bottom'}).find('div').contents[0],
            'image': lambda x: 'https://1x.com/' + x.find('img', {'class': 'member_profilepic'}).get('src', ''),
        }
    },
    'Last.fm': {
        'url_hints': ('last.fm',),
        'flags': ['Music Profile | Last.fm</title>'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('span', {'class': 'header-title-display-name'}).contents[0].strip(),
            'bio': lambda x: x.find('span', {'class': 'header-scrobble-since'}).contents[0].strip(),
            'image': lambda x: x.find('span', {'class': 'avatar'}).find('img').get('src', ''),
            'created_at': lambda x: (lambda m: m.group(1) if m else None)(re.search(r'(\d{4})', x.find('span', {'class': 'header-scrobble-since'}).text)) if x.find('span', {'class': 'header-scrobble-since'}) else None,
        }
    },
    'Ask.fm': {
        'url_hints': ('ask.fm',),
        'flags': [' | ASKfm</title>'],
        'bs': True,
        'fields': {
            'username': lambda x: x.find('form', {'id': 'profileAnswersForm'}).get('action', '').split('/')[-2],
            'fullname': lambda x: x.find('span', {'class': 'userName'}).contents[0],
            'posts_count': lambda x: x.find('div', {'class': 'profileTabAnswerCount'}).contents[0],
            'likes_count': lambda x: x.find('div', {'class': 'profileTabLikeCount'}).contents[0],
            'image': lambda x:
            x.find('a', {'class': 'userAvatar-big'}).get('style').replace('background-image:url(', '').rstrip(
                ')').split(';')[1],
            'location': lambda x: x.find('div', {'class': 'icon-location'}).contents[0],
        }
    },
    'Launchpad': {
        'url_hints': ('launchpad.net',),
        'flags': ['in Launchpad</title>'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('h2', {'id': 'watermark-heading'}).find('a').contents[0],
            'username': lambda x: x.find('dl', {'id': 'launchpad-id'}).find('dd').contents[0],
            'languages': lambda x: x.find('dl', {'id': 'languages'}).find('dd').contents[0].strip(),
            'karma': lambda x: x.find('a', {'id': 'karma-total'}).contents[0],
            'created_at': lambda x: x.find('dd', {'id': 'member-since'}).contents[0],
            'timezone': lambda x: re.sub(r'\s+', ' ',
                                         x.find('dl', {'id': 'timezone'}).find('dd').contents[0] or '').strip(),
            'openpgp_key': lambda x: x.find('dl', {'id': 'pgp-keys'}).find('dd').find('span').text.strip()
        }
    },
    'Xakep.ru': {
        'url_hints': ('xakep.ru',),
        'flags': ['https://xakep.ru/author/'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('div', {'class': 'authorBlock-header'}).find('h4').contents[0],
            'image': lambda x: x.find('div', {'class': 'authorBlock-avatar'}).find('img').get('src', ''),
            'bio': lambda x: '\n'.join(x.find('p', {'class': 'authorBlock-header-bio'}).contents),
            'links': lambda x: [a.get('href') for a in x.find('div', {'class': 'authorBlock-meta'}).findAll('a')],
            'created_at': lambda x: extract_digits(
                x.find('div', {'class': 'authorBlock-header'}).find('h6').contents[0]),
        }
    },
    'Tproger.ru': {
        'url_hints': ('tproger.ru',),
        'flags': ['<meta property="og:url" content="https://tproger.ru/author/'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('h1', {'class': 'author-main__header'}).contents[0],
            'image': lambda x: x.find('div', {'class': 'author-main'}).find('img').get('data-src', ''),
        }
    },
    'Jsfiddle.net': {
        'url_hints': ('jsfiddle.net',),
        'flags': ['<meta name="author" edit="JSFiddle">'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('div', {'class': 'profileDetails'}).find('a').contents[0].strip(),
            'company': lambda x: x.find('div', {'class': 'profileDetails'}).find('div', {'class': 'company'}).contents[
                0].strip(),
            'links': lambda x: [a.get('href') for a in x.find('div', {'class': 'userDetails'}).findAll('a')],
            'image': lambda x: x.find('div', {'class': 'avatar'}).find('img').get('src', ''),
        }
    },
    'Disqus API': {
        'url_hints': ('disqus.com',),
        'flags': ['https://disqus.com/api/users/'],
        'regex': r'^([\s\S]+)$',
        'url_mutations': [
            {
                'from': r'https?://disqus.com/by/(?P<username>[^/]+)/?',
                'to': 'https://disqus.com/api/3.0/users/details?user=username:{username}&attach=userFlaggedUser&api_key=E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F',
            }
        ],
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['response'],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x['id'],
            'fullname': lambda x: x['name'],
            'disqus_username': lambda x: x['username'],
            'bio': lambda x: x['about'],
            'reputation': lambda x: x['reputation'],
            'reputation_label': lambda x: x['reputationLabel'],
            'following_count': lambda x: x['numFollowers'],
            'follower_count': lambda x: x['numFollowing'],
            'location': lambda x: x['location'],
            'is_power_contributor': lambda x: x['isPowerContributor'],
            'is_anonymous': lambda x: x['isAnonymous'],
            'created_at': lambda x: x['joinedAt'],
            'upvotes_count': lambda x: x['numLikesReceived'],
            'website': lambda x: x['url'],
            'forums_count': lambda x: x['numForumsFollowing'],
            'image': lambda x: x['avatar']['large']['permalink'],
            'is_trackers_disabled': lambda x: x['response'],
            'forums_following_count': lambda x: x['numForumsFollowing'],
            'is_private': lambda x: x['isPrivate'],
            'comments_count': lambda x: x['numPosts'],
        }
    },
    'uCoz-like profile page': {
        'url_hints': ('ucoz.',),
        'flags': ['UCOZ-JS-DATA'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('div', string='Имя:').next_sibling.split('[')[0].strip(),
            'url': lambda x: get_ucoz_userlink(x.find('div', string='Пользователь:')),
            'image': lambda x: get_ucoz_image(x),
            'gender': lambda x: x.find('div', string='Имя:').next_sibling.split(' ')[-2],
            'created_at': lambda x: x.find('div', string='Дата регистрации:').next_sibling.strip(),
            'latest_activity_at': lambda x: x.find('div', string='Дата входа:').next_sibling.strip(),
            'link': lambda x: get_ucoz_uid_node(x).parent.get('href'),
            'uidme_uguid': lambda x: get_ucoz_uid_node(x).parent.get('href', '').split('/')[-1],
            'location': lambda x: x.find('div', string='Место проживания:').next_sibling.strip(),
            'country': lambda x: x.find('div', string='Страна:').next_sibling.strip(),
            'city': lambda x: x.find('div', string='Город:').next_sibling.strip(),
            'state': lambda x: x.find('div', string='Штат:').next_sibling.strip(),
            'email': lambda x: get_ucoz_email(x.find('div', string='E-mail:').next_sibling.strip()),
            'birthday': lambda x: x.find('div', string='Дата рождения:').next_sibling.split('[')[0].strip(),
        },
    },
    'uID.me': {
        'url_hints': ('uid.me',),
        'flags': [' - uID.me</title>'],
        'bs': True,
        'fields': {
            'username': lambda x: x.find('title').contents[0].split(' ')[0],
            'image': lambda x: 'https://uid.me' + x.find('img', {'id': 'profile_picture'}).get('src'),
            'headline': lambda x: x.find('h2', {'id': 'profile_headline'}).contents[0].strip(),
            'bio': lambda x: x.find('div', {'id': 'profile_bio'}).contents[0].strip(),
            'contacts': lambda x: [a.contents[0] for a in x.find('div', {'id': 'profile_contacts'}).find_all('a')],
            'email': lambda x: x.find('a', {'id': 'user-email'}).contents[0],
            'phone': lambda x: x.find('span', {'id': 'profile-phone'}).contents[0],
            'skype': lambda x: x.find('span', {'id': 'profile-skype'}).contents[0],
            'location': lambda x: ','.join(
                [a.contents[0] for a in x.find('ul', {'id': 'profile_places'}).find_all('a')]),
            'links': lambda x: [a.get('href') for a in x.find('div', {'id': 'list_my-sites'}).find_all('a')] or None,
        },
    },
    'tapd': {
        'url_hints': ('tapd.co',),
        'flags': ['{"_id"', 'userDetails":{"', '"sid":"'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://tapd.co/(?P<username>[^/]+).*',
                'to': 'https://tapd.co/api/user/getPublicProfile/{username}',
            }
        ],
        'fields': {
            'fullname': lambda x: x['name'],
            'username': lambda x: x['userDetails']['username'],
            'bio': lambda x: x['bio'],
            'views_count': lambda x: x['count'],
            'image': lambda x: 'https://distro.tapd.co/' + x['header']['picture'],
            'links': lambda x: [l['url'].strip() for l in x['links']],
        }
    },
    'freelancer.com': {
        'url_hints': ('freelancer.com',),
        'flags': ['{"status":"success","result":{"users":{'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www.)?freelancer\.com/u/(?P<username>[^/]+).*',
                'to': 'https://www.freelancer.com/api/users/0.1/users?usernames%5B%5D={username}&compact=true',
            }
        ],
        'transforms': [
            json.loads,
            lambda x: list(x['result']['users'].values())[0],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x['id'],
            'nickname': lambda x: x['display_name'],
            'username': lambda x: x['username'],
            'fullname': lambda x: x['public_name'],
            'company': lambda x: x['company'],
            'company_founder_id': lambda x: x['corporate']['founder_id'],
            'role': lambda x: x['role'],
            'location': lambda x: x['location']['city'] + ', ' + x['location']['country']['name'],
            'created_at': lambda x: parse_datetime(x['registration_date']),
        }
    },
    'Yelp': {
        'url_hints': ('yelp.com',),
        'flags': ['yelp.www.init.user_details'],
        'bs': True,
        'fields': {
            # Lambda function to extract Yelp user ID from the meta tag with property 'og:url'
            'yelp_userid': lambda x: x.find('meta', {'property': 'og:url'}).get('content').split('=')[-1],

            # Lambda function to extract the user's full name from a span with itemprop 'name'
            'fullname': lambda x: x.find('h2', {'class': 'css-rlqqlq'}).text,

            # Lambda function to extract the user's location from a span with itemprop 'address'
            'location': lambda x: x.find('p', {'class': 'css-147vps'}).text,

            # Lambda function to extract the user's image URL from an img tag with itemprop 'image'
            'image': lambda x: x.find('img', {'class': 'css-1pz4y59'}).get('src'),

        }
    },
    'Trello API': {
        'url_hints': ('trello.com',),
        'flags': ['"aaId"', '"trophies":'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'fields': {
            'id': lambda x: x['id'],
            'username': lambda x: x['username'],
            'fullname': lambda x: x['fullName'],
            'email': lambda x: x['email'],
            'image': lambda x: x['avatarUrl'] + '/170.png',
            'bio': lambda x: x['bio'],
            'type': lambda x: x['memberType'],
            'gravatar_email_md5_hash': lambda x: x['gravatarHash'],
            'is_verified': lambda x: x['confirmed'],
        }
    },
    'Weibo API': {
        'url_hints': ('weibo.com',),
        'flags': ['"ok":1', '"data":{"user"'],
        'regex': r'^(.+)$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://weibo.com/(?P<username>[^/u][^/]*)/?$',
                'to': 'https://weibo.com/ajax/profile/info?custom={username}',
            },
            {
                'from': r'https?://weibo.com/u/(?P<uid>\d+)/?$',
                'to': 'https://weibo.com/ajax/profile/info?uid={uid}',
            },
        ],
        'fields': {
            'weibo_id': lambda x: x['data']['user']['idstr'],
            'username': lambda x: x['data']['user'].get('domain'),
            'fullname': lambda x: x['data']['user']['screen_name'],
            'bio': lambda x: x['data']['user'].get('description'),
            'image': lambda x: x['data']['user'].get('avatar_hd'),
            'gender': lambda x: x['data']['user'].get('gender'),
            'location': lambda x: x['data']['user'].get('location'),
            'verified': lambda x: x['data']['user'].get('verified'),
            'verified_reason': lambda x: x['data']['user'].get('verified_reason'),
            'follower_count': lambda x: x['data']['user'].get('followers_count'),
            'following_count': lambda x: x['data']['user'].get('friends_count'),
            'statuses_count': lambda x: x['data']['user'].get('statuses_count'),
        }
    },
    # TODO
    'Weibo': {
        'url_hints': ('weibo.com',),
        'flags': ['$CONFIG = {"showAriaEntrance'],
        'regex': r'aria-label',
        'transforms': [
            lambda x: re.split('[\r\n]', x),
            lambda x: [r.split("'") for r in x if r],
            lambda x: {r[1]: r[-2] for r in x},
        ],
        'fields': {
            'weibo_id': lambda x: x['oid'],
            'fullname': lambda x: x['onick'],
            'nickname': lambda x: x['nick'],
            'image': lambda x: x['avatar_large'],
            'gender': lambda x: x['sex'],
            'language': lambda x: x['lang'],
        }
    },
    'ICQ': {
        'url_hints': ('icq.com',),
        'flags': ['a href="//icq.com/app" class="icq-prompt__banner-link"'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find('h2', {'class': 'icq-profile__name'}).contents[0],
            'username': lambda x: x.find('p', {'class': 'icq-profile__subtitle'}).contents[0].strip('\n\t@'),
            'bio': lambda x: x.find('p', {'class': 'icq-profile__description box'}).contents[0].strip('\n\t'),
            'image': lambda x: x.find('meta', {'itemprop': 'image'}).get("content"),
        }
    },
    'Pastebin': {
        'url_hints': ('pastebin.com',),
        'flags': ['src="/themes/pastebin/js/'],
        'bs': True,
        'fields': {
            'image': lambda x: 'https://pastebin.com' + x.find('div', {'class': 'user-icon'}).find('img').get('src'),
            'website': lambda x: x.find('a', {'class': 'web'}).get('href'),
            'location': lambda x: x.find('span', {'class': 'location'}).contents[0],
            'views_count': lambda x: x.find('span', {'class': 'views'}).contents[0].replace(',', ''),
            'all_views_count': lambda x: x.find('span', {'class': 'views -all'}).contents[0].replace(',', ''),
            'created_at': lambda x: x.find('span', {'class': 'date-text'}).get("title"),
        }
    },
    'Periscope': {
        'url_hints': ('periscope.tv', 'pscp.tv'),
        'flags': ['canonicalPeriscopeUrl', 'pscp://user/', 'property="og:site_name" content="Periscope"/>'],
        'regex': r'data-store="(.*)"><div id="PageView"',
        'extract_json': True,
        'transforms': [
            lambda x: x.replace('&quot;', '"'),
            json.loads,
            lambda x: list(x['UserCache']['users'].values())[0]['user'],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x['id'],
            'created_at': lambda x: x['created_at'],
            'periscope_username': lambda x: x['username'],
            'fullname': lambda x: x['display_name'],
            'bio': lambda x: x['description'],
            'follower_count': lambda x: x['n_followers'],
            'following_count': lambda x: x['n_following'],
            'hearts_count': lambda x: x['n_hearts'],
            'broadcasts_count': lambda x: x.get('n_broadcasts'),
            'is_beta_user': lambda x: x['is_beta_user'],
            'is_employee': lambda x: x['is_employee'],
            'is_verified': lambda x: x['isVerified'],
            'is_twitter_verified': lambda x: x['is_twitter_verified'],
            'twitter_uid': lambda x: x.get('twitterUserId'),
            'twitter_screen_name': lambda x: x.get('twitter_screen_name'),
            'image': lambda x: x['profile_image_urls'][0]['url'],
        }
    },
    'Imgur API': {
        'url_hints': ('imgur.com', 'api.imgur.com'),
        'flags': ['"reputation_count"', '"reputation_name"'],
        'regex': r'^([\s\S]+)$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://imgur.com/user/(?P<username>[^/]+)',
                'to': 'https://api.imgur.com/account/v1/accounts/{username}?client_id=546c25a59c58ad7',
            }
        ],
        'fields': {
            'id': lambda x: x['id'],
            'imgur_username': lambda x: x['username'],
            'bio': lambda x: x['bio'],
            'reputation_count': lambda x: x['reputation_count'],
            'reputation_name': lambda x: x['reputation_name'],
            'image': lambda x: x['avatar_url'],
            # Stable direct avatar URL (GET returns image/png); complements CDN avatar_url from API
            'imgur_profile_avatar_url': lambda x: imgur_profile_avatar_url(x.get('username')),
            'created_at': lambda x: x['created_at'],
        }
    },
    'PayPal': {
        'url_hints': ('paypal.com', 'paypal.me'),
        'flags': ["indexOf('qa.paypal.com')", 'PayPalSansSmall-Regular'],
        'regex': r'application/json" id="client-data">(.*)</script><script type="application/json" id="l10n-content">',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['recipientSlugDetails']['slugDetails'],
            json.dumps,
        ],
        'fields': {
            'fullname': lambda x: x['userInfo']['displayName'],
            'alternative_fullname': lambda x: x['userInfo'].get('alternateFullName'),
            'username': lambda x: x['paypalmeSlugName'],
            'payerId': lambda x: x['payerId'],
            'address': lambda x: x['userInfo']['displayAddress'],
            'isProfileStatusActive': lambda x: x['isProfileStatusActive'],
            'primaryCurrencyCode': lambda x: x['userInfo']['primaryCurrencyCode'],
            'image': lambda x: x['userInfo']['profilePhotoUrl'],
        }
    },
    'Tinder': {
        'url_hints': ('tinder.com',),
        'flags': ['<html id="Tinder"', 'content="tinder:'],
        'regex': r'window.__data=(.*);</script><script>window.__intlData=JSON.parse',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['webProfile'],
            json.dumps,
        ],
        'fields': {
            'tinder_username': lambda x: x['username'],
            'birth_date': lambda x: x['user']['birth_date'],
            'id': lambda x: x['user']['_id'],
            'badges_list': lambda x: [badge['type'] for badge in x['user']['badges']],
            'company': lambda x: x['user'].get('jobs')[0]['company']['name'],
            'position_held': lambda x: x['user'].get('jobs')[0]['title']['name'],
            'fullname': lambda x: x['user']['name'],
            'image': lambda x: x['user']['photos'][0]['url'],
            'images': lambda x: [photo['url'] for photo in x['user']['photos']],
            'education': lambda x: [school['name'] for school in x['user']['schools']],

        }
    },
    'ifunny.co': {
        'url_hints': ('ifunny.co',),
        'flags': ['window.__INITIAL_STATE__', '"nick":'],
        'regex': r'window.__INITIAL_STATE__=(.+?);',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['user']['data'],
            json.dumps,
        ],
        'fields': {
            'id': lambda x: x['id'],
            'username': lambda x: x['nick'],
            'bio': lambda x: x['about'],
            'image': lambda x: x['avatar']['url'],
            'follower_count': lambda x: x['num']['subscriptions'],
            'following_count': lambda x: x['num']['subscribers'],
            'posts_count': lambda x: x['num']['total_posts'],
            'created_count': lambda x: x['num']['created'],
            'featured_count': lambda x: x['num']['featured'],
            'smile_count': lambda x: x['num']['total_smiles'],
            'achievement_count': lambda x: x['num']['achievements'],
            'is_verified': lambda x: x['isVerified'],
        }
    },
    'Wattpad API': {
        'url_hints': ('wattpad.com',),
        'flags': ['{"username":"', '"allowCrawler"'],
        'regex': r'^({"username":"(.+)})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www.|a.)?wattpad.com/user/(?P<username>[^/]+).*',
                'to': 'https://www.wattpad.com/api/v3/users/{username}',
            }
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'image': lambda x: x.get('avatar'),
            'image_bg': lambda x: x.get('backgroundUrl'),
            'fullname': lambda x: x.get('name'),
            'description': lambda x: x.get('description'),
            'status': lambda x: x.get('status'),
            'gender': lambda x: x.get('gender'),
            'locale': lambda x: x.get('locale'),
            'created_at': lambda x: x.get('createDate'),
            'updated_at': lambda x: x.get('modifyDate'),
            'location': lambda x: x.get('location'),
            'isPrivate': lambda x: x.get('isPrivate'),
            'is_verified': lambda x: x.get('verified'),
            'verified_email': lambda x: x.get('verified_email'),
            'ambassador': lambda x: x.get('ambassador'),
            'isMuted': lambda x: x.get('isMuted'),
            'allowCrawler': lambda x: x.get('allowCrawler'),
            'follower_count': lambda x: x.get('numFollowers'),
            'following_count': lambda x: x.get('numFollowing'),
            'facebook': lambda x: 'https://www.facebook.com/' + x.get('facebook') if x.get('facebook') else None,
            'twitter': lambda x: 'https://twitter.com/' + x.get('twitter') if x.get('twitter') else None,
            'website': lambda x: x.get('website'),
            'lulu': lambda x: x.get('lulu'),
            'smashwords': lambda x: x.get('smashwords'),
            'bubok': lambda x: x.get('bubok'),
        }
    },
    'Kik': {
        'url_hints': ('kik.me', 'kik.com'),
        'flags': ['{"firstName":"'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://kik.me/(?P<username>[^/]+).*',
                'to': 'https://ws2.kik.com/user/{username}',
            }
        ],
        'fields': {
            'fullname': lambda x: x.get('firstName') + ' ' + x.get('lastName'),
            'image': lambda x: x.get('displayPic'),
            'update_pic_at': lambda x: parse_datetime(x.get('displayPicLastModified')),
        }
    },
    'Docker Hub API': {
        'url_hints': ('hub.docker.com',),
        'flags': ['{"id":"', '"type":"User"}'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://hub.docker.com/u/(?P<username>[^/]+).*',
                'to': 'https://hub.docker.com/v2/users/{username}/',
            }
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'full_name': lambda x: x.get('full_name'),
            'location': lambda x: x.get('location'),
            'company': lambda x: x.get('company'),
            'created_at': lambda x: x.get('data_joined'),
            'type': lambda x: x.get('type'),
            'image': lambda x: x.get('gravatar_url'),
        }
    },
    'Mixcloud API': {
        'url_hints': ('mixcloud.com', 'api.mixcloud.com'),
        'flags': ['"key": "'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www.)?mixcloud.com/(?P<username>[^/]+).*',
                'to': 'https://api.mixcloud.com/{username}/',
            }
        ],
        'fields': {
            'fullname': lambda x: x.get('fullname'),
            'username': lambda x: x.get('username'),
            'country': lambda x: x.get('country'),
            'city': lambda x: x.get('city'),
            'created_at': lambda x: x.get('created_time'),
            'updated_at': lambda x: x.get('updated_time'),
            'description': lambda x: x.get('blog'),
            'image': lambda x: x['pictures'].get('640wx640h'),
            'follower_count': lambda x: x.get('follower_count'),
            'following_count': lambda x: x.get('following_count'),
            'cloudcast_count': lambda x: x.get('cloudcast_count'),
            'favorite_count': lambda x: x.get('favorite_count'),
            'listen_count': lambda x: x.get('listen_count'),
            'is_pro': lambda x: x.get('is_pro'),
            'is_premium': lambda x: x.get('is_premium'),
        }
    },
    'binarysearch API': {
        'url_hints': ('binarysearch.com',),
        'flags': [',"preferredSubmissionPrivacy":'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://binarysearch.com/@/(?P<username>[^/]+).*',
                'to': 'https://binarysearch.com/api/users/{username}/profile',
            }
        ],
        'fields': {
            'uid': lambda x: x['user'].get('id'),
            'username': lambda x: x['user'].get('username'),
            'image': lambda x: x['user'].get('profilePic'),
            'location': lambda x: x['user'].get('location'),
            'created_at': lambda x: parse_datetime(x['user'].get('createTime')),
            'updated_at': lambda x: parse_datetime(x['user'].get('updateTime')),
            'bio': lambda x: x['user'].get('bio'),
            'work': lambda x: x['user'].get('work'),
            'college': lambda x: x['user'].get('college'),
            'Role': lambda x: x['user'].get('preferredRole'),
            'github_url': lambda x: x['user'].get('githubHandle'),
            'twitter_url': lambda x: x['user'].get('twitterHandle'),
            'linkedin_url': lambda x: x['user'].get('linkedinHandle'),
            'links': lambda x: x['user'].get('personalWebsite'),
            'is_admin': lambda x: x['user'].get('isAdmin'),
            'is_verified': lambda x: x['user'].get('isVerified'),
            'HistoryPublic': lambda x: x['user'].get('preferredHistoryPublic'),
            'RoomPublic': lambda x: x['user'].get('preferredRoomPublic'),
            'InviteOnly': lambda x: x['user'].get('preferredInviteOnly'),
        }
    },
    'pr0gramm API': {
        'url_hints': ('pr0gramm.com',),
        'flags': [',"likesArePublic":'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://pr0gramm.com/user/(?P<username>[^/]+).*',
                'to': 'https://pr0gramm.com/api/profile/info?name={username}',
            }
        ],
        'fields': {
            'uid': lambda x: x['user'].get('id'),
            'username': lambda x: x['user'].get('name'),
            'created_at': lambda x: parse_datetime(x['user'].get('registered')),
            'uploadCount': lambda x: x.get('uploadCount'),
            'commentCount': lambda x: x.get('commentCount'),
            'tagCount': lambda x: x.get('tagCount'),
            'likesArePublic': lambda x: x.get('likesArePublic'),
        }
    },
    'Aparat API': {
        'url_hints': ('aparat.com',),
        'flags': ['ProfileMore', 'aparat.com'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www.)?aparat.com/(?P<username>[^/]+)$',
                'to': 'https://www.aparat.com/api/fa/v1/user/user/information/username/{username}',
            }
        ],
        'fields': {
            'uid': lambda x: x['data']['id'],
            'hashed_user_id': lambda x: x['data']['attributes']['hash_user_id'],
            'username': lambda x: x['data']['attributes']['username'],
            'fullname': lambda x: x['data']['attributes']['name'],
            'image': lambda x: x['data']['attributes']['pic_b'],
            'image_bg': lambda x: x['data']['attributes']['cover_src'],
            'follower_count': lambda x: x['data']['attributes']['follower_cnt'],  # not really a number
            'following_count': lambda x: x['data']['attributes']['follow_cnt'],  # not really a number
            'is_official': lambda x: x['data']['attributes']['official'],
            'is_banned': lambda x: x['data']['attributes']['banned'] != "no",
            'links': lambda x: [x['data']['attributes']['url']] + [i['link'] for i in
                                                                   x['included'][0]['attributes']['social']],
            'video_count': lambda x: x['data']['attributes']['video_cnt'],
            'bio': lambda x: x['data']['attributes']['description'],
            'created_at': lambda x: parse_datetime(x['data']['attributes']['start_date']),
        }
    },
    'UnstoppableDomains': {
        'url_hints': ('unstoppabledomains.com',),
        'flags': ['reservedForUserId', 'DomainProduct'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x['searchQuery'],
            'registered_domains': lambda x: [i["productCode"] for i in x["exact"] if i["status"] == "registered"],
            'protected_domains': lambda x: [i["productCode"] for i in x["exact"] if i["status"] == "protected"],
        }
    },
    'memory.lol': {
        'url_hints': ('memory.lol',),
        'flags': ['{"accounts":[{'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'fields': {
            'id': lambda x: x['accounts'][0]['id'],
            'known_usernames': lambda x: [i for i in x['accounts'][0]['screen_names']],
        }
    },
    'Duolingo API': {
        'url_hints': ('duolingo.com',),
        'flags': ['"users":[{', 'learningLanguage', 'duolingo.com'],
        'regex': r'^({[\S\s]+?})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'(?i)https?://(?:www\.)?duolingo\.com/profile/(?P<username>[^/?#]+)',
                'to': 'https://www.duolingo.com/2017-06-30/users?username={username}',
            }
        ],
        'fields': {
            'uid': lambda x: x['users'][0]['id'],
            'username': lambda x: x['users'][0]['username'],
            'fullname': lambda x: x['users'][0]['name'],
            'image': lambda x: enrich_link(x['users'][0].get('picture')) if x['users'][0].get('picture') else None,
            'created_at': lambda x: parse_datetime(x['users'][0].get('creationDate')),
            'url': lambda x: f"https://www.duolingo.com/profile/{x['users'][0]['username']}",
            'location': lambda x: x['users'][0].get('profileCountry'),
            'streak': lambda x: x['users'][0].get('streak'),
            'totalXp': lambda x: x['users'][0].get('totalXp'),
            'learningLanguage': lambda x: x['users'][0].get('learningLanguage'),
            'fromLanguage': lambda x: x['users'][0].get('fromLanguage')
        }
    },
    'TwitchTracker': {
        'url_hints': ('twitchtracker.com',),
        'flags': ['window.channel', 'og:site_name" content="TwitchTracker"'],
        # Inline script assigns a JS object literal (not JSON); capture fields by regex.
        'regex': (
            r'window\.channel\s*=\s*\{[\s\S]*?id:\s*(?P<twitch_channel_id>\d+)[\s\S]*?'
            r"name:\s*'(?P<twitch_username>[^']+)'[\s\S]*?"
            r"created_at:\s*'(?P<created_at>[^']+)'"
        ),
    },
    'Chess.com API': {
        'url_hints': ('chess.com', 'api.chess.com'),
        'flags': ['"player_id"', '"username"', '"status"'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www\.)?chess\.com/member/(?P<username>[^/]+)/?.*',
                'to': 'https://api.chess.com/pub/player/{username}',
            },
        ],
        'fields': {
            'chess_user_id': lambda x: x.get('player_id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name'),
            'title': lambda x: x.get('title'),
            'image': lambda x: x.get('avatar'),
            'country_code': lambda x: (x.get('country') or '').rsplit('/', 1)[-1] if x.get('country') else '',
            'location': lambda x: x.get('location'),
            'follower_count': lambda x: x.get('followers'),
            'status': lambda x: x.get('status'),
            'is_streamer': lambda x: x.get('is_streamer'),
            'is_verified': lambda x: x.get('verified'),
            'twitch_url': lambda x: x.get('twitch_url'),
            'created_at': lambda x: parse_datetime(x.get('joined')) if x.get('joined') else '',
            'latest_activity_at': lambda x: parse_datetime(x.get('last_online')) if x.get('last_online') else '',
        },
    },
    'Roblox user API': {
        'url_hints': ('roblox.com', 'users.roblox.com'),
        'flags': ['"externalAppDisplayName"', '"hasVerifiedBadge"', '"isBanned"'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(www\.)?roblox\.com/users/(?P<id>\d+)/profile/?.*',
                'to': 'https://users.roblox.com/v1/users/{id}',
            },
        ],
        'fields': {
            'roblox_user_id': lambda x: x.get('id'),
            'username': lambda x: x.get('name'),
            'fullname': lambda x: x.get('displayName'),
            'created_at': lambda x: x.get('created'),
            'is_banned': lambda x: x.get('isBanned'),
            'is_verified': lambda x: x.get('hasVerifiedBadge'),
            'bio': lambda x: x.get('description'),
        },
    },
    'Roblox username lookup API': {
        'url_hints': ('roblox.com', 'users.roblox.com'),
        'flags': ['"requestedUsername"', '"hasVerifiedBadge"', '"data":[{'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: (x.get('data') or [{}])[0],
            json.dumps,
        ],
        'fields': {
            'roblox_user_id': lambda x: x.get('id'),
            'username': lambda x: x.get('name'),
            'fullname': lambda x: x.get('displayName'),
            'is_verified': lambda x: x.get('hasVerifiedBadge'),
        },
    },
    'MyAnimeList profile': {
        'url_hints': ('myanimelist.net',),
        'flags': ['myanimelist.net/profile', 'class="user-profile"', 'data-ga-click-param="uid:'],
        'regex': (
            r'property="og:url" content="https://myanimelist\.net/profile/(?P<mal_username>[^"]+)"[\s\S]*?'
            r'data-ga-click-param="uid:(?P<mal_uid>\d+)"'
        ),
    },
    'XVideos profile': {
        'url_hints': ('xvideos.com',),
        'flags': ['xvideos.com/profiles', 'id_user', 'xv-responsive'],
        'regex': r'"id_user":(?P<uid>\d+),"username":"(?P<username>[^"]+)","display":"(?P<fullname>[^"]*)"[\s\S]*?"sex":"(?P<gender>[^"]*)"[\s\S]*?'
                 r'Country:</strong>\s*<span>(?P<country>[^<]*)</span>[\s\S]*?'
                 r'Profile hits:</strong>\s*<span>(?P<profile_hits>[^<]*)</span>[\s\S]*?'
                 r'Subscribers:</strong>\s*<span>(?P<follower_count>[^<]*)</span>[\s\S]*?'
                 r'Signed up:</strong>\s*<span>(?P<created_at>[^(<]*)',
    },
    'lnk.bio': {
        'url_hints': ('lnk.bio',),
        'flags': ['__NEXT_DATA__', 'lnk.bio'],
        'regex': r'<script id="__NEXT_DATA__" type="application/json">([\s\S]+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lnk_bio_next_props,
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('username') or x.get('slug'),
            'fullname': lambda x: x.get('displayName') or x.get('name') or x.get('title'),
            'bio': lambda x: x.get('bio') or x.get('description'),
            'image': lambda x: x.get('avatar') or x.get('image') or x.get('profileImage'),
            'links': lambda x: x.get('links') or x.get('socialLinks'),
        },
    },
    'Wikipedia user API': {
        'url_hints': ('wikipedia.org',),
        'flags': ['"batchcomplete"', '"editcount"'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'url_mutations': [{
            'from': r'https?://(?P<lang>\w+)\.wikipedia\.org/wiki/User:(?P<username>[^/?#]+)',
            'to': 'https://{lang}.wikipedia.org/w/api.php?action=query&list=users&ususers={username}&usprop=editcount|registration|gender&format=json',
        }],
        'fields': {
            'uid': lambda x: x.get('query', {}).get('users', [{}])[0].get('userid'),
            'username': lambda x: x.get('query', {}).get('users', [{}])[0].get('name'),
            'edit_count': lambda x: x.get('query', {}).get('users', [{}])[0].get('editcount'),
            'created_at': lambda x: x.get('query', {}).get('users', [{}])[0].get('registration'),
            'gender': lambda x: x.get('query', {}).get('users', [{}])[0].get('gender') if x.get('query', {}).get('users', [{}])[0].get('gender') != 'unknown' else None,
        },
    },
    'Fandom MediaWiki API': {
        'url_hints': ('fandom.com',),
        'flags': ['"batchcomplete"', '"query"', '"users"'],
        'regex': r'^(\{[\s\S]*\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('query', {}).get('users', [{}])[0].get('userid'),
            'username': lambda x: x.get('query', {}).get('users', [{}])[0].get('name'),
        },
        'url_mutations': [{
            'from': r'https?://(?P<wiki>[^/]+)\.fandom\.com/wiki/User:(?P<username>[^/?#]+)',
            'to': 'https://{wiki}.fandom.com/api.php?action=query&list=users&ususers={username}&format=json',
        }],
    },
    'Substack public profile API': {
        'url_hints': ('substack.com',),
        'flags': ['"handle"', '"profile_set_up_at"'],
        'regex': r'^(\{[\s\S]*\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('handle'),
            'fullname': lambda x: x.get('name'),
            'bio': lambda x: x.get('bio'),
            'image': lambda x: x.get('photo_url'),
            'created_at': lambda x: x.get('profile_set_up_at') or None,
            'twitter_username': lambda x: (x.get('twitterAccount') or {}).get('screen_name') or None,
            'twitter_id': lambda x: (x.get('twitterAccount') or {}).get('twitter_id') or None,
            'publication_subdomain': lambda x: ((x.get('publicationUsers') or [{}])[0].get('publication') or {}).get('subdomain') or None,
            'publication_name': lambda x: ((x.get('publicationUsers') or [{}])[0].get('publication') or {}).get('name') or None,
            'publication_bio': lambda x: ((x.get('publicationUsers') or [{}])[0].get('publication') or {}).get('hero_text') or None,
            'image_cdn': lambda x: 'https://substackcdn.com/image/fetch/w_224,h_224,c_fill,f_webp,q_auto:good,fl_progressive:steep/' + __import__('urllib.parse', fromlist=['quote']).quote(x.get('photo_url', ''), safe='') if x.get('photo_url') else None,
        },
        'url_mutations': [{
            'from': r'https?://substack\.com/@(?P<username>[^/?#]+)',
            'to': 'https://substack.com/api/v1/user/{username}/public_profile',
        }],
    },
    'Lesswrong GraphQL API': {
        'url_hints': ('lesswrong.com',),
        'flags': ['"displayName"', '"slug"', '"karma"', '"createdAt"'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('data', {}).get('user', {}).get('result', {}),
            json.dumps,
        ],
        'fields': {
            'fullname': lambda x: x.get('displayName'),
            'username': lambda x: x.get('slug'),
            'karma': lambda x: x.get('karma'),
            'bio': lambda x: x.get('bio') or None,
            'created_at': lambda x: x.get('createdAt'),
        },
    },
    'hashnode GraphQL API': {
        'url_hints': ('hashnode.com', 'gql.hashnode.com'),
        'flags': ['"dateJoined"', '"socialMediaLinks"'],
        'regex': r'^(\{[\s\S]*\})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('data', {}).get('user', {}).get('username') if x.get('data', {}).get('user') else None,
            'fullname': lambda x: x.get('data', {}).get('user', {}).get('name') if x.get('data', {}).get('user') else None,
            'bio': lambda x: x.get('data', {}).get('user', {}).get('tagline') or None if x.get('data', {}).get('user') else None,
            'created_at': lambda x: x.get('data', {}).get('user', {}).get('dateJoined') if x.get('data', {}).get('user') else None,
            'twitter_username': lambda x: (x.get('data', {}).get('user', {}).get('socialMediaLinks', {}) or {}).get('twitter', '').rstrip('/').rsplit('/', 1)[-1] or None if x.get('data', {}).get('user') else None,
            'github_username': lambda x: (x.get('data', {}).get('user', {}).get('socialMediaLinks', {}) or {}).get('github', '').rstrip('/').rsplit('/', 1)[-1] or None if x.get('data', {}).get('user') else None,
            'website': lambda x: (x.get('data', {}).get('user', {}).get('socialMediaLinks', {}) or {}).get('website') or None if x.get('data', {}).get('user') else None,
        },
        'url_mutations': [{
            'from': r'https?://hashnode\.com/@(?P<username>[^/?#]+)',
            'to': 'https://gql.hashnode.com?query=%7Buser(username%3A%20%22{username}%22)%20%7B%20name%20username%20tagline%20dateJoined%20socialMediaLinks%20%7B%20twitter%20github%20linkedin%20website%20%7D%20%7D%7D',
        }],
    },
    'Rarible API': {
        'url_hints': ('rarible.com',),
        'flags': ['"createDate"', '"owner"', '"ref"'],
        'regex': r'^(\{[\s\S]*\})$',
        'extract_json': True,
        'fields': {
            'rarible_id': lambda x: x.get('id'),
            'rarible_owner': lambda x: x.get('owner'),
            'rarible_ref': lambda x: x.get('ref'),
            'rarible_type': lambda x: x.get('type'),
            'created_at': lambda x: x.get('createDate'),
        },
        'url_mutations': [{
            'from': r'https?://rarible\.com/(?P<username>[^/?#]+)$',
            'to': 'https://rarible.com/marketplace/api/v4/urls/{username}',
        }],
    },
    'CSSBattle': {
        'url_hints': ('cssbattle.dev',),
        'flags': ['__NEXT_DATA__', 'cssbattle.dev'],
        'regex': r'<script id="__NEXT_DATA__" type="application/json">([\s\S]+?)</script>',
        'extract_json': True,
        'fields': {
            'cssbattle_id': lambda x: x.get('props', {}).get('pageProps', {}).get('player', {}).get('id'),
            'cssbattle_username': lambda x: x.get('props', {}).get('pageProps', {}).get('player', {}).get('username'),
            'cssbattle_games_played': lambda x: x.get('props', {}).get('pageProps', {}).get('player', {}).get('gamesPlayed'),
            'cssbattle_score': lambda x: x.get('props', {}).get('pageProps', {}).get('player', {}).get('score'),
        },
    },
    'Max (max.ru) profile': {
        'url_hints': ('max.ru',),
        'flags': ['channel:{title:"'],
        'regex': r'channel:\{title:"(?P<max_title>[^"]*)",description:"(?P<max_description>[^"]*)",icon:"(?P<max_icon>[^"]*)",participantsCount:(?P<max_participants_count>\d+)\}',
    },
    'Bluesky API': {
        'url_hints': ('bsky.app', 'bsky.social', 'api.bsky.app'),
        'flags': ['"did":', '"handle":', '"followersCount"'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'url_mutations': [{
            'from': r'https?://bsky\.app/profile/(?P<handle>[^/?#]+)',
            'to': 'https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={handle}',
        }],
        'fields': {
            'uid': lambda x: x.get('did'),
            'username': lambda x: x.get('handle', '').removesuffix('.bsky.social') if x.get('handle') else None,
            'fullname': lambda x: x.get('displayName'),
            'bio': lambda x: x.get('description'),
            'image': lambda x: x.get('avatar'),
            'image_bg': lambda x: x.get('banner'),
            'created_at': lambda x: x.get('createdAt'),
            'follower_count': lambda x: x.get('followersCount'),
            'following_count': lambda x: x.get('followsCount'),
            'posts_count': lambda x: x.get('postsCount'),
        },
    },
    'Scratch API': {
        'url_hints': ('scratch.mit.edu',),
        'flags': ['"scratchteam"', '"history"', '"profile"'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'url_mutations': [{
            'from': r'https?://scratch\.mit\.edu/users/(?P<username>[^/?#]+)',
            'to': 'https://api.scratch.mit.edu/users/{username}',
        }],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'bio': lambda x: x.get('profile', {}).get('bio'),
            'status': lambda x: x.get('profile', {}).get('status'),
            'country': lambda x: x.get('profile', {}).get('country'),
            'image': lambda x: x.get('profile', {}).get('images', {}).get('90x90'),
            'created_at': lambda x: x.get('history', {}).get('joined'),
            'is_scratchteam': lambda x: x.get('scratchteam'),
        },
    },
    'DailyMotion API': {
        'url_hints': ('dailymotion.com',),
        'flags': ['"avatar_720_url"', '"followers_total"'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'url_mutations': [{
            'from': r'https?://(?:www\.)?dailymotion\.com/(?P<username>[^/?#]+)',
            'to': 'https://api.dailymotion.com/user/{username}?fields=id,username,screenname,description,avatar_720_url,cover_250_url,followers_total,following_total,videos_total,country,created_time,verified,url',
        }],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('screenname'),
            'bio': lambda x: x.get('description'),
            'image': lambda x: x.get('avatar_720_url'),
            'image_bg': lambda x: x.get('cover_250_url'),
            'follower_count': lambda x: x.get('followers_total'),
            'following_count': lambda x: x.get('following_total'),
            'videos_count': lambda x: x.get('videos_total'),
            'country': lambda x: x.get('country'),
            'created_at': lambda x: parse_datetime(x.get('created_time')),
            'is_verified': lambda x: x.get('verified'),
        },
    },
    'SlideShare': {
        'url_hints': ('slideshare.net',),
        'flags': ['slidesharecdn.com', '__NEXT_DATA__'],
        'regex': r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.+?)</script>',
        'extract_json': True,
        'transforms': [
            lambda x: next_data_page_props(json.loads(x), 'user'),
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'fullname': lambda x: x.get('name'),
            'username': lambda x: x.get('login'),
            'image': lambda x: x.get('photo'),
            'bio': lambda x: x.get('description'),
            'slideshow_count': lambda x: x.get('slideshowCount'),
            'follower_count': lambda x: x.get('followersCount'),
            'following_count': lambda x: x.get('followingCount'),
            'city': lambda x: x.get('city') or None,
            'country': lambda x: x.get('country') or None,
            'organization': lambda x: x.get('organization'),
            'occupation': lambda x: x.get('occupation'),
            'website': lambda x: x.get('url'),
            'is_suspended': lambda x: x.get('suspended'),
            'is_organization': lambda x: x.get('isOrganization'),
        },
    },
    'WordPress.org Profile': {
        'url_hints': ('profiles.wordpress.org',),
        'flags': ['profiles.wordpress.org', 'user-member-since'],
        'regex': r'<meta property="og:title" content="(?P<fullname>.+?) \(@(?P<username>[^)]+)\)[^"]*"[\s\S]*?<meta property="og:image" content="(?P<image>[^"]+)"',
    },
    'Weebly': {
        'url_hints': ('weebly.com',),
        'flags': ['cdn2.editmysite.com', 'com_currentSite', 'com_userID'],
        'regex': r'com_currentSite\s*=\s*"(?P<weebly_site_id>\d+)";\s*com_userID\s*=\s*"(?P<uid>\d+)"',
    },
    'Calendly': {
        'url_hints': ('calendly.com',),
        'flags': ['"unavailability_reason"', '"owning_user"', '"organization_uuid"'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'url_mutations': [{
            'from': r'https?://calendly\.com/(?P<username>[^/?#]+)(?:/.*)?',
            'to': 'https://calendly.com/api/booking/profiles/{username}',
        }],
        'fields': {
            'uid': lambda x: x.get('id'),
            'fullname': lambda x: x.get('name'),
            'username': lambda x: x.get('slug'),
            'bio': lambda x: x.get('description'),
            'image': lambda x: x.get('avatar_url') or x.get('logo_url'),
            'owner_uuid': lambda x: x.get('owning_user', {}).get('uuid'),
            'organization_uuid': lambda x: x.get('organization_uuid'),
            'timezone': lambda x: x.get('timezone'),
        },
    },
    'Google Play Developer': {
        'url_hints': ('play.google.com',),
        'flags': ['play.google.com/store', 'AF_initDataCallback'],
        'regex': r'<meta property="og:title" content="Android Apps by (?P<developer_name>.+?) on Google Play"',
    },
    'Amazon Author': {
        'url_hints': ('amazon.com', 'amazon.co.uk', 'amazon.de'),
        'flags': ['stores/author/', 'AuthorSubHeader'],
        'regex': r'"authorName":"(?P<author_name>[^"]+)"[\s\S]*?"authorId":"(?P<author_id>[^"]+)"[\s\S]*?"storeId":"(?P<store_id>[^"]+)"',
    },
    'Habr': {
        'url_hints': ('habr.com',),
        'flags': ['og:site_name" content="Хабр"', 'habr.com/ru/users/'],
        'regex': r'<meta property="og:title" content="(?P<fullname>.+?) aka (?P<username>\w+)\s*[\n\s]*-?\s*"[\s\S]*?<meta property="og:url" content="(?P<website>[^"]+)"',
    },
    'Taplink': {
        'url_hints': ('taplink.cc',),
        'flags': ['og:site_name" content="Taplink"', 'at Taplink'],
        'regex': r'<meta property="og:image" content="(?P<image>[^"]+)"[\s\S]*?<meta property="og:title" content="(?P<fullname>.+?) at Taplink"[\s\S]*?<meta property="og:url" content="https://taplink\.cc/(?P<username>[^"]+)"',
    },
    'Product Hunt': {
        'url_hints': ('producthunt.com',),
        'flags': ['og:site_name" content="Product Hunt"', 'og:type" content="profile"'],
        'regex': r'<meta name="twitter:creator" content="@(?P<twitter_username>[^"]+)"[\s\S]*?<meta property="og:url" content="https://www\.producthunt\.com/@(?P<username>[^"]+)"',
    },
    'Chess.com HTML': {
        'url_hints': ('chess.com',),
        'flags': ['og:site_name" content="Chess.com"', 'Chess Profile'],
        'regex': r'<meta property="og:title" content="(?P<fullname>[^"]+?) \((?P<username>[^)]+)\) - Chess Profile"[\s\S]*?<meta property="og:image" content="(?P<image>[^"]+)"',
        'url_mutations': [{
            'from': r'https?://(?:www\.)?chess\.com/member/(?P<username>[^/?#]+)',
            'to': 'https://api.chess.com/pub/player/{username}',
        }],
    },
    'Roblox HTML': {
        'url_hints': ('roblox.com',),
        'flags': ['og:site_name" content="Roblox"', 'og:type" content="profile"'],
        'regex': r'<meta property="og:title" content="(?P<username>[^&\']+?)(?:&#x27;|\')?s Profile"[\s\S]*?<meta property="og:url" content="https://www\.roblox\.com/users/(?P<uid>\d+)/profile"[\s\S]*?<meta property="og:image" content="(?P<image>[^"]+)"',
        'url_mutations': [{
            'from': r'https?://(?:www\.)?roblox\.com/users/(?P<id>\d+)/profile',
            'to': 'https://users.roblox.com/v1/users/{id}',
        }],
    },
    'LeetCode GraphQL': {
        'url_hints': ('leetcode.com',),
        'url_mutations': [
            {
                'from': r'https?://leetcode\.com/(?:u/)?(?P<username>[^/]+)/?$',
                'to': 'https://leetcode.com/graphql?query=query%20userPublicProfile%28%24username%3A%20String%21%29%20%7B%20matchedUser%28username%3A%20%24username%29%20%7B%20username%20profile%20%7B%20realName%20aboutMe%20userAvatar%20countryName%20company%20school%20ranking%20%7D%20%7D%20%7D&variables=%7B%22username%22%3A%20%22{username}%22%7D',
            }
        ],
        'flags': ['"data":', '"matchedUser":', '"profile":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('data', {}).get('matchedUser', {}),
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('profile', {}).get('realName') or None,
            'bio': lambda x: x.get('profile', {}).get('aboutMe') or None,
            'image': lambda x: x.get('profile', {}).get('userAvatar'),
            'country': lambda x: x.get('profile', {}).get('countryName') or None,
            'company': lambda x: x.get('profile', {}).get('company') or None,
            'school': lambda x: x.get('profile', {}).get('school') or None,
            'ranking': lambda x: x.get('profile', {}).get('ranking'),
        },
    },
    'Boosty API': {
        'url_hints': ('boosty.to',),
        'flags': ['"owner":', '"avatarUrl":', '"signedQuery":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('owner', {}).get('id'),
            'fullname': lambda x: x.get('owner', {}).get('name'),
            'image': lambda x: x.get('owner', {}).get('avatarUrl'),
            'blog_title': lambda x: x.get('title'),
            'blog_description': lambda x: ' '.join(
                json.loads(b['content'])[0]
                for b in (x.get('description') or [])
                if b.get('type') in ('text', 'link') and b.get('content')
                and isinstance(json.loads(b['content']), list)
                and json.loads(b['content'])[0]
            ).strip() or None,
            'telegram_username': lambda x: (x.get('owner', {}).get('externalApps', {}).get('telegram', {}).get('username') or None),
        },
    },
    'Threads': {
        'url_hints': ('threads.net', 'threads.com'),
        'flags': ['Threads, Say more', 'barcelona'],
        'regex': r'(?:"data":{"user":)(.*)(?:},"extensions)',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('full_name'),
            'bio': lambda x: x.get('biography'),
            'image': lambda x: x.get('hd_profile_pic_versions', [{}])[-1].get('url'),
            'follower_count': lambda x: x.get('follower_count'),
            'is_verified': lambda x: x.get('is_verified'),
            'links': lambda x: [entry.get('url') for entry in x.get('bio_links')],
        }
    },
    'Smule': {
        'url_hints': ('smule.com',),
        'flags': ['smule.com', 'Profile: {"user"'],
        'regex': r'Profile:\s*(\{[^\n]+\})',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('user', {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('account_id'),
            'username': lambda x: x.get('handle'),
            'image': lambda x: x.get('pic_url'),
            'follower_count': lambda x: x.get('followers'),
            'following_count': lambda x: x.get('followees'),
        },
    },
    'Warpcast API': {
        'url_hints': ('warpcast.com',),
        'flags': ['"result":', '"fid":', '"connectedAccounts":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['result']['user'],
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('fid'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('displayName'),
            'bio': lambda x: x.get('profile', {}).get('bio', {}).get('text') or None,
            'image': lambda x: x.get('pfp', {}).get('url'),
            'url': lambda x: x.get('profile', {}).get('url') or None,
            'follower_count': lambda x: x.get('followerCount'),
            'following_count': lambda x: x.get('followingCount'),
            'twitter_username': lambda x: next(
                (a['username'] for a in x.get('connectedAccounts', [])
                 if a.get('platform') == 'x' and a.get('username')),
                None,
            ),
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?warpcast\.com/(?P<username>[^/?#]+)',
            'to': 'https://client.warpcast.com/v2/user-by-username?username={username}',
        }],
    },
    'Paragraph API': {
        'url_hints': ('paragraph.com', 'paragraph.xyz'),
        'flags': ['"reputation":', '"lowercase_url":', '"needToSetup":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'paragraph_user_id': lambda x: x.get('userId'),
            'fullname': lambda x: x.get('user', {}).get('displayName', {}).get('fullName') or x.get('name'),
            'username': lambda x: (x.get('lowercase_url') or '').lstrip('@') or None,
            'bio': lambda x: (x.get('user', {}).get('authorBio') or '').strip() or None,
            'image': lambda x: x.get('user', {}).get('avatar_url') or x.get('logo_url') or None,
            'updated_at': lambda x: parse_datetime(x.get('updatedAt')),
            'latest_activity_at': lambda x: parse_datetime(x.get('latestPostModifiedTs')),
            'twitter_username': lambda x: (x.get('user', {}).get('social', {}).get('twitter') or x.get('social', {}).get('twitter') or '').strip() or None,
            'github_username': lambda x: (x.get('user', {}).get('social', {}).get('github') or '').strip() or None,
            'facebook_username': lambda x: (x.get('user', {}).get('social', {}).get('facebook') or '').strip() or None,
            'instagram_username': lambda x: (x.get('user', {}).get('social', {}).get('instagram') or '').strip() or None,
            'wallet_address': lambda x: x.get('user', {}).get('wallet_address') or None,
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?paragraph\.(?:com|xyz)/@(?P<username>[^/?#]+)',
            'to': 'https://paragraph.com/api/blogs/@{username}',
        }],
    },
    'Fragment': {
        'url_hints': ('fragment.com',),
        'flags': ['Fragment Auctions', 'tm-wallet'],
        'regex': r'<title>(?P<telegram_username>[^<]+?)\s*.\s*Fragment</title>[\s\S]*?class="table-cell-value tm-value icon-before icon-ton">(?P<sale_price>[^<]+)</div>[\s\S]*?href="https://tonviewer\.com/(?P<ton_wallet>[^"]+)" class="tm-wallet"[\s\S]*?<time datetime="(?P<purchased_at>[^"]+)"',
    },
    'Tonometerbot': {
        'url_hints': ('tonometerbot.com',),
        'flags': ['og:site_name" content="TonometerBot"'],
        'regex': r'og:title" content="@(?P<username>[^"]+)"[\s\S]*?og:description"\s+content="@[^,]+, Subscribers: (?P<subscriber_count>\d+), NFT.s: (?P<nft_count>\d+)',
    },
    'Spatial': {
        'url_hints': ('spatial.io',),
        'flags': ['"dehydratedState":', '"userID":', '"avatarImageURL":'],
        'regex': r'__NEXT_DATA__[^>]*>(\{[\s\S]+?\})\s*</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['props']['pageProps']['dehydratedState']['queries'][0]['state']['data'],
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('userID'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('displayName'),
            'bio': lambda x: x.get('about') or None,
            'image': lambda x: x.get('avatarImageURL') or None,
            'follower_count': lambda x: x.get('numFollowers'),
            'following_count': lambda x: x.get('numFollowing'),
            'discord_username': lambda x: x.get('socialLinks', {}).get('usernameDiscord') or None,
            'twitter_username': lambda x: x.get('socialLinks', {}).get('usernameTwitter') or None,
            'instagram_username': lambda x: x.get('socialLinks', {}).get('usernameInstagram') or None,
            'linkedin_username': lambda x: x.get('socialLinks', {}).get('usernameLinkedin') or None,
            'tiktok_username': lambda x: x.get('socialLinks', {}).get('usernameTiktok') or None,
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?spatial\.io/@(?P<username>[^/?#]+)',
            'to': 'https://www.spatial.io/@{username}',
        }],
    },
    'OpenSea': {
        'url_hints': ('opensea.io',),
        'flags': ['Profile | OpenSea', '"ProfilePage"'],
        'regex': r'<script type="application/ld\+json">(\{[\s\S]*?\})\s*</script>',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('name'),
            'uid': lambda x: x.get('mainEntity', {}).get('url', '').split('/')[-1] or None,
            'image': lambda x: x.get('mainEntity', {}).get('image') or None,
            'bio': lambda x: x.get('mainEntity', {}).get('description') or None,
            'links': lambda x: ', '.join(x.get('mainEntity', {}).get('sameAs', [])) or None,
        },
    },
    'Hive Blog': {
        'url_hints': ('hive.blog',),
        'flags': ['"userProfiles":', '"metadata":', '"reputation":'],
        'regex': r'<script[^>]*>(\{"community":[\s\S]+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: list(x.get('userProfiles', {}).get('profiles', {}).values())[0],
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('name'),
            'fullname': lambda x: x.get('metadata', {}).get('profile', {}).get('name') or None,
            'bio': lambda x: x.get('metadata', {}).get('profile', {}).get('about') or None,
            'image': lambda x: x.get('metadata', {}).get('profile', {}).get('profile_image') or None,
            'image_bg': lambda x: x.get('metadata', {}).get('profile', {}).get('cover_image') or None,
            'website': lambda x: x.get('metadata', {}).get('profile', {}).get('website') or None,
            'location': lambda x: x.get('metadata', {}).get('profile', {}).get('location') or None,
            'reputation': lambda x: x.get('reputation'),
            'posts_count': lambda x: x.get('post_count'),
            'follower_count': lambda x: x.get('stats', {}).get('followers'),
            'following_count': lambda x: x.get('stats', {}).get('following'),
            'created_at': lambda x: x.get('created'),
            'latest_activity_at': lambda x: x.get('active'),
        },
    },
    # https://pub.orcid.org/v3.0/{orcid}/record
    # Returns JSON only when `Accept: application/json` is sent; default is XML.
    # The richest single endpoint in the academic-OSINT chain: surfaces homepage,
    # social URLs, current employer, PhD institution, Scopus/ResearcherID IDs, etc.
    'ORCID API': {
        'url_hints': ('pub.orcid.org', 'orcid.org'),
        'flags': ['"orcid-identifier":', '"activities-summary":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'^https?://(?:www\.)?orcid\.org/(?P<orcid>\d{4}-\d{4}-\d{4}-\d{3}[\dX])/?$',
                'to': 'https://pub.orcid.org/v3.0/{orcid}/record',
                'headers': {'Accept': 'application/json'},
            },
        ],
        'fields': {
            'orcid': lambda x: safe_deep_get(x, 'orcid-identifier', 'path'),
            'fullname': lambda x: (' '.join(filter(None, [
                safe_deep_get(x, 'person', 'name', 'given-names', 'value'),
                safe_deep_get(x, 'person', 'name', 'family-name', 'value'),
            ])).strip() or None),
            'credit_name': lambda x: safe_deep_get(x, 'person', 'name', 'credit-name', 'value'),
            'bio': lambda x: safe_deep_get(x, 'person', 'biography', 'content'),
            'links': lambda x: [u['url']['value']
                                for u in safe_deep_get(x, 'person', 'researcher-urls', 'researcher-url', default=[]) or []
                                if safe_deep_get(u, 'url', 'value')] or None,
            'interests': lambda x: (', '.join(k['content']
                                              for k in safe_deep_get(x, 'person', 'keywords', 'keyword', default=[]) or []
                                              if k.get('content')) or None),
            'country_code': lambda x: safe_deep_get(x, 'person', 'addresses', 'address', 0, 'country', 'value'),
            'email': lambda x: safe_deep_get(x, 'person', 'emails', 'email', 0, 'email'),
            'other_names': lambda x: [o['content']
                                      for o in safe_deep_get(x, 'person', 'other-names', 'other-name', default=[]) or []
                                      if o.get('content')] or None,
            'external_ids': lambda x: ({e['external-id-type']: e['external-id-value']
                                        for e in safe_deep_get(x, 'person', 'external-identifiers', 'external-identifier', default=[]) or []
                                        if e.get('external-id-type')} or None),
            'company': lambda x: safe_deep_get(
                x, 'activities-summary', 'employments', 'affiliation-group', 0,
                'summaries', 0, 'employment-summary', 'organization', 'name'),
            'occupation': lambda x: safe_deep_get(
                x, 'activities-summary', 'employments', 'affiliation-group', 0,
                'summaries', 0, 'employment-summary', 'role-title'),
            'education_school': lambda x: safe_deep_get(
                x, 'activities-summary', 'educations', 'affiliation-group', 0,
                'summaries', 0, 'education-summary', 'organization', 'name'),
            'education_degree': lambda x: safe_deep_get(
                x, 'activities-summary', 'educations', 'affiliation-group', 0,
                'summaries', 0, 'education-summary', 'role-title'),
            'created_at': lambda x: safe_deep_get(x, 'history', 'submission-date', 'value'),
            'posts_count': lambda x: len(safe_deep_get(x, 'activities-summary', 'works', 'group', default=[]) or []) or None,
            'is_verified': lambda x: safe_deep_get(x, 'history', 'verified-primary-email'),
        },
    },
    # https://api.openalex.org/authors/orcid:{orcid}
    # Bibliometric stats + affiliations + research topics keyed off ORCID.
    'OpenAlex Authors API': {
        'url_hints': ('api.openalex.org', 'openalex.org'),
        'flags': ['"works_count":', '"cited_by_count":', '"summary_stats":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'^https?://(?:www\.)?orcid\.org/(?P<orcid>\d{4}-\d{4}-\d{4}-\d{3}[\dX])/?$',
                'to': 'https://api.openalex.org/authors/orcid:{orcid}',
            },
            {
                'from': r'^https?://openalex\.org/(?P<openalex_id>A\d+)/?$',
                'to': 'https://api.openalex.org/authors/{openalex_id}',
            },
        ],
        'fields': {
            'orcid': lambda x: (x.get('orcid') or '').replace('https://orcid.org/', '') or None,
            'openalex_id': lambda x: (x.get('id') or '').replace('https://openalex.org/', '') or None,
            'fullname': lambda x: x.get('display_name'),
            'name_alternatives': lambda x: x.get('display_name_alternatives') or None,
            'posts_count': lambda x: x.get('works_count'),
            'cited_by_count': lambda x: x.get('cited_by_count'),
            'h_index': lambda x: safe_deep_get(x, 'summary_stats', 'h_index'),
            'i10_index': lambda x: safe_deep_get(x, 'summary_stats', 'i10_index'),
            'company': lambda x: safe_deep_get(x, 'last_known_institutions', 0, 'display_name'),
            'country_code': lambda x: safe_deep_get(x, 'last_known_institutions', 0, 'country_code'),
            'institutions': lambda x: [i['display_name']
                                       for i in x.get('last_known_institutions') or []
                                       if i.get('display_name')] or None,
            'interests': lambda x: (', '.join(t['display_name']
                                              for t in (x.get('topics') or [])[:5]
                                              if t.get('display_name')) or None),
            'created_at': lambda x: x.get('created_date'),
            'updated_at': lambda x: x.get('updated_date'),
        },
    },
    # https://arxiv.org/a/{orcid}
    # NB: arXiv only links the page if the user explicitly connected ORCID
    # in arXiv's UI. A 404 (or empty list) does NOT prove "not on arXiv".
    'arXiv author page': {
        'url_hints': ('arxiv.org',),
        'flags': ["'s articles on arXiv"],
        'bs': True,
        'url_mutations': [
            {
                'from': r'^https?://(?:www\.)?orcid\.org/(?P<orcid>\d{4}-\d{4}-\d{4}-\d{3}[\dX])/?$',
                'to': 'https://arxiv.org/a/{orcid}',
            },
        ],
        'fields': {
            'fullname': lambda x: next(
                (h.get_text().split("'s articles on arXiv")[0].strip()
                 for h in x.find_all('h1')
                 if "'s articles on arXiv" in h.get_text()),
                None),
            'arxiv_ids': lambda x: list(dict.fromkeys(
                a['href'].split('/abs/', 1)[1].split('?')[0].rstrip('/')
                for a in x.find_all('a', href=True)
                if '/abs/' in a['href']
            )) or None,
            'posts_count': lambda x: len({
                a['href'].split('/abs/', 1)[1].split('?')[0].rstrip('/')
                for a in x.find_all('a', href=True)
                if '/abs/' in a['href']
            }) or None,
        },
    },
    # https://dblp.org/orcid/{orcid}.xml (and pid/XX/YY.xml)
    # XML person record; computer-science only. Affiliation, homepages,
    # cross-links to Scholar/ACM/Wikipedia/Wikidata/ISNI/ORCID all live here.
    # html.parser handles this fine (XMLParsedAsHTMLWarning is acceptable).
    'DBLP person record': {
        'url_hints': ('dblp.org',),
        'flags': ['<dblpperson ', '<author pid='],
        'bs': True,
        'url_mutations': [
            {
                'from': r'^https?://(?:www\.)?orcid\.org/(?P<orcid>\d{4}-\d{4}-\d{4}-\d{3}[\dX])/?$',
                'to': 'https://dblp.org/orcid/{orcid}.xml',
            },
            {
                'from': r'^https?://dblp\.org/pid/(?P<pid>[\w/]+)\.html$',
                'to': 'https://dblp.org/pid/{pid}.xml',
            },
        ],
        'fields': {
            'fullname': lambda x: x.find('dblpperson').get('name'),
            'dblp_pid': lambda x: x.find('dblpperson').get('pid'),
            'posts_count': lambda x: x.find('dblpperson').get('n'),
            'company': lambda x: (x.find('note', attrs={'type': 'affiliation'}).get_text()
                                  if x.find('note', attrs={'type': 'affiliation'}) else None),
            'awards': lambda x: [f"{n.get('label')}: {n.get_text()}"
                                 for n in x.find_all('note', attrs={'type': 'award'})] or None,
            # `<person>` wraps homepage+xref URLs; `<r>` blocks below it hold
            # per-publication URLs which would otherwise drown the signal.
            'links': lambda x: ([u.get_text() for u in x.find('person').find_all('url') if u.get_text()]
                                if x.find('person') else None) or None,
        },
    },
    # https://scholia.toolforge.org/orcid/{orcid} -> redirects to /author/{Q}
    # Page itself is JS-rendered (no name/works in HTML), but the canonical
    # link exposes the Wikidata QID — enough to pivot to Wikidata SPARQL.
    'Scholia author profile': {
        'url_hints': ('scholia.toolforge.org',),
        'flags': ['scholia.toolforge.org/author/Q', 'rel="canonical"'],
        'regex': r'<link rel="canonical" href="https?://scholia\.toolforge\.org/author/(?P<wikidata_qid>Q\d+)"',
        'url_mutations': [
            {
                'from': r'^https?://(?:www\.)?orcid\.org/(?P<orcid>\d{4}-\d{4}-\d{4}-\d{3}[\dX])/?$',
                'to': 'https://scholia.toolforge.org/orcid/{orcid}',
            },
        ],
    },
    'BuyMeACoffee': {
        'url_hints': ('buymeacoffee.com',),
        'flags': ['buymeacoffee.com', 'og:title'],
        'bs': True,
        'fields': {
            'fullname': lambda x: (
                (x.find('meta', property='og:title') and x.find('meta', property='og:title').get('content')) or
                (x.find('title') and x.find('title').text.replace(' - Buymeacoffee', '').strip())
            ),
            'bio': lambda x: (
                (x.find('meta', attrs={'name': 'description'}) and x.find('meta', attrs={'name': 'description'}).get('content')) or
                (x.find('meta', property='og:description') and x.find('meta', property='og:description').get('content'))
            ),
            'image': lambda x: (
                x.find('meta', property='og:image') and x.find('meta', property='og:image').get('content')
            ),
        }
    },
    'Discourse API': {
        'flags': ['"trust_level"', '"badge_count"', '"profile_view_count"'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('user', {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name') or None,
            'title': lambda x: x.get('title') or None,
            'bio': lambda x: x.get('bio_raw') or None,
            'website': lambda x: x.get('website') or None,
            'location': lambda x: x.get('location') or None,
            'image': lambda x: x.get('avatar_template', '').replace('{size}', '240') or None,
            'trust_level': lambda x: x.get('trust_level'),
            'is_moderator': lambda x: x.get('moderator'),
            'is_admin': lambda x: x.get('admin'),
            'badge_count': lambda x: x.get('badge_count'),
            'views_count': lambda x: x.get('profile_view_count'),
            'created_at': lambda x: x.get('created_at'),
            'latest_activity_at': lambda x: x.get('last_seen_at'),
        },
    },
    'Snapchat': {
        'flags': ['__NEXT_DATA__', '"userProfile":'],
        'regex': r'<script[^>]+id="__NEXT_DATA__"[^>]*>([\s\S]+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['props']['pageProps'],
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x['userProfile']['userInfo'].get('username'),
            'fullname': lambda x: x['userProfile']['userInfo'].get('displayName'),
            'bio': lambda x: x.get('pageMetadata', {}).get('pageDescription', {}).get('value'),
            'url': lambda x: x.get('linkPreview', {}).get('canonicalUrl'),
            'image': lambda x: x.get('linkPreview', {}).get('twitterImage', {}).get('url'),
            'snapcode_image': lambda x: x['userProfile']['userInfo'].get('snapcodeImageUrl'),
            'profile_type': lambda x: x['userProfile'].get('$case'),
        }
    },
    'Bio Site': {
        'url_hints': ('bio.site',),
        'flags': ['window.initial_state=', 'media.bio.site', 'Bio Sites'],
        'regex': r'window\.initial_state=({[\s\S]+?});\s*window\.additionalRenderingContext=',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('metadata', {}).get('handle'),
            'fullname': lambda x: x.get('header', {}).get('name'),
            'bio': lambda x: x.get('header', {}).get('bio'),
            'image': lambda x: x.get('header', {}).get('profile_photo'),
            'image_bg': lambda x: x.get('header', {}).get('cover_photo'),
            'created_at': lambda x: parse_datetime(x.get('metadata', {}).get('created_at')),
            'updated_at': lambda x: parse_datetime(x.get('metadata', {}).get('last_updated_at')),
            'links': _bio_site_links,
            'instagram_username': lambda x: _bio_site_social_value(x, 'instagram'),
        },
    },
    'Faceit API': {
        'url_hints': ('faceit.com',),
        'flags': ['"payload"', '"skill_level_label"' ,'"registration_status_v2"'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('payload') or {},
            json.dumps,
        ],
        'url_mutations': [
            {
                'from': r'https?://(?:www\.)?faceit\.com/(?:[a-z]{2}/)?players/(?P<username>[^/?#]+).*',
                'to': 'https://www.faceit.com/api/users/v1/nicknames/{username}',
            },
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('nickname'),
            'image': lambda x: x.get('avatar'),
            'image_bg': lambda x: x.get('cover_image_url'),
            'country_code': lambda x: x.get('country', '').upper() if x.get('country') else None,
            'created_at': lambda x: parse_datetime_str(x.get('created_at')) if x.get('created_at') else None,
            'friends_count': lambda x: len(x.get('friends') or []),
            'faceit_game': lambda x: x.get('flag'),
            'faceit_elo': lambda x: _faceit_current_game(x).get('faceit_elo'),
            'faceit_skill_level': lambda x: _faceit_current_game(x).get('skill_level'),
            'faceit_region': lambda x: _faceit_current_game(x).get('region'),
            'steam_id': lambda x: x.get('platforms', {}).get('steam', {}).get('id64'),
            'steam_nickname': lambda x: x.get('platforms', {}).get('steam', {}).get('nickname'),
            'social_links': lambda x: _faceit_streaming_links(x),
        },
    },
    'Fansly API': {
        'url_hints': ('apiv2.fansly.com', 'fansly.com'),
        'flags': ['"subscriberCount"', '"timelineStats"', '"accountMediaLikes"'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: (x.get('response') or [{}])[0],
            json.dumps,
        ],
        'url_mutations': [
            {
                'from': r'https?://(?:www\.)?fansly\.com/(?P<username>[^/?#]+)',
                'to': 'https://apiv2.fansly.com/api/v1/account?usernames={username}',
            },
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('displayName') or None,
            'follower_count': lambda x: x.get('followCount'),
            'subscriber_count': lambda x: x.get('subscriberCount'),
        },
    },
    'Codewars API': {
        'url_hints': ('codewars.com',),
        # ponytail: structural keys only — no user-dependent values (see FIELDS/flags rule)
        'flags': ['"honor":', '"leaderboardPosition":', '"codeChallenges":'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://(?:www\.)?codewars\.com/users/(?P<username>[^/?#]+).*',
                'to': 'https://www.codewars.com/api/v1/users/{username}',
            },
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name') or None,
            'honor': lambda x: x.get('honor'),
            'clan': lambda x: x.get('clan') or None,
            'leaderboard_position': lambda x: x.get('leaderboardPosition'),
            'rank': lambda x: ((x.get('ranks') or {}).get('overall') or {}).get('name'),
            'rank_score': lambda x: ((x.get('ranks') or {}).get('overall') or {}).get('score'),
            'languages': lambda x: sorted((((x.get('ranks') or {}).get('languages')) or {}).keys()) or None,
            'challenges_completed': lambda x: (x.get('codeChallenges') or {}).get('totalCompleted'),
            'challenges_authored': lambda x: (x.get('codeChallenges') or {}).get('totalAuthored'),
        },
    },
    'Minds API': {
        'url_hints': ('minds.com',),
        # ponytail: structural keys only, present on any successful channel response
        'flags': ['"briefdescription":', '"icontime":', '"boostProPlus"'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('channel') or {},
            json.dumps,
        ],
        'url_mutations': [
            {
                'from': r'https?://(?:www\.)?minds\.com/(?P<username>[^/?#]+).*',
                'to': 'https://www.minds.com/api/v1/channel/{username}',
            },
        ],
        'fields': {
            'uid': lambda x: x.get('guid'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('briefdescription') or None,
            'location': lambda x: x.get('city') or None,
            'gender': lambda x: x.get('gender') or None,
            'website': lambda x: x.get('website') or None,
            'is_verified': lambda x: x.get('verified'),
            'created_at': lambda x: parse_datetime(x['time_created']) if x.get('time_created') else None,
            'image': lambda x: 'https://www.minds.com/icon/{}/large/{}'.format(x['guid'], x.get('icontime')) if x.get('guid') else None,
            # social_profiles: [{key, value}] — scheme-less crosslink URLs (instagram/github/gitlab/...)
            'social_links': lambda x: [p.get('value') for p in (x.get('social_profiles') or []) if p.get('value')] or None,
        },
    },
    'HackerNoon API': {
        'url_hints': ('hackernoon.com', 'hackernoon-app.cloudfunctions.net'),
        # ponytail: all three present on any profile envelope, absent on the {"redirect":…}
        # case-mismatch response and the 404 {"ok":false} body — so neither is mis-parsed.
        'flags': ['"handle":', '"displayName":', '"socialMedia":'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('profile') or {},
            json.dumps,
        ],
        'url_mutations': [
            {
                'from': r'https?://(?:www\.)?hackernoon\.com/u/(?P<username>[^/?#]+).*',
                'to': 'https://us-central1-hackernoon-app.cloudfunctions.net/profilesApi/?handle={username}',
            },
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('handle'),
            'fullname': lambda x: x.get('displayName') or None,
            'bio': lambda x: x.get('bio') or None,
            'email': lambda x: x.get('email') or None,
            'image': lambda x: x.get('avatar'),
            # socialMedia values are mixed (bare handle vs full URL) — keep the platform label,
            # ponytail: per-platform username normalisation is a future enhancement.
            'social_accounts': lambda x: ['{}:{}'.format(k, v) for k, v in (x.get('socialMedia') or {}).items() if v] or None,
        },
    },
    'Polar API': {
        'url_hints': ('polar.sh', 'api.polar.sh'),
        'flags': ['"organization":{', '"slug":'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('organization') or {},
            json.dumps,
        ],
        'url_mutations': [
            {
                'from': r'https?://(?:www\.)?polar\.sh/(?P<username>[^/?#]+).*',
                'to': 'https://api.polar.sh/v1/customer-portal/organizations/{username}',
            },
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('slug'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('bio') or None,
            'company': lambda x: x.get('company') or None,
            'location': lambda x: x.get('location') or None,
            'blog': lambda x: x.get('blog') or None,
            'website': lambda x: x.get('website') or None,
            'email': lambda x: x.get('email') or None,
            'twitter_username': lambda x: x.get('twitter_username') or None,
            'image': lambda x: x.get('avatar_url'),
            # avatar is a GitHub CDN URL → the numeric u/{id} is the github_uid (same as GitHub API)
            'github_uid': lambda x: m.group(1) if (m := re.search(r'githubusercontent\.com/u/(\d+)', x.get('avatar_url') or '')) else None,
            'created_at': lambda x: x.get('created_at') or None,
        },
    },
    'thanks.dev API': {
        'url_hints': ('thanks.dev', 'api.thanks.dev'),
        'flags': ['"git":{', '"ghgl":'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'fields': {
            # shadow profiles (any GitHub user, not registered) set name to the literal `gh/{handle}`
            'fullname': lambda x: x.get('name') if x.get('name') and x.get('name') != 'gh/' + ((x.get('git') or {}).get('name') or '\0') else None,
            'bio': lambda x: x.get('bio') or None,
            'description': lambda x: x.get('resume') or None,
            'website': lambda x: x.get('url') or None,
            'linkedin_url': lambda x: x.get('li') or None,
            # `tw` is sometimes a bare handle, sometimes a full URL — normalise to the handle
            'twitter_username': lambda x: (x.get('tw') or '').rstrip('/').split('/')[-1] or None,
            'discord_invite': lambda x: x.get('dc') or None,
            'bluesky_handle': lambda x: x.get('bs') or None,
            'github_username': lambda x: (x.get('git') or {}).get('name'),
            'is_thanks_dev_user': lambda x: x.get('isTdUser'),
        },
    },
    'Matrix profile API': {
        # federated: works against any homeserver's /_matrix/client/v3/profile/@{user}:{hs} endpoint.
        # Body carries only display name + avatar; username/uid live in the request URL, not here.
        'url_hints': ('matrix.org', '_matrix/client'),
        'flags': ['"displayname":', '"avatar_url":'],
        'regex': r'^({[\S\s]+})$',
        'extract_json': True,
        'fields': {
            'fullname': lambda x: x.get('displayname') or None,
            # mxc://{server}/{id} → media thumbnail URL on matrix.org's media repo
            'image': lambda x: 'https://matrix-client.matrix.org/_matrix/client/v1/media/thumbnail/{}/{}?width=512&height=512&method=scale'.format(*x['avatar_url'][6:].split('/', 1)) if (x.get('avatar_url') or '').startswith('mxc://') and '/' in x['avatar_url'][6:] else None,
        },
    },
    "osu!": {
        "url_hints": ("osu.ppy.sh"),
        "flags": ["data-initial-data=", "osu-layout"],
        "regex": r'data-initial-data="([^"]*)"',
        "extract_json": True,
        "transforms": [
            lambda x: x.replace("&quot;", '"'),
            json.loads,
            lambda x: x.get("user"),
            json.dumps,
        ],
        "fields": {
            "uid": lambda x: x.get("id"),
            "username": lambda x: x.get("username"),
            "image": lambda x: x.get("avatar_url"),
            "image_bg": lambda x: x.get("cover_url"),
            "website": lambda x: x.get("website"),
            "occupation": lambda x: x.get("occupation"),
            "interests": lambda x: x.get("interests"),
            "country": lambda x: x.get("country").get("name"),
            "country_code": lambda x: x.get("country").get("code"),
            "location": lambda x: x.get("location"),
            "created_at": lambda x: x.get("join_date"),
            "latest_activity_at": lambda x: x.get("last_visit"),
            "follower_count": lambda x: x.get("follower_count"),
            "posts_count": lambda x: x.get("post_count"),
            "comments_count": lambda x: x.get("comments_count"),
            "is_deleted": lambda x: x.get("is_deleted"),
            "is_employee": lambda x: x.get("is_admin"),  # maybe not totally correct?
            "is_banned": lambda x: x.get(
                "is_restricted"
            ),  # maybe is_suspended instead of is_banned?
            "social_links": lambda x: [
                {"discord": x.get("discord")},
                {"twitter/x": x.get("twitter")},
            ],
        },
    },
    # Lens Protocol account, shared by every Lens-built client (Hey, Orb,
    # Buttrfly, Tape, ...). The web clients are static SPAs; real data comes
    # from the Lens GraphQL API (POST https://api.lens.xyz/graphql). Maigret
    # does the POST itself and feeds the response body to extract(), so the
    # scheme matches by flags — no url_mutations (mutate_url can't POST).
    'Lens (Hey/Orb/Buttrfly) account': {
        'url_hints': ('api.lens.xyz', 'hey.xyz', 'orb.club', 'buttrfly.app'),
        'flags': ['"account":{', '"localName":', '"namespace":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: (x.get('data') or {}).get('account') or {},
            json.dumps,
        ],
        'fields': {
            'uid':              lambda x: x.get('address'),  # Ethereum wallet, reusable across Lens clients
            'username':         lambda x: (x.get('username') or {}).get('localName'),
            'lens_namespace':   lambda x: (x.get('username') or {}).get('namespace'),
            'fullname':         lambda x: (x.get('metadata') or {}).get('name'),
            'bio':              lambda x: (x.get('metadata') or {}).get('bio'),
            'image':            lambda x: (x.get('metadata') or {}).get('picture'),
            'image_bg':         lambda x: (x.get('metadata') or {}).get('coverPicture'),
            'location':         lambda x: _lens_attr((x.get('metadata') or {}).get('attributes'), 'location'),
            'website':          lambda x: _lens_attr((x.get('metadata') or {}).get('attributes'), 'website'),
            'twitter_username': lambda x: _lens_attr((x.get('metadata') or {}).get('attributes'), 'x', 'twitter'),
            'lens_score':       lambda x: x.get('score'),
            'created_at':       lambda x: parse_datetime_str(x['createdAt']) if x.get('createdAt') else None,
        },
    },
    'HuggingFace API': {
        'url_hints': ('huggingface.co',),
        'flags': ['"numModels":', '"numDatasets":', '"numSpaces":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'url_mutations': [
            {
                'from': r'https?://huggingface\.co/(?P<username>[^/?#]+)',
                'to': 'https://huggingface.co/api/users/{username}/overview',
            },
        ],
        'fields': {
            'uid': lambda x: x.get('_id'),
            'username': lambda x: x.get('user'),
            'fullname': lambda x: x.get('fullname') or None,
            'bio': lambda x: x.get('details') or None,
            'image': lambda x: x.get('avatarUrl') if x.get('avatarUrl') and x.get('avatarUrl').startswith('http') else ('https://huggingface.co' + x.get('avatarUrl') if x.get('avatarUrl') else None),
            'is_pro': lambda x: x.get('isPro'),
            'follower_count': lambda x: x.get('numFollowers'),
            'following_count': lambda x: x.get('numFollowing'),
            'likes_count': lambda x: x.get('numLikes'),
            'upvotes_count': lambda x: x.get('numUpvotes'),
            'created_at': lambda x: x.get('createdAt'),
            'huggingface_models': lambda x: x.get('numModels'),
            'huggingface_datasets': lambda x: x.get('numDatasets'),
            'huggingface_spaces': lambda x: x.get('numSpaces'),
            'huggingface_papers': lambda x: x.get('numPapers'),
        }
    },
    'HackerNews': {
        'url_hints': ('news.ycombinator.com',),
        'flags': ['>created:</td>', '>karma:</td>'],
        'regex': r'^([\s\S]+)$',
        'fields': {
            'username': lambda x: m.group(1) if (m := re.search(r'class="hnuser">([^<]+)</a>', x)) else None,
            'created_at': lambda x: m.group(1).strip() if (m := re.search(r'created:</td><td><span class="age"><a[^>]+>([^<]+)</a></span></td>', x)) else (m2.group(1).strip() if (m2 := re.search(r'created:</td><td>([^<]+)</td>', x)) else None),
            'karma': lambda x: int(re.sub(r'[^\d]', '', m.group(1))) if (m := re.search(r'karma:</td><td>([^<]+)</td>', x)) and re.sub(r'[^\d]', '', m.group(1)) else None,
            'bio': lambda x: re.sub(r'<[^>]+>', '', m.group(1)).strip() if (m := re.search(r'about:</td><td[^>]*>(.*?)</td>', x, re.DOTALL)) else None,
        }
    },
    'GDBrowser API': {
        'url_hints': ('gdbrowser.com',),
        'flags': ['"playerID":', '"accountID":', '"userCoins":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('username'),
            'uid': lambda x: x.get('playerID'),
            'gd_account_id': lambda x: x.get('accountID'),
            'youtube_username': lambda x: x.get('youtube') or None,
            'twitter_username': lambda x: x.get('twitter') or None,
            'twitch_username': lambda x: x.get('twitch') or None,
            'discord_username': lambda x: x.get('discord') or None,
            'instagram_username': lambda x: x.get('instagram') or None,
            'tiktok_username': lambda x: x.get('tiktok') or None,
            'website': lambda x: x.get('customLink') or None,
        },
        'url_mutations': [{
            'from': r'https?://gdbrowser\.com/u/(?P<username>[^/?#]+)',
            'to': 'https://gdbrowser.com/api/profile/{username}',
        }],
    },
    'StreamElements API': {
        'url_hints': ('streamelements.com',),
        'flags': ['"providerId":', '"broadcasterType":', '"isPartner":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('_id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('displayName'),
            'image': lambda x: x.get('avatar') or None,
            'provider': lambda x: x.get('provider'),
            'provider_id': lambda x: x.get('providerId'),
            'is_partner': lambda x: x.get('isPartner'),
        },
        'url_mutations': [{
            'from': r'https?://streamelements\.com/(?P<username>[^/?#]+)',
            'to': 'https://api.streamelements.com/kappa/v2/channels/{username}',
        }],
    },
    'Streamlabs API': {
        'url_hints': ('streamlabs.com',),
        'flags': ['"primary_account":', '"ab_test_group":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'image': lambda x: x.get('logo') or None,
            'primary_account_type': lambda x: x.get('primary_account', {}).get('type'),
            'primary_account_id': lambda x: x.get('primary_account', {}).get('id'),
            'primary_account_username': lambda x: x.get('primary_account', {}).get('username'),
        },
        'url_mutations': [{
            'from': r'https?://streamlabs\.com/(?P<username>[^/?#]+)',
            'to': 'https://streamlabs.com/api/v6/user/{username}',
        }],
    },
    'Donatty API': {
        'url_hints': ('donatty.com',),
        'flags': ['"response":', '"registrationDate":', '"refId":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['response'],
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('refId'),
            'username': lambda x: x.get('name'),
            'fullname': lambda x: x.get('displayName'),
            'image': lambda x: x.get('picture', {}).get('source') or None,
            'created_at': lambda x: x.get('registrationDate'),
            'twitch_url': lambda x: x.get('twitch', {}).get('url') or None,
            'twitch_username': lambda x: x.get('twitch', {}).get('url', '').rstrip('/').split('/')[-1] or None,
        },
        'url_mutations': [{
            'from': r'https?://donatty\.com/(?P<username>[^/?#]+)',
            'to': 'https://api.donatty.com/users/find/{username}',
        }],
    },
    'VisnessCard API': {
        'url_hints': ('visnesscard.com',),
        'flags': ['"card_id":', '"end_point":', '"business_title":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('card_id'),
            'username': lambda x: x.get('end_point'),
            'fullname': lambda x: ' '.join(filter(None, [x.get('first_name'), x.get('last_name')])) or None,
            'email': lambda x: x.get('email') or None,
            'company': lambda x: x.get('company_name') or None,
            'business_title': lambda x: x.get('business_title') or None,
            'location': lambda x: ', '.join(filter(None, [x.get('address'), x.get('suite'), x.get('city'), x.get('state'), x.get('zip')])) or None,
            'website': lambda x: x.get('company_website_1') or x.get('company_website_2') or None,
            'image': lambda x: (x.get('icons', [{}])[0].get('image_key') if x.get('icons') else None) or x.get('android_icon_key') or None,
            'views_count': lambda x: x.get('unique_views') or x.get('views'),
            'created_at': lambda x: x.get('date_created'),
        },
        'url_mutations': [{
            'from': r'https?://my\.visnesscard\.com/(?P<username>[^/?#]+)',
            'to': 'https://my.visnesscard.com/Home/GetCard/{username}',
        }],
    },
    'Codeforces API': {
        'url_hints': ('codeforces.com',),
        'flags': ['"status":"OK"', '"handle":', '"maxRating":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['result'][0],
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('handle'),
            'fullname': lambda x: ' '.join(filter(None, [x.get('firstName'), x.get('lastName')])) or None,
            'country': lambda x: x.get('country') or None,
            'city': lambda x: x.get('city') or None,
            'organization': lambda x: x.get('organization') or None,
            'image': lambda x: x.get('avatar'),
            'image_bg': lambda x: x.get('titlePhoto') or None,
            'rank': lambda x: x.get('rank'),
            'max_rank': lambda x: x.get('maxRank'),
            'rating': lambda x: x.get('rating'),
            'max_rating': lambda x: x.get('maxRating'),
            'contribution': lambda x: x.get('contribution'),
            'follower_count': lambda x: x.get('friendOfCount'),
            'created_at': lambda x: x.get('registrationTimeSeconds'),
        },
        'url_mutations': [{
            'from': r'https?://codeforces\.com/profile/(?P<username>[^/?#]+)',
            'to': 'https://codeforces.com/api/user.info?handles={username}',
        }],
    },
    'Discogs API': {
        'url_hints': ('discogs.com',),
        'flags': ['"wantlist_url":', '"releases_contributed":', '"inventory_url":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('profile') or None,
            'location': lambda x: x.get('location') or None,
            'website': lambda x: x.get('home_page') or None,
            'image': lambda x: x.get('avatar_url') or None,
            'image_bg': lambda x: x.get('banner_url') or None,
            'created_at': lambda x: x.get('registered'),
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?discogs\.com/user/(?P<username>[^/?#]+)',
            'to': 'https://api.discogs.com/users/{username}',
        }],
    },
    'iNaturalist API': {
        'url_hints': ('inaturalist.org',),
        'flags': ['"total_results":', '"observations_count":', '"identifications_count":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['results'][0],
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('login'),
            'fullname': lambda x: x.get('name') or None,
            'image': lambda x: x.get('icon_url') or None,
            'orcid': lambda x: x.get('orcid') or None,
            'observations_count': lambda x: x.get('observations_count'),
            'species_count': lambda x: x.get('species_count'),
            'identifications_count': lambda x: x.get('identifications_count'),
            'created_at': lambda x: x.get('created_at'),
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?inaturalist\.org/people/(?P<username>[^/?#]+)',
            'to': 'https://api.inaturalist.org/v1/users/{username}',
        }],
    },
    'Pronouny API': {
        'url_hints': ('pronouny.xyz',),
        'flags': ['"pronouns":', '"nouns":', '"isPublic":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('_id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x['names'][0] if isinstance(x.get('names'), list) and x['names'] and isinstance(x['names'][0], str) else (x['names'][0].get('name') if isinstance(x.get('names'), list) and x['names'] and isinstance(x['names'][0], dict) else None),
            'bio': lambda x: x.get('bio') or None,
            'image': lambda x: x.get('profileImageURL') if x.get('profileImageURL', '').startswith('http') else None,
            'pronouns': lambda x: ', '.join(p.get('pattern', '').split('/')[0] + '/' + p.get('pattern', '').split('/')[1] if '/' in p.get('pattern', '') else p.get('pattern', '') for p in x.get('pronouns', []) if isinstance(p, dict)) or None,
            'created_at': lambda x: x.get('created'),
        },
        'url_mutations': [{
            'from': r'https?://pronouny\.xyz/u/(?P<username>[^/?#]+)',
            'to': 'https://pronouny.xyz/api/users/profile/username/{username}',
        }],
    },
    'Zepeto API': {
        'url_hints': ('zepeto.io', 'zepeto.me'),
        'flags': ['"zepetoId":', '"hashCode":', '"isCreator":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('zepetoId'),
            'fullname': lambda x: x.get('name') or None,
            'hash_code': lambda x: x.get('hashCode'),
            'image': lambda x: x.get('profilePic') or None,
            'bio': lambda x: x.get('statusMessage') or None,
            'country': lambda x: x.get('nationality') or None,
            'occupation': lambda x: x.get('job') or None,
            'is_creator': lambda x: x.get('isCreator'),
            'follower_count': lambda x: x.get('followerCount'),
            'following_count': lambda x: x.get('followingCount'),
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?zepeto\.me/profile/(?P<username>[^/?#]+)',
            'to': 'https://gw-napi.zepeto.io/profiles/{username}',
        }],
    },
    'OnlyFans API': {
        'url_hints': ('onlyfans.com',),
        'flags': ['"isPerformer":', '"subscribersCount":', '"joinDate":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name'),
            'bio': lambda x: x.get('about'),
            'website': lambda x: x.get('website') or None,
            'location': lambda x: x.get('location') or None,
            'image': lambda x: x.get('avatar'),
            'image_bg': lambda x: x.get('header') or None,
            'created_at': lambda x: x.get('joinDate'),
            'latest_activity_at': lambda x: x.get('lastSeen') or None,
            'is_verified': lambda x: x.get('isVerified'),
            'is_performer': lambda x: x.get('isPerformer'),
            'is_adult_content': lambda x: x.get('isAdultContent'),
            'posts_count': lambda x: x.get('postsCount'),
            'photos_count': lambda x: x.get('photosCount'),
            'videos_count': lambda x: x.get('videosCount'),
            'follower_count': lambda x: x.get('subscribersCount'),
            'favorites_count': lambda x: x.get('favoritedCount'),
            'subscribe_price': lambda x: x.get('subscribePrice'),
        },
    },
    'eToro API': {
        'url_hints': ('etoro.com',),
        'flags': ['"gcid":', '"realCID":', '"allowDisplayFullName":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('gcid'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: ' '.join(filter(None, [x.get('firstName'), x.get('lastName')])) or None,
            'bio': lambda x: x.get('aboutMe') or None,
            'country': lambda x: x.get('country'),
            'language': lambda x: x.get('languageIsoCode'),
            'image': lambda x: next((a['url'] for a in x.get('avatars', []) if a.get('width') == 150), None),
            'is_verified': lambda x: x.get('isVerified'),
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?etoro\.com/people/(?P<username>[^/?#]+)',
            'to': 'https://www.etoro.com/api/logininfo/v1.1/users/{username}',
        }],
    },
    'Gettr API': {
        'url_hints': ('gettr.com',),
        'flags': ['"nickname":', '"flw":', '"dsc":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('result', {}).get('data', {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('_id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('nickname') or None,
            'bio': lambda x: x.get('dsc') or None,
            'website': lambda x: x.get('website') or None,
            'location': lambda x: x.get('location') or None,
            'language': lambda x: x.get('lang') or None,
            'image': lambda x: x.get('ico') or None,
            'image_bg': lambda x: x.get('bgimg') or None,
            'is_verified': lambda x: x.get('vrf'),
            'follower_count': lambda x: x.get('flw'),
            'created_at': lambda x: x.get('cdate'),
        },
        'url_mutations': [{
            'from': r'https?://gettr\.com/user/(?P<username>[^/?#]+)',
            'to': 'https://gettr.com/api/s/uinf/{username}',
        }],
    },
    'Habbo API': {
        'url_hints': ('habbo.com', 'habbo.de', 'habbo.fr', 'habbo.es',
                      'habbo.it', 'habbo.nl', 'habbo.fi', 'habbo.com.br',
                      'habbo.com.tr'),
        'flags': ['"uniqueId":', '"figureString":', '"memberSince":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('uniqueId'),
            'username': lambda x: x.get('name'),
            'bio': lambda x: x.get('motto') or None,
            'is_online': lambda x: x.get('online'),
            'created_at': lambda x: x.get('memberSince'),
            'latest_activity_at': lambda x: x.get('lastAccessTime') or None,
            'level': lambda x: x.get('currentLevel'),
            'experience': lambda x: x.get('totalExperience'),
            'is_profile_visible': lambda x: x.get('profileVisible'),
        },
        'url_mutations': [
            {'from': r'https?://www\.habbo\.com/profile/(?P<username>[^/?#]+)',
             'to': 'https://www.habbo.com/api/public/users?name={username}'},
            {'from': r'https?://www\.habbo\.de/profile/(?P<username>[^/?#]+)',
             'to': 'https://www.habbo.de/api/public/users?name={username}'},
            {'from': r'https?://www\.habbo\.fr/profile/(?P<username>[^/?#]+)',
             'to': 'https://www.habbo.fr/api/public/users?name={username}'},
            {'from': r'https?://www\.habbo\.es/profile/(?P<username>[^/?#]+)',
             'to': 'https://www.habbo.es/api/public/users?name={username}'},
            {'from': r'https?://www\.habbo\.it/profile/(?P<username>[^/?#]+)',
             'to': 'https://www.habbo.it/api/public/users?name={username}'},
            {'from': r'https?://www\.habbo\.nl/profile/(?P<username>[^/?#]+)',
             'to': 'https://www.habbo.nl/api/public/users?name={username}'},
            {'from': r'https?://www\.habbo\.fi/profile/(?P<username>[^/?#]+)',
             'to': 'https://www.habbo.fi/api/public/users?name={username}'},
            {'from': r'https?://www\.habbo\.com\.br/profile/(?P<username>[^/?#]+)',
             'to': 'https://www.habbo.com.br/api/public/users?name={username}'},
            {'from': r'https?://www\.habbo\.com\.tr/profile/(?P<username>[^/?#]+)',
             'to': 'https://www.habbo.com.tr/api/public/users?name={username}'},
        ],
    },
    'Hackadvisor API': {
        'url_hints': ('hackadvisor.io',),
        'flags': ['"crypto_wallet_address":', '"bb_platform":', '"accounts":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: ' '.join(filter(None, [x.get('first_name'), x.get('last_name')])) or None,
            'bio': lambda x: x.get('bio') or None,
            'crypto_wallet': lambda x: x.get('crypto_wallet_address') or None,
        },
        'url_mutations': [{
            'from': r'https?://hackadvisor\.io/hacker/(?P<username>[^/?#]+)',
            'to': 'https://hackadvisor.io/api/v2/profile/{username}/',
        }],
    },
    'Pillowfort JSON API': {
        'url_hints': ('pillowfort.social',),
        'flags': ['"posts":', '"rebloggable":', '"avatar_url":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('posts', [{}])[0] if isinstance(x.get('posts'), list) and x['posts'] else {},
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('user_id'),
            'username': lambda x: x.get('username'),
            'image': lambda x: x.get('avatar_url') or None,
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?pillowfort\.social/(?P<username>[^/?#]+)',
            'to': 'https://www.pillowfort.social/{username}/json/?p=1',
        }],
    },
    'Scored API': {
        'url_hints': ('scored.co',),
        'flags': ['"post_score":', '"comment_score":', '"moderates":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('users', [{}])[0] if isinstance(x.get('users'), list) and x['users'] else {},
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'image': lambda x: x.get('profile_picture') or None,
            'is_admin': lambda x: x.get('is_admin'),
            'post_score': lambda x: x.get('post_score'),
            'comment_score': lambda x: x.get('comment_score'),
            'created_at': lambda x: x.get('created'),
        },
        'url_mutations': [{
            'from': r'https?://scored\.co/u/(?P<username>[^/?#]+)',
            'to': 'https://scored.co/api/v2/user/about.json?user={username}',
        }],
    },
    'YesWeHack API': {
        'url_hints': ('yeswehack.com',),
        'flags': ['"hunter_profile":', '"nb_reports":', '"kyc_status":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: ' '.join(filter(None, [x.get('public_firstname'), x.get('public_lastname')])) or None,
            'image': lambda x: x.get('avatar') or None,
            'country': lambda x: x.get('nationality') or None,
            'website': lambda x: (x.get('hunter_profile') or {}).get('website_url') or None,
            'github_username': lambda x: (x.get('hunter_profile') or {}).get('github') or None,
            'twitter_username': lambda x: (x.get('hunter_profile') or {}).get('twitter') or None,
            'rank': lambda x: x.get('rank'),
            'reports_count': lambda x: x.get('nb_reports'),
            'points': lambda x: x.get('points'),
            'impact': lambda x: x.get('impact'),
            'created_at': lambda x: x.get('joined_on'),
        },
        'url_mutations': [{
            'from': r'https?://yeswehack\.com/hunters/(?P<username>[^/?#]+)',
            'to': 'https://api.yeswehack.com/hunters/{username}',
        }],
    },
    'Destream API': {
        'url_hints': ('destream.net',),
        'flags': ['"userName":', '"logoImageUrl":', '"liveStream":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('userName'),
            'image': lambda x: x.get('logoImageUrl') or None,
        },
        'url_mutations': [{
            'from': r'https?://destream\.net/live/(?P<username>[^/?#]+)',
            'to': 'https://api.destream.net/siteapi/v2/live/details/{username}',
        }],
    },
    'Tipeeestream API': {
        'url_hints': ('tipeeestream.com',),
        'flags': ['"tipper_number":', '"paymentMeans":', '"aclPage":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: (x.get('user') or {}).get('id'),
            'username': lambda x: x.get('slug'),
            'fullname': lambda x: (x.get('user') or {}).get('pseudo') or None,
            'image': lambda x: x.get('avatar') or None,
            'image_bg': lambda x: x.get('cover') or None,
            'language': lambda x: (x.get('user') or {}).get('userLanguage') or None,
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?tipeeestream\.com/(?P<username>[^/?#]+)',
            'to': 'https://www.tipeeestream.com/v3.0/pages/{username}',
        }],
    },
    'Komi API': {
        'url_hints': ('komi.io',),
        'flags': ['"accountStatus":', '"talentProfile":', '"hasBooking":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: (x.get('talentProfile') or {}).get('displayName') or None,
            'bio': lambda x: (x.get('talentProfile') or {}).get('bio') or None,
            'image': lambda x: x.get('avatar') or (x.get('talentProfile') or {}).get('avatar') or None,
            'website': lambda x: (x.get('talentProfile') or {}).get('website') or None,
            'instagram_username': lambda x: (x.get('talentProfile') or {}).get('instagram') or None,
            'youtube_channel': lambda x: (x.get('talentProfile') or {}).get('youtube') or None,
        },
        'url_mutations': [{
            'from': r'https?://(?P<username>[^./?#]+)\.komi\.io',
            'to': 'https://api.komi.io/api/talent/usernames/{username}',
        }],
    },
    'Cropty API': {
        'url_hints': ('cropty.io',),
        'flags': ['"ref_code":', '"ref_link":', '"nickname":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('data', {}),
            json.dumps,
        ],
        'fields': {
            'fullname': lambda x: x.get('name') or None,
            'username': lambda x: x.get('nickname'),
            'image': lambda x: x.get('image') or None,
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?cropty\.io/@(?P<username>[^/?#]+)',
            'to': 'https://api.cropty.io/v1/auth/{username}',
        }],
    },
    'Redgifs API': {
        'url_hints': ('redgifs.com',),
        'flags': ['"profileImageUrl":', '"publishedGifs":', '"creationtime":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('description') or None,
            'image': lambda x: x.get('profileImageUrl') or None,
            'website': lambda x: x.get('profileUrl') or None,
            'is_verified': lambda x: x.get('verified'),
            'follower_count': lambda x: x.get('followers'),
            'following_count': lambda x: x.get('following'),
            'views_count': lambda x: x.get('views'),
            'likes_count': lambda x: x.get('likes'),
            'gifs_count': lambda x: x.get('gifs'),
            'created_at': lambda x: x.get('creationtime'),
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?redgifs\.com/users/(?P<username>[^/?#]+)',
            'to': 'https://api.redgifs.com/v1/users/{username}',
        }],
    },
    'Tappy API': {
        'url_hints': ('tappy.tech',),
        'flags': ['"header_logo":', '"social_order":', '"accent_color":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('user_id'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('bio') or None,
            'image': lambda x: x.get('photo') or None,
            'image_bg': lambda x: x.get('banner_image') or x.get('header_logo') or None,
            'created_at': lambda x: x.get('created_at'),
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?tappy\.tech/(?P<username>[^/?#]+)',
            'to': 'https://api.tappy.tech/api/profile/username/{username}',
        }],
    },
    'Komoot API': {
        'url_hints': ('komoot.com', 'komoot.de'),
        'flags': ['"display_name":', '"_links":', 'komoot'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('display_name') or None,
            'image': lambda x: (x.get('avatar') or {}).get('src') if isinstance(x.get('avatar'), dict) else None,
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?komoot\.com/user/(?P<username>[^/?#]+)',
            'to': 'https://api.komoot.de/v007/users/{username}/',
        }],
    },
    'Tapitag API': {
        'url_hints': ('tapitag.co',),
        'flags': ['"profileDetail":', '"rfnumber":', '"privacystatus":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: (x.get('data') or {}).get('profileDetail', {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('uuid') or x.get('id'),
            'username': lambda x: x.get('rfnumber'),
            'fullname': lambda x: ' '.join(filter(None, [x.get('first_name'), x.get('last_name')])) or None,
            'email': lambda x: x.get('email') or None,
            'bio': lambda x: x.get('bio') or None,
            'image': lambda x: x.get('image') or None,
            'image_bg': lambda x: x.get('bannerimage') or None,
        },
        'url_mutations': [{
            'from': r'https?://account\.tapitag\.co/(?P<username>[^/?#]+)',
            'to': 'https://account.tapitag.co/tapitag/api/v1/{username}',
        }],
    },
    'Vivino API': {
        'url_hints': ('vivino.com',),
        'flags': ['"seo_name":', '"is_featured":', '"statistics":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('seo_name'),
            'fullname': lambda x: x.get('alias') or None,
            'bio': lambda x: x.get('bio') or None,
            'website': lambda x: x.get('website') or None,
            'image': lambda x: x.get('image', {}).get('location') or None,
            'image_bg': lambda x: x.get('background_image', {}).get('location') or None,
            'language': lambda x: x.get('language') or None,
            'country': lambda x: (x.get('address') or {}).get('country') or None,
            'is_premium': lambda x: x.get('is_premium'),
            'follower_count': lambda x: (x.get('statistics') or {}).get('followers_count'),
            'following_count': lambda x: (x.get('statistics') or {}).get('followings_count'),
            'ratings_count': lambda x: (x.get('statistics') or {}).get('ratings_count'),
            'reviews_count': lambda x: (x.get('statistics') or {}).get('reviews_count'),
            'wishlist_count': lambda x: (x.get('statistics') or {}).get('wishlist_count'),
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?vivino\.com/users/(?P<username>[^/?#]+)',
            'to': 'https://api.vivino.com/users/{username}',
        }],
    },
    'Google Scholar': {
        'url_hints': ('scholar.google.com', 'scholar.google.ru'),
        'flags': ['gsc_prf_in', 'gsc_prf_il', 'gsc_rsb_st'],
        'bs': True,
        'fields': {
            'fullname': lambda x: x.find(id='gsc_prf_in').text if x.find(id='gsc_prf_in') else None,
            'bio': lambda x: x.find('div', class_='gsc_prf_il').text if x.find('div', class_='gsc_prf_il') else None,
            'image': lambda x: x.find(id='gsc_prf_pup-img')['src'] if x.find(id='gsc_prf_pup-img') else None,
            'website': lambda x: x.find(id='gsc_prf_ivh').find('a')['href'] if x.find(id='gsc_prf_ivh') and x.find(id='gsc_prf_ivh').find('a') else None,
            'interests': lambda x: ', '.join(a.text for a in x.find_all('a', class_='gsc_prf_inta')) or None,
        },
    },
    'Snapchat profile': {
        'url_hints': ('snapchat.com',),
        'flags': ['__NEXT_DATA__', '"snapcodeImageUrl":', '"publicProfileInfo":'],
        'regex': r'id="__NEXT_DATA__"[^>]*>([\s\S]+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('props', {}).get('pageProps', {}).get('userProfile', {}).get('publicProfileInfo', {}),
            json.dumps,
        ],
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('title') or None,
            'bio': lambda x: x.get('bio') or None,
            'image': lambda x: x.get('profilePictureUrl') or None,
            'website': lambda x: x.get('websiteUrl') or None,
            'snapcode_url': lambda x: x.get('snapcodeImageUrl') or None,
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?snapchat\.com/add/(?P<username>[^/?#]+)',
            'to': 'https://www.snapchat.com/add/{username}',
        }],
    },
    'Flipboard profile': {
        'url_hints': ('flipboard.com',),
        'flags': ['__PRELOADED_STATE__', 'authorDisplayName', 'authorUsername'],
        'regex': r'__PRELOADED_STATE__\s*=\s*(\{.*?\});\s*</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('sections', {}).get('entries', [{}])[0] if isinstance(x.get('sections', {}).get('entries'), list) and x['sections']['entries'] else {},
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('userid'),
            'username': lambda x: x.get('authorUsername'),
            'fullname': lambda x: x.get('authorDisplayName') or None,
            'bio': lambda x: x.get('authorDescription') or None,
            'image': lambda x: (x.get('authorImage') or {}).get('smallURL') or None,
            'is_verified': lambda x: x.get('isVerifiedPublisher'),
            'mastodon_url': lambda x: x.get('mastodonProfile') or None,
            'follower_count': lambda x: (x.get('metrics') or {}).get('follower'),
            'following_count': lambda x: (x.get('metrics') or {}).get('follow'),
            'articles_count': lambda x: (x.get('metrics') or {}).get('articles'),
            'magazines_count': lambda x: (x.get('metrics') or {}).get('magazineCount'),
        },
    },
    'Clubhouse profile': {
        'url_hints': ('clubhouse.com',),
        'flags': ['__NEXT_DATA__', '"num_followers":', '"user_profile_type":'],
        'regex': r'id="__NEXT_DATA__"[^>]*>([\s\S]+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('props', {}).get('pageProps', {}).get('routeProps', {}),
            json.dumps,
        ],
        'fields': {
            'username': lambda x: (x.get('user') or {}).get('username'),
            'fullname': lambda x: (x.get('user') or {}).get('full_name') or None,
            'bio': lambda x: (x.get('user') or {}).get('bio') or None,
            'image': lambda x: (x.get('user') or {}).get('photo_url') or None,
            'twitter_username': lambda x: (x.get('user') or {}).get('twitter_username') or None,
            'instagram_username': lambda x: (x.get('user') or {}).get('instagram_username') or None,
            'follower_count': lambda x: x.get('num_followers'),
            'following_count': lambda x: x.get('num_following'),
        },
    },
    'Coda.io profile': {
        'url_hints': ('coda.io',),
        'flags': ['application/ld+json', '"Person"', 'coda.io/@'],
        'regex': r'<script[^>]*application/ld\+json[^>]*>\s*(\{[^<]+\})\s*</script>',
        'extract_json': True,
        'fields': {
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('description') or None,
            'image': lambda x: x.get('image') or None,
            'occupation': lambda x: x.get('jobTitle') or None,
            'company': lambda x: (x.get('worksFor') or {}).get('name') or None,
            'website': lambda x: x.get('url') or None,
        },
    },
    'Poe.com profile': {
        'url_hints': ('poe.com',),
        'flags': ['__NEXT_DATA__', '"followerCount":', '"createdBotCount":'],
        'regex': r'id="__NEXT_DATA__"[^>]*>([\s\S]+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('props', {}).get('pageProps', {}).get('data', {}).get('mainQuery', {}).get('user', {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('uid'),
            'username': lambda x: x.get('handle'),
            'fullname': lambda x: x.get('fullName') or None,
            'bio': lambda x: x.get('bio') or None,
            'image': lambda x: x.get('largeProfilePhotoUrl') or x.get('profilePhotoUrl') or None,
            'follower_count': lambda x: x.get('followerCount'),
            'following_count': lambda x: x.get('followeeCount'),
            'bots_count': lambda x: x.get('createdBotCount'),
        },
    },
    'Gumroad profile': {
        'url_hints': ('gumroad.com',),
        'flags': ['data-page=', 'creator_profile', 'Gumroad'],
        'regex': r'data-page="([^"]+)"',
        'extract_json': True,
        'transforms': [
            html.unescape,
            json.loads,
            lambda x: x.get('props', {}).get('creator_profile', {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('external_id'),
            'fullname': lambda x: x.get('name') or None,
            'image': lambda x: x.get('avatar_url') or None,
            'is_verified': lambda x: x.get('is_verified'),
        },
    },
    'Mastodon HTML profile': {
        'flags': ['id="mastodon"', 'profile:username', 'initial-state'],
        'bs': True,
        'fields': {
            'username': lambda x: x.find('meta', {'property': 'profile:username'})['content'].split('@')[0] if x.find('meta', {'property': 'profile:username'}) else None,
            'fullname': lambda x: (lambda t: t['content'].split(' (@')[0] if ' (@' in t.get('content', '') else t['content'])(x.find('meta', {'property': 'og:title'})) if x.find('meta', {'property': 'og:title'}) else None,
            'bio': lambda x: x.find('meta', {'property': 'og:description'})['content'] if x.find('meta', {'property': 'og:description'}) else None,
            'image': lambda x: x.find('meta', {'property': 'og:image'})['content'] if x.find('meta', {'property': 'og:image'}) else None,
            'mastodon_id': lambda x: x.find('meta', {'property': 'profile:username'})['content'] if x.find('meta', {'property': 'profile:username'}) else None,
        },
    },
    'Discourse HTML profile': {
        'flags': ['data-preloaded=', 'discourse_theme_id', 'discourse_current_homepage'],
        'bs': True,
        'fields': {
            'uid': lambda x: _discourse_user_field(x, 'id'),
            'username': lambda x: _discourse_user_field(x, 'username'),
            'fullname': lambda x: _discourse_user_field(x, 'name') or None,
            'title': lambda x: _discourse_user_field(x, 'title') or None,
            'website': lambda x: _discourse_user_field(x, 'website') or None,
            'image': lambda x: (_discourse_user_field(x, 'avatar_template') or '').replace('{size}', '240') or None,
            'trust_level': lambda x: _discourse_user_field(x, 'trust_level'),
            'is_moderator': lambda x: _discourse_user_field(x, 'moderator'),
            'is_admin': lambda x: _discourse_user_field(x, 'admin'),
            'badge_count': lambda x: _discourse_user_field(x, 'badge_count'),
            'views_count': lambda x: _discourse_user_field(x, 'profile_view_count'),
            'created_at': lambda x: _discourse_user_field(x, 'created_at'),
            'latest_activity_at': lambda x: _discourse_user_field(x, 'last_seen_at'),
        },
        'url_mutations': [{
            'from': r'https?://(?P<domain>[^/]+)/u/(?P<username>[^/?#.]+)/summary',
            'to': 'https://{domain}/u/{username}',
        }],
    },
    'Mastodon API': {
        'url_hints': tuple(_MASTODON_INSTANCES),
        'flags': ['"followers_count":', '"avatar_static":', '"header_static":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('display_name') or None,
            'bio': lambda x: x.get('note') or None,
            'image': lambda x: x.get('avatar') if x.get('avatar') and '/missing.' not in x.get('avatar', '') else None,
            'image_bg': lambda x: x.get('header') if x.get('header') and '/missing.' not in x.get('header', '') else None,
            'is_locked': lambda x: x.get('locked'),
            'is_bot': lambda x: x.get('bot'),
            'follower_count': lambda x: x.get('followers_count'),
            'following_count': lambda x: x.get('following_count'),
            'posts_count': lambda x: x.get('statuses_count'),
            'created_at': lambda x: x.get('created_at'),
            'latest_activity_at': lambda x: x.get('last_status_at') or None,
        },
        'url_mutations': [
            {
                'from': r'https?://' + d.replace('.', r'\.') + r'/@(?P<username>[^/?#]+)',
                'to': 'https://' + d + '/api/v1/accounts/lookup?acct={username}',
            }
            for d in _MASTODON_INSTANCES
        ],
    },
    'Discourse Forums': {
        'url_hints': tuple(_DISCOURSE_INSTANCES),
        'flags': ['"trust_level"', '"badge_count"', '"profile_view_count"'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('user', {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name') or None,
            'title': lambda x: x.get('title') or None,
            'bio': lambda x: x.get('bio_raw') or None,
            'website': lambda x: x.get('website') or None,
            'location': lambda x: x.get('location') or None,
            'image': lambda x: x.get('avatar_template', '').replace('{size}', '240') or None,
            'trust_level': lambda x: x.get('trust_level'),
            'is_moderator': lambda x: x.get('moderator'),
            'is_admin': lambda x: x.get('admin'),
            'badge_count': lambda x: x.get('badge_count'),
            'views_count': lambda x: x.get('profile_view_count'),
            'created_at': lambda x: x.get('created_at'),
            'latest_activity_at': lambda x: x.get('last_seen_at'),
        },
        'url_mutations': [
            {
                'from': r'https?://' + d.replace('.', r'\.') + r'/u/(?P<username>[^/?#.]+)',
                'to': 'https://' + d + '/u/{username}.json',
            }
            for d in _DISCOURSE_INSTANCES
        ],
    },
    'FL.ru': {
        'url_hints': ('fl.ru',),
        'flags': ['application/ld+json', '"ProfilePage"', 'fl.ru'],
        'bs': True,
        'fields': {
            'uid': lambda x: (lambda m: m.group(1) if m else None)(re.search(r'ID:(\d+)', x.title.text if x.title else '')),
            'username': lambda x: (lambda m: m.group(1) if m else None)(re.search(r'/users/([^/]+)/', _fl_ld(x, 'mainEntity', 'url') or '')),
            'fullname': lambda x: _fl_ld(x, 'mainEntity', 'name'),
            'occupation': lambda x: _fl_ld(x, 'mainEntity', 'jobTitle'),
            'image': lambda x: _fl_ld(x, 'mainEntity', 'image'),
            'created_at': lambda x: _fl_ld(x, 'dateCreated'),
        },
    },
    'Manifold Markets': {
        'url_hints': ('manifold.markets',),
        'flags': ['__NEXT_DATA__', '"creatorTraders":', '"followerCountCached":'],
        'regex': r'id="__NEXT_DATA__"[^>]*>([\s\S]+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: {**x.get('props', {}).get('pageProps', {}).get('user', {}),
                        '_rating': x.get('props', {}).get('pageProps', {}).get('rating'),
                        '_reviewCount': x.get('props', {}).get('pageProps', {}).get('reviewCount')},
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('bio') or None,
            'image': lambda x: x.get('avatarUrl') or None,
            'website': lambda x: x.get('website') or None,
            'twitter_username': lambda x: x.get('twitterHandle') or None,
            'discord_username': lambda x: x.get('discordHandle') or None,
            'is_bot': lambda x: x.get('isBot'),
            'is_verified': lambda x: x.get('idVerified'),
            'follower_count': lambda x: x.get('followerCountCached'),
            'created_at': lambda x: x.get('createdTime'),
            'rating': lambda x: x.get('_rating'),
            'review_count': lambda x: x.get('_reviewCount'),
        },
    },
    'VSCO': {
        'url_hints': ('vsco.co',),
        'flags': ['__PRELOADED_STATE__', 'vsco.co', '"profileImage"'],
        'regex': r'__PRELOADED_STATE__\s*=\s*(\{[\s\S]+\})\s*;?\s*</script>',
        'extract_json': True,
        'transforms': [
            lambda x: x.replace('undefined', 'null'),
            json.loads,
            lambda x: next((v.get('site', {}) for v in (x.get('sites', {}).get('siteByUsername', {}) or {}).values() if isinstance(v, dict) and 'site' in v), {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id') or x.get('userId'),
            'username': lambda x: x.get('subdomain'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('description') or None,
            'image': lambda x: x.get('profileImage') or None,
            'website': lambda x: (x.get('links', {}) or {}).get('personalUrl') or x.get('externalLink') or None,
        },
    },
    'Mojang API': {
        'url_hints': ('api.mojang.com',),
        'flags': ['"id" :', '"name" :'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('name'),
        },
    },
    'OP.GG': {
        'url_hints': ('op.gg',),
        'flags': ['op.gg/lol/summoners/', 'game_name'],
        'regex': r'\\"game_name\\":\\"(?P<username>[^\\]+)\\",\\"tagline\\":\\"(?P<opgg_tagline>[^\\]+)\\",\\"name\\":\\"(?P<opgg_summoner_name>[^\\]*)\\",\\"internal_name\\":\\"[^\\]*\\",\\"profile_image_url\\":\\"(?P<image>[^\\]+)\\",\\"level\\":(?P<opgg_level>\d+)',
        'fields': {},
    },
    'coder.social': {
        'url_hints': ('coder.social',),
        'flags': ['Coder Social</title>', 'og:site_name'],
        'bs': True,
        'fields': {
            'username': lambda x: (lambda t: t.split('|')[0].strip() if t else None)(x.title.text if x.title else None),
            'fullname': lambda x: (lambda m: m['content'].split(',')[1].strip() if ',' in m.get('content', '') else None)(x.find('meta', {'name': 'keywords'}) or {}) if x.find('meta', {'name': 'keywords'}) else None,
            'image': lambda x: (lambda i: i['src'] if i else None)(x.find('img', src=re.compile(r'avatars\.githubusercontent\.com'))),
            'location': lambda x: (lambda d: d.split('.')[-2].strip() if d and '.' in d else None)(x.find('meta', {'name': 'description'}).get('content', '') if x.find('meta', {'name': 'description'}) else None),
        },
    },
    'osu!': {
        'url_hints': ('osu.ppy.sh',),
        'flags': ['data-initial-data=', 'osu-layout', 'play_count'],
        'bs': True,
        'fields': {
            'uid': lambda x: _osu_field(x, 'id'),
            'username': lambda x: _osu_field(x, 'username'),
            'image': lambda x: _osu_field(x, 'avatar_url'),
            'country': lambda x: (_osu_field(x, 'country') or {}).get('name') if isinstance(_osu_field(x, 'country'), dict) else None,
            'country_code': lambda x: _osu_field(x, 'country_code'),
            'title': lambda x: _osu_field(x, 'title') or None,
            'occupation': lambda x: _osu_field(x, 'occupation') or None,
            'interests': lambda x: _osu_field(x, 'interests') or None,
            'website': lambda x: _osu_field(x, 'website') or None,
            'twitter_username': lambda x: _osu_field(x, 'twitter') or None,
            'discord_username': lambda x: _osu_field(x, 'discord') or None,
            'is_bot': lambda x: _osu_field(x, 'is_bot'),
            'is_active': lambda x: _osu_field(x, 'is_active'),
            'is_deleted': lambda x: _osu_field(x, 'is_deleted'),
            'is_supporter': lambda x: _osu_field(x, 'is_supporter'),
            'follower_count': lambda x: _osu_field(x, 'follower_count'),
            'posts_count': lambda x: _osu_field(x, 'post_count'),
            'created_at': lambda x: _osu_field(x, 'join_date'),
            'osu_pp': lambda x: (_osu_field(x, 'statistics') or {}).get('pp'),
            'osu_global_rank': lambda x: (_osu_field(x, 'statistics') or {}).get('global_rank'),
            'osu_country_rank': lambda x: (_osu_field(x, 'statistics') or {}).get('country_rank'),
            'osu_play_count': lambda x: (_osu_field(x, 'statistics') or {}).get('play_count'),
            'osu_hit_accuracy': lambda x: (_osu_field(x, 'statistics') or {}).get('hit_accuracy'),
            'previous_usernames': lambda x: ', '.join(_osu_field(x, 'previous_usernames') or []) or None,
        },
    },
    'GOG': {
        'url_hints': ('gog.com',),
        'flags': ['profilesData.profileUser', '"games_owned"'],
        'regex': r'profilesData\.profileUser\s*=\s*(\{[^;]+\})\s*;',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('userId'),
            'username': lambda x: x.get('username'),
            'image': lambda x: x.get('avatar') or None,
            'created_at': lambda x: x.get('created_date'),
            'gog_games_owned': lambda x: (x.get('stats') or {}).get('games_owned'),
            'gog_achievements': lambda x: (x.get('stats') or {}).get('achievements'),
            'gog_hours_played': lambda x: (x.get('stats') or {}).get('hours_played'),
        },
    },
    'Kick API': {
        'url_hints': ('kick.com',),
        'flags': ['"followers_count":', '"subscriber_badges":', '"playback_url":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('user', {}).get('id'),
            'username': lambda x: x.get('user', {}).get('username'),
            'bio': lambda x: x.get('user', {}).get('bio') or None,
            'image': lambda x: x.get('user', {}).get('profile_pic') or None,
            'image_bg': lambda x: (x.get('banner_image') or {}).get('url') or None,
            'is_verified': lambda x: x.get('verified'),
            'is_banned': lambda x: x.get('is_banned'),
            'follower_count': lambda x: x.get('followers_count'),
            'instagram_username': lambda x: x.get('user', {}).get('instagram').rstrip('/').rsplit('/', 1)[-1] if x.get('user', {}).get('instagram') else None,
            'twitter_username': lambda x: x.get('user', {}).get('twitter') or None,
            'youtube_channel_id': lambda x: x.get('user', {}).get('youtube').split('/')[-1] if x.get('user', {}).get('youtube') else None,
            'discord_username': lambda x: x.get('user', {}).get('discord') or None,
            'tiktok_username': lambda x: x.get('user', {}).get('tiktok') or None,
            'facebook_username': lambda x: x.get('user', {}).get('facebook') or None,
            'created_at': lambda x: x.get('user', {}).get('email_verified_at'),
        },
    },
    'Academia.edu': {
        'url_hints': ('academia.edu',),
        'flags': ['Aedu.User.set_viewed(', 'academia.edu'],
        'regex': r'Aedu\.User\.set_viewed\(\s*(\{[^)]+\})\s*\)',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('page_name'),
            'fullname': lambda x: x.get('display_name') or None,
            'image': lambda x: x.get('photo') if x.get('has_photo') else None,
            'created_at': lambda x: x.get('created_at'),
        },
    },
    'TradingView': {
        'url_hints': ('tradingview.com',),
        'flags': ['"ssrData":', '"date_joined":', 'tradingview.com/u/'],
        'regex': r'"ssrData"\s*:\s*(\{.+?"paid_space":[^}]*\})',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('username'),
            'bio': lambda x: x.get('bio') or None,
            'image': lambda x: x.get('picture_url_orig') or None,
            'website': lambda x: (x.get('social_links') or {}).get('website') or None,
            'twitter_username': lambda x: (x.get('social_links') or {}).get('twitter_username') or None,
            'instagram_username': lambda x: (x.get('social_links') or {}).get('instagram_username') or None,
            'facebook_username': lambda x: (x.get('social_links') or {}).get('facebook_username') or None,
            'follower_count': lambda x: (x.get('statistics') or {}).get('followers'),
            'following_count': lambda x: (x.get('statistics') or {}).get('following'),
            'created_at': lambda x: parse_datetime(int(x['date_joined'])) if x.get('date_joined') else None,
            'latest_activity_at': lambda x: parse_datetime(int(x['last_login'])) if x.get('last_login') else None,
        },
    },
    'Geocaching': {
        'url_hints': ('geocaching.com',),
        'flags': ['geocaching.com', 'ProfileHeader_lblMemberName'],
        'bs': True,
        'fields': {
            'username': lambda x: (lambda t: t.text.strip() if t else None)(x.find(id=re.compile(r'lblMemberName'))),
            'uid': lambda x: (lambda m: m.group(1) if m else None)(re.search(r'guid=([a-f0-9-]+)', str(x))),
            'image': lambda x: (lambda t: t['src'] if t and '/default_avatar' not in t.get('src', '') else None)(x.find(id=re.compile(r'uxProfilePhoto'))),
        },
    },
    'Rutracker': {
        'url_hints': ('rutracker.org', 'rutracker.net'),
        'flags': ['rutracker', 'avatar-img'],
        'bs': True,
        'fields': {
            'uid': lambda x: (lambda m: m.group(1) if m else None)(re.search(r'privmsg\.php\?mode=post&(?:amp;)?u=(\d+)', str(x))),
            'username': lambda x: x.title.text.strip() if x.title else None,
            'image': lambda x: (lambda t: t.find('img')['src'] if t and t.find('img') else None)(x.find(id='avatar-img')),
            'created_at': lambda x: (lambda m: m.group(1) if m else None)(re.search(r'Зарегистрирован.*?<b[^>]*>(\d{4}-\d{2}-\d{2})', str(x), re.DOTALL)),
            'posts_count': lambda x: (lambda m: m.group(1).replace(',', '') if m else None)(re.search(r'Сообщения.*?<b>([\d,]+)</b>', str(x), re.DOTALL)),
        },
    },
    'Weburg': {
        'url_hints': ('weburg.net',),
        'flags': ['search-item_type_persons', 'weburg.me/user/'],
        'bs': True,
        'fields': {
            'uid': lambda x: (lambda a: re.search(r'/user/(\d+)', a['href']).group(1) if a and re.search(r'/user/(\d+)', a.get('href', '')) else None)(x.find('a', class_='search-item-heading-link')),
            'username': lambda x: (lambda a: a.text.strip() if a else None)(x.find('a', class_='search-item-heading-link')),
            'image': lambda x: (lambda i: i['src'] if i else None)(x.find('img', class_='search-item-image')),
        },
    },
    'Pokemon Showdown': {
        'url_hints': ('pokemonshowdown.com',),
        'flags': ['pokemonshowdown.com', 'Joined:'],
        'regex': r'<h1>(?P<fullname>[^<]+)</h1>[\s\S]*?<em>Joined:</em>\s*(?P<created_at>[^<]+)</small>',
        'fields': {},
    },
    'ImageShack': {
        'url_hints': ('imageshack.com',),
        'flags': ['IS.start(', 'bootstrapped'],
        'regex': r'photosTotal:\s*"(?P<photos_count>\d+)",\s*username:\s*"(?P<username>[^"]+)"',
        'fields': {},
    },
    'Replit': {
        'url_hints': ('replit.com',),
        'flags': ['__NEXT_DATA__', 'apolloState', '"User:'],
        'regex': r'id="__NEXT_DATA__"[^>]*>([\s\S]+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: next((v for k, v in x.get('props', {}).get('apolloState', {}).items() if k.startswith('User:')), {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('fullName') or None,
            'bio': lambda x: x.get('bio') or None,
            'image': lambda x: x.get('image') or None,
            'location': lambda x: x.get('location') or None,
        },
    },
    'Itch.io': {
        'url_hints': ('itch.io',),
        'flags': ['itch:path', 'itch.io'],
        'bs': True,
        'fields': {
            'uid': lambda x: (lambda m: m['content'].split('/')[-1] if m else None)(x.find('meta', {'name': 'itch:path'})),
            'fullname': lambda x: (lambda t: t['content'] if t else None)(x.find('meta', {'property': 'og:title'})),
            'created_at': lambda x: (lambda a: a['title'] if a else None)(x.find('abbr')),
        },
    },
    'Giphy': {
        'url_hints': ('giphy.com',),
        'flags': ['giphy.com/channel', 'avatar_url'],
        'regex': r'\\"display_name\\":\\"(?P<fullname>[^\\]*)\\",\\"about_bio\\":\\"(?P<bio>[^\\]*)\\",\\"avatar\\":\\"(?P<image>[^\\]+)\\"[\s\S]*?\\"is_verified\\":(?P<is_verified>true|false)[\s\S]*?\\"twitter\\":\\"(?P<twitter_username>[^\\]*)\\",\\"instagram\\":\\"(?P<instagram_username>[^\\]*)\\",\\"facebook\\":\\"(?P<facebook_username>[^\\]*)\\",\\"tiktok\\":\\"(?P<tiktok_username>[^\\]*)\\",\\"youtube\\":\\"(?P<youtube_username>[^\\]*)\\",\\"website_url\\":(?:\\"(?P<website>[^\\]*)\\"|null)',
        'fields': {},
    },
    'Wattpad HTML profile': {
        'url_hints': ('wattpad.com',),
        'flags': ['wattpad.com/user/', '"allowCrawler"', '"numStoriesPublished"'],
        'regex': r'"user\.[^"]+":\{"data":\[(\{[\s\S]+?"lastName":"[^"]*"\})\]',
        'extract_json': True,
        'fields': {
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('description') or None,
            'image': lambda x: x.get('avatar') or None,
            'image_bg': lambda x: x.get('backgroundUrl') or None,
            'gender': lambda x: x.get('gender') or None,
            'location': lambda x: x.get('location') or None,
            'website': lambda x: x.get('website') or None,
            'is_verified': lambda x: x.get('verified'),
            'is_private': lambda x: x.get('isPrivate'),
            'follower_count': lambda x: x.get('numFollowers'),
            'following_count': lambda x: x.get('numFollowing'),
            'posts_count': lambda x: x.get('numStoriesPublished'),
            'created_at': lambda x: x.get('createDate'),
            'facebook_username': lambda x: x.get('facebook') or None,
        },
    },
    'Venmo': {
        'url_hints': ('venmo.com',),
        'flags': ['__NEXT_DATA__', '"friendCount":', '"initials":'],
        'regex': r'id="__NEXT_DATA__"[^>]*>([\s\S]+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('props', {}).get('pageProps', {}).get('user', {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('displayName') or None,
            'image': lambda x: x.get('profilePictureUrl') or None,
            'friends_count': lambda x: x.get('friendCount'),
            'is_active': lambda x: x.get('isActive'),
        },
    },
    'Tumblr blog': {
        'url_hints': ('tumblr.com',),
        'flags': ['___INITIAL_STATE___', '"blog-info"', '"uuid":"t:'],
        'regex': r'id="___INITIAL_STATE___"[^>]*>\s*([\s\S]+?)\s*</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: {
                **next((q.get('state', {}).get('data', {}) for q in x.get('queries', {}).get('queries', []) if 'blog-info' in str(q.get('queryKey', []))), {}),
                '_latest_post_ts': (x.get('PeeprRoute', {}).get('initialTimeline', {}).get('objects', [{}]) or [{}])[0].get('timestamp'),
                '_visible_posts': len(x.get('PeeprRoute', {}).get('initialTimeline', {}).get('objects', []) or []),
            },
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('uuid'),
            'username': lambda x: x.get('name'),
            'fullname': lambda x: x.get('title') or None,
            'website': lambda x: x.get('url') or None,
            'image': lambda x: next((a['url'] for a in x.get('avatar', []) if a.get('width') == 512), None) or (x.get('avatar', [{}])[0].get('url') if x.get('avatar') else None),
            'image_bg': lambda x: (x.get('theme') or {}).get('headerImage') or None,
            'is_adult': lambda x: x.get('isAdult'),
            'created_at': lambda x: parse_datetime(int(x['created'])) if x.get('created') else None,
            'latest_activity_at': lambda x: parse_datetime(int(x['_latest_post_ts'])) if x.get('_latest_post_ts') else None,
            'last_posts_count': lambda x: x.get('_visible_posts'),
        },
    },
    'Drive2.ru': {
        'url_hints': ('drive2.ru',),
        'flags': ['drive2.ru', 'data-ihc-token', 'c-username'],
        'bs': True,
        'fields': {
            'uid': lambda x: (lambda m: m.group(1) if m else None)(re.search(r'data-ihc-token="p/(\d+)"', str(x))),
            'username': lambda x: (lambda l: l['href'].rstrip('/').rsplit('/', 1)[-1] if l and '/users/' in l.get('href', '') else None)(x.find('link', rel='canonical')),
            'fullname': lambda x: (lambda m: m['content'].split(',', 1)[1].rsplit('—', 1)[0].strip() if m and ',' in m.get('content', '') else None)(x.find('meta', {'property': 'yandex_recommendations_title'})),
            'bio': lambda x: (lambda m: m['content'] if m else None)(x.find('meta', {'name': 'description'})),
            'image': lambda x: (lambda m: m['content'] if m else None)(x.find('meta', {'property': 'og:image'})),
            'location': lambda x: (lambda m: m['title'] if m else None)(x.find('span', title=re.compile(r'.+,.+'))),
        },
    },
    'Lichess API': {
        'url_hints': ('lichess.org',),
        'flags': ['"perfs":', '"playTime":', '"createdAt":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('profile', {}).get('realName') or None,
            'bio': lambda x: x.get('profile', {}).get('bio') or None,
            'country_code': lambda x: x.get('profile', {}).get('flag') or None,
            'location': lambda x: x.get('profile', {}).get('location') or None,
            'is_verified': lambda x: x.get('verified'),
            'lichess_is_patron': lambda x: x.get('patron'),
            'lichess_is_tos_violation': lambda x: x.get('tosViolation'),
            'created_at': lambda x: x.get('createdAt'),
            'latest_activity_at': lambda x: x.get('seenAt'),
            'play_time_seconds': lambda x: x.get('playTime', {}).get('total'),
            'games_count': lambda x: x.get('count', {}).get('all'),
            'wins_count': lambda x: x.get('count', {}).get('win'),
            'losses_count': lambda x: x.get('count', {}).get('loss'),
            'draws_count': lambda x: x.get('count', {}).get('draw'),
            'links': lambda x: x.get('profile', {}).get('links') or None,
            'twitch_username': lambda x: ((x.get('streamer', {}).get('twitch', {}) or {}).get('channel') or '').rstrip('/').rsplit('/', 1)[-1] or None,
        },
        'url_mutations': [{
            'from': r'https?://lichess\.org/@/(?P<username>[^/?#]+)',
            'to': 'https://lichess.org/api/user/{username}',
        }],
    },
    'Hackerrank API': {
        'url_hints': ('hackerrank.com',),
        'flags': ['"model":', '"username":', '"followers_count":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x['model'],
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('short_bio') or None,
            'country': lambda x: x.get('country') or None,
            'image': lambda x: x.get('avatar') or None,
            'website': lambda x: x.get('website') or None,
            'company': lambda x: x.get('company') or None,
            'occupation': lambda x: x.get('job_title') or None,
            'school': lambda x: x.get('school') or None,
            'created_at': lambda x: x.get('created_at'),
            'follower_count': lambda x: x.get('followers_count'),
            'is_admin': lambda x: x.get('is_admin'),
            'is_deleted': lambda x: x.get('deleted'),
            'linkedin_username': lambda x: (x.get('linkedin_url') or '').rstrip('/').rsplit('/', 1)[-1] or None,
            'github_username': lambda x: (x.get('github_url') or '').rstrip('/').rsplit('/', 1)[-1] or None,
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?hackerrank\.com/(?:profile/)?(?P<username>[^/?#]+)',
            'to': 'https://www.hackerrank.com/rest/contests/master/hackers/{username}/profile',
        }],
    },
    'Kongregate API': {
        'url_hints': ('kongregate.com',),
        'flags': ['"user_data":', '"profile_data":', '"badge_count":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('user_data', {}).get('id'),
            'username': lambda x: x.get('user_data', {}).get('username'),
            'image': lambda x: x.get('user_data', {}).get('avatar_url') or None,
            'level': lambda x: x.get('user_data', {}).get('level'),
            'points': lambda x: x.get('user_data', {}).get('points'),
            'is_developer': lambda x: x.get('user_data', {}).get('developer'),
            'is_moderator': lambda x: x.get('user_data', {}).get('moderator'),
            'is_admin': lambda x: x.get('user_data', {}).get('admin'),
            'is_premium': lambda x: x.get('user_data', {}).get('premium'),
            'is_banned': lambda x: x.get('user_data', {}).get('banned'),
            'facebook_uid': lambda x: x.get('user_data', {}).get('facebook_uid'),
            'bio': lambda x: x.get('profile_data', {}).get('about') or None,
            'location': lambda x: x.get('profile_data', {}).get('location') or None,
            'created_at': lambda x: x.get('profile_data', {}).get('created_at'),
            'friends_count': lambda x: x.get('profile_data', {}).get('friend_count'),
            'badge_count': lambda x: x.get('profile_data', {}).get('badge_count'),
            'comments_count': lambda x: x.get('profile_data', {}).get('comment_count'),
        },
        'url_mutations': [{
            'from': r'https?://(?:www\.)?kongregate\.com/accounts/(?P<username>[^/?#.]+)',
            'to': 'https://www.kongregate.com/accounts/{username}.json',
        }],
    },
    'WordPress.com site API': {
        'url_hints': ('wordpress.com', 'public-api.wordpress.com'),
        'flags': ['"jetpack":', '"subscribers_count":', '"is_private":'],
        'regex': r'^(\{[\s\S]+\})$',
        'extract_json': True,
        'fields': {
            'uid': lambda x: x.get('ID'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('description') or None,
            'website': lambda x: x.get('URL') or None,
            'image': lambda x: (x.get('icon') or {}).get('img') or None,
            'follower_count': lambda x: x.get('subscribers_count'),
            'is_private': lambda x: x.get('is_private'),
            'is_deleted': lambda x: x.get('is_deleted'),
        },
        'url_mutations': [{
            'from': r'https?://(?P<username>[^/?#.]+)\.wordpress\.com/?',
            'to': 'https://public-api.wordpress.com/rest/v1.1/sites/{username}.wordpress.com',
        }],
    },
    'Codecademy profile': {
        'url_hints': ('codecademy.com',),
        'flags': ['__NEXT_DATA__', '"profile":', '"profileImageUrl":', '"proGold":'],
        'regex': r'id="__NEXT_DATA__"[^>]*>([\s\S]+?)</script>',
        'extract_json': True,
        'transforms': [
            json.loads,
            lambda x: x.get('props', {}).get('pageProps', {}).get('profile', {}),
            json.dumps,
        ],
        'fields': {
            'uid': lambda x: x.get('id'),
            'username': lambda x: x.get('username'),
            'fullname': lambda x: x.get('name') or None,
            'bio': lambda x: x.get('bio') or None,
            'image': lambda x: x.get('profileImageUrl') or None,
            'is_pro': lambda x: x.get('pro'),
            'codecademy_is_pro_gold': lambda x: x.get('proGold'),
            'is_private': lambda x: True if x.get('__typename') == 'PrivateUser' else None,
        },
    },
    'About.me profile': {
        'url_hints': ('about.me',),
        'flags': ['about.me', 'aboutme_prod:page', 'application/ld+json'],
        'bs': True,
        'fields': {
            'fullname': lambda x: _fl_ld(x, 'name'),
            'bio': lambda x: _fl_ld(x, 'description'),
            'website': lambda x: _fl_ld(x, 'url'),
            'image': lambda x: _fl_ld(x, 'image', 'url'),
        },
    },
    'Fur Affinity profile': {
        'url_hints': ('furaffinity.net',),
        'flags': ['Fur Affinity', 'og:title', 'Userpage of'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'/user/([^/?#]+)/?'),
            'fullname': lambda x: _meta_re(x, 'og:title', r'Userpage of\s+(.+?)\s+--'),
            'bio': lambda x: _meta(x, 'og:description'),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'Pikabu profile': {
        'url_hints': ('pikabu.ru',),
        'flags': ['pikabu.ru', 'data-user-id=', 'profile__nick'],
        'bs': True,
        'fields': {
            'uid': lambda x: (lambda t: t.get('data-user-id') if t else None)(x.find(attrs={'data-user-id': True})),
            'username': lambda x: _meta_re(x, 'og:url', r'/@([^/?#]+)'),
            'image': lambda x: _meta(x, 'og:image') or None,
        },
    },
    'Codepen profile': {
        'url_hints': ('codepen.io',),
        'flags': ['codepen.io', 'og:url', 'CodePen'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'codepen\.io/([^/?#]+)'),
            'fullname': lambda x: _meta_re(x, 'og:title', r'^(.+?)\s+on CodePen$'),
            'bio': lambda x: _meta(x, 'og:description'),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'Letterboxd profile': {
        'url_hints': ('letterboxd.com',),
        'flags': ['letterboxd.com', 'og:url', 'Letterboxd'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'letterboxd\.com/([^/?#]+)/?'),
            'fullname': lambda x: _meta_re(x, 'og:title', r'^(.+?)(?:’s|\'s)\s+profile$'),
            'bio': lambda x: _meta(x, 'og:description'),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'Gitee profile': {
        'url_hints': ('gitee.com',),
        'flags': ['Gitee.com', 'og:url', 'gon.info'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:title', r'\(([^)]+)\)'),
            'fullname': lambda x: _meta_re(x, 'og:title', r'^(.+?)\s*\('),
            'image': lambda x: _meta(x, 'og:image'),
            'bio': lambda x: _meta(x, 'og:description'),
        },
    },
    'Slack workspace': {
        'url_hints': ('slack.com',),
        'flags': ['slack.com', 'og:url', 'team_id'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'https?://([^./]+)\.slack\.com'),
            'fullname': lambda x: _meta(x, 'og:title'),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'Instructables member': {
        'url_hints': ('instructables.com',),
        'flags': ['Instructables', 'og:type', '/member/'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'/member/([^/?#]+)/?'),
            'fullname': lambda x: _meta(x, 'og:title'),
            'bio': lambda x: _meta(x, 'og:description'),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'Envato Author profile': {
        'url_hints': (
            'themeforest.net', 'codecanyon.net', 'audiojungle.net',
            'graphicriver.net', 'photodune.net', 'videohive.net', '3docean.net',
        ),
        'flags': ['profile on', 'envato', '/user/'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'/user/([^/?#]+)'),
            'fullname': lambda x: _meta_re(x, 'og:title', r"^(.+?)(?:'s|&#39;s)\s+profile on"),
            'bio': lambda x: _meta(x, 'og:description'),
            'image': lambda x: _meta(x, 'og:image'),
            'envato_marketplace': lambda x: _meta_re(x, 'og:title', r"profile on (\S+)$"),
        },
    },
    'Kwork freelancer': {
        'url_hints': ('kwork.ru', 'kwork.com'),
        'flags': ['Kwork', '<title>', '/user/'],
        'bs': True,
        'fields': {
            'username': lambda x: (lambda t: re.search(r'\(([^)]+)\)', t.text).group(1) if t and re.search(r'\(([^)]+)\)', t.text) else None)(x.find('title')),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'Freesound user': {
        'url_hints': ('freesound.org',),
        'flags': ['freesound.org', '/people/', 'Freesound'],
        'bs': True,
        'fields': {
            'username': lambda x: (lambda a: re.search(r'/people/([^/?#]+)/', a['href']).group(1) if a and a.get('title', '').startswith('Username:') else None)(x.find('a', title=re.compile(r'^Username:'))),
            'fullname': lambda x: (lambda h: h.get_text(strip=True) if h else None)(x.find('h1')),
        },
    },
    'Star Citizen citizen': {
        'url_hints': ('robertsspaceindustries.com',),
        'flags': ['robertsspaceindustries', 'UEE Citizen Record', 'Handle name'],
        'bs': True,
        'fields': {
            'uid': lambda x: _sc_value(x, 'UEE Citizen Record', strip='#'),
            'username': lambda x: _sc_value(x, 'Handle name'),
            'created_at': lambda x: _sc_value(x, 'Enlisted'),
            'location': lambda x: _sc_value(x, 'Location'),
            'sc_organization_rank': lambda x: _sc_value(x, 'Organization rank'),
            'sc_sid': lambda x: _sc_value(x, 'Spectrum Identification (SID)'),
            'sc_fluency': lambda x: _sc_value(x, 'Fluency'),
        },
    },
    'Dribbble profile': {
        'url_hints': ('dribbble.com',),
        'flags': ['dribbble.com', 'og:type', 'Dribbble', 'profile'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'dribbble\.com/([^/?#]+)'),
            'fullname': lambda x: _meta(x, 'og:title'),
            'bio': lambda x: _meta(x, 'description', tag_attr='name'),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'Depop shop': {
        'url_hints': ('depop.com',),
        'flags': ['depop.com', 'og:url', 'Depop'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'depop\.com/([^/?#]+)/?'),
            'fullname': lambda x: _meta_re(x, 'og:title', r"^(.+?)(?:’s|'s)\s+Shop"),
            'bio': lambda x: _meta(x, 'og:description'),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'ModDB member': {
        'url_hints': ('moddb.com',),
        'flags': ['moddb.com', '/members/', 'ModDB'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'/members/([^/?#]+)'),
            'fullname': lambda x: _meta(x, 'og:title'),
            'bio': lambda x: _meta(x, 'og:description'),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'Xbox Gamertag': {
        'url_hints': ('xboxgamertag.com',),
        'flags': ['Xbox Gamertag', 'Xbox Live Profile'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'description', r"^(.+?)(?:’s|'s)\s+Xbox Live Profile", tag_attr='name'),
            'fullname': lambda x: _meta_re(x, 'description', r"^(.+?)(?:’s|'s)\s+Xbox Live Profile", tag_attr='name'),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'DonationAlerts streamer': {
        'url_hints': ('donationalerts.com',),
        'flags': ['donationalerts.com', 'DonationAlerts', '/r/'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'donationalerts\.com/r/([^/?#]+)'),
            'image': lambda x: (lambda v: v if v and 'da_logo' not in v else None)(_meta(x, 'og:image')),
        },
    },
    'CCM profile': {
        'url_hints': ('ccm.net',),
        'flags': ['ccm.net', "'s profile - CCM", '/profile/user/'],
        'bs': True,
        'fields': {
            'username': lambda x: (lambda t: re.search(r"^(.+?)(?:’s|'s)\s+profile - CCM$", t.text).group(1) if t and re.search(r"^(.+?)(?:’s|'s)\s+profile - CCM$", t.text) else None)(x.find('title')),
            'image': lambda x: _meta(x, 'og:image'),
        },
    },
    'Wikidot user': {
        'url_hints': ('wikidot.com',),
        'flags': ['Wikidot', 'profile-title', 'profile-box'],
        'bs': True,
        'fields': {
            'username': lambda x: (lambda t: t.get_text(strip=True) if t else None)(x.find(class_='profile-title')),
            'gender': lambda x: _wikidot_field(x, 'Gender'),
            'website': lambda x: _wikidot_field(x, 'Website'),
            'created_at': lambda x: _wikidot_field(x, 'Wikidot user since'),
            'wikidot_account_type': lambda x: _wikidot_field(x, 'Account type'),
            'karma': lambda x: _wikidot_field(x, 'Karma level'),
        },
    },
    'Couchsurfing person': {
        'url_hints': ('couchsurfing.com',),
        'flags': ['couchsurfing.com', 'Couchsurfing', '/people/'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'/people/([^/?#]+)'),
            'fullname': lambda x: (lambda v: v if v and v.lower() != 'couchsurfing' else None)(_meta(x, 'og:title')),
            'bio': lambda x: (lambda v: v if v and 'Couchsurfers share their homes' not in (v or '') else None)(_meta(x, 'og:description')),
            'image': lambda x: (lambda v: v if v and 'og_image-' not in (v or '') else None)(_meta(x, 'og:image')),
        },
    },
    'ReverbNation artist': {
        'url_hints': ('reverbnation.com',),
        'flags': ['reverbnation.com', 'ReverbNation', 'og:type'],
        'bs': True,
        'fields': {
            'username': lambda x: _meta_re(x, 'og:url', r'reverbnation\.com/([^/?#]+)'),
            'fullname': lambda x: _meta_re(x, 'og:title', r'^(.+?)(?:\s*\|\s*)'),
            'bio': lambda x: _meta(x, 'og:description'),
            'image': lambda x: (lambda v: v if v and 'rn-logo' not in (v or '') else None)(_meta(x, 'og:image')),
        },
    },
}

# -- Plugin loading (must come after the built-in schemes dict is defined) --
from .plugins import load_plugins  # noqa: E402
load_plugins(schemes)
