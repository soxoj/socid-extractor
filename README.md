# socid_extractor

[![PyPI version](https://img.shields.io/pypi/v/socid-extractor.svg)](https://pypi.org/project/socid-extractor/)
[![Downloads/month](https://static.pepy.tech/badge/socid-extractor/month)](https://pepy.tech/project/socid-extractor)
[![Total downloads](https://static.pepy.tech/badge/socid-extractor)](https://pepy.tech/project/socid-extractor)
[![License](https://img.shields.io/pypi/l/socid-extractor.svg)](https://github.com/soxoj/socid-extractor/blob/master/LICENSE)

[![CI](https://img.shields.io/github/actions/workflow/status/soxoj/socid-extractor/python-package.yml?branch=master&label=tests)](https://github.com/soxoj/socid-extractor/actions/workflows/python-package.yml)
[![GitHub stars](https://img.shields.io/github/stars/soxoj/socid-extractor.svg?style=social)](https://github.com/soxoj/socid-extractor/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/soxoj/socid-extractor.svg?style=social)](https://github.com/soxoj/socid-extractor/network/members)

> Turn any public profile page into a structured account record — usernames, display names, bios, avatars, locations, joined-at dates, follower counts, external links, and the **stable internal identifiers** that uniquely pin an account across renames, redesigns, and deletions.

`socid_extractor` parses HTML pages and API responses from 130+ platforms and returns a flat, machine-readable dictionary of account fields. No API keys required, no headless browser — just a single function call on response text.

**Why it's useful**

- **Stable cross-service IDs.** Get GAIA ID (Google), Facebook UID, Yandex Public ID, Instagram pk, and dozens more — values that survive username changes and let you correlate accounts across leaks, archives, and search-engine indices.
- **One uniform interface.** Same `extract()` call for Instagram, GitHub, VK, Reddit, Substack, Bluesky, TikTok — no per-platform glue code on your side.
- **Field ontology.** [Normalized field names](https://github.com/soxoj/socid-extractor/blob/master/FIELDS.md) across platforms (`username`, `fullname`, `created_at`, `is_verified`, …) so downstream pipelines don't need 130 mappings.
- **Battle-tested.** Powers [Maigret](https://github.com/soxoj/maigret) and a number of other OSINT tools.

## Installation

Python: 3.10+.

```sh
pip install socid-extractor
```

For a clean CLI install on a workstation:

```sh
pipx install socid-extractor
```

The latest development version:

```sh
pip install -U git+https://github.com/soxoj/socid-extractor.git
```

## Quick start

**As a CLI:**

```sh
$ socid_extractor --url https://www.deviantart.com/muse1908
country: France
created_at: 2005-06-16 18:17:41
gender: female
username: Muse1908
website: www.patreon.com/musemercier
links: ['https://www.facebook.com/musemercier', 'https://www.instagram.com/muse.mercier/', 'https://www.patreon.com/musemercier']
tagline: Nothing worth having is easy...
```

**As a Python library:**

```python
import requests
import socid_extractor

r = requests.get('https://www.patreon.com/annetlovart')
print(socid_extractor.extract(r.text))
# {'patreon_id': '33913189', 'patreon_username': 'annetlovart',
#  'fullname': 'Annet Lovart',
#  'links': "['https://www.facebook.com/322598031832479', ...]"}
```

**Tip — batch runs:** pass `--skip-fetch-if-no-url-hint` to skip the HTTP request when the URL doesn't match any known site hint (faster, but may skip generic engines such as forum templates):

```sh
$ socid_extractor --url https://example.com/foo --skip-fetch-if-no-url-hint
```

## Supported sites

[**130+ schemes** — see METHODS.md for the full list.](https://github.com/soxoj/socid-extractor/blob/master/METHODS.md)

A non-exhaustive sample:

- **Major networks:** Facebook (user & group pages), Instagram, VK.com, OK.ru, Reddit, TikTok, Bluesky, Tumblr, Flickr
- **Google ecosystem:** Google docs/maps contributions (cookies required), Google Play, YouTube
- **Mail.ru:** my.mail.ru user mainpage, photo, video
- **Dev / writing platforms:** GitHub, Stack Overflow (HTML + API), LeetCode, Hashnode, Medium, Substack, Paragraph, WordPress.org, Virgool
- **Forums (universal detectors):** Discourse, MediaWiki / Fandom wikis, Mastodon
- **Niche / vertical:** Chess.com, Roblox, MyAnimeList, Scratch, Wikipedia, DailyMotion, SlideShare, Weebly, Calendly, Amazon Author, Boosty, Warpcast (Farcaster), Fragment (TON/Telegram), Rarible, CSSBattle, lnk.bio, Spatial, TwitchTracker, Max (max.ru)

…and many others.

For data examples, see [`tests/test_e2e.py`](https://github.com/soxoj/socid-extractor/blob/master/tests/test_e2e.py); for the parsing logic, see [`socid_extractor/schemes.py`](https://github.com/soxoj/socid-extractor/blob/master/socid_extractor/schemes.py); for the field ontology, see [FIELDS.md](https://github.com/soxoj/socid-extractor/blob/master/FIELDS.md).

## Use cases

- **Pivot from a profile to everything you can see.** One call returns the visible info plus the hidden internal IDs the platform uses behind the scenes. Background reading: [Week in OSINT — Getting a grasp on Google IDs](https://medium.com/week-in-osint/getting-a-grasp-on-googleids-77a8ab707e43).
- **Track accounts across renames, redesigns, and deletions.** Stable IDs (GAIA, FB UID, Yandex Public ID, Instagram pk, …) let you re-identify the same person even when every visible field has changed. Background: [Aware Online — User IDs in social-media investigations](https://www.aware-online.com/en/importance-of-user-ids-in-social-media-investigations/).
- **Search by cross-service UID.** Once you have a stable identifier you can pivot into:
  - SQL / leaked databases (forum dumps, breach data) where the UID is the join key,
  - Google / Yandex / archive.org indices that captured URLs containing the UID.
- **Feed downstream OSINT tooling.** A normalized record is much easier to ingest than per-site scrapers — used by [Maigret](https://github.com/soxoj/maigret) and similar tools for enrichment.

## Commercial Use

The open-source `socid_extractor` is MIT-licensed and free for commercial use without restriction — but page parsers break over time as platforms change their HTML and APIs, and they need active maintenance.

For serious commercial use — with a maintained private plugin pack of extra parsers or a hosted extraction API — reach out: 📧 socid@soxoj.com

- Private parser plugin — **100+ additional checks** on top of the public 150+ sites, kept up to date as platforms change (separate from the public open-source database)
- Extraction API — integrate `socid_extractor` into your product

## SOWEL classification

Maps to the following [SOWEL](https://sowel.soxoj.com/) techniques:
- [SOTL-1.4. Analyze Internal Identifiers](https://sowel.soxoj.com/internal-identifiers)
- [SOTL-11.1. Check Outdated And Unused Functionality](https://sowel.soxoj.com/outdated-unused-functionality)

## Tools using socid_extractor

- [**Maigret**](https://github.com/soxoj/maigret) — powerful namechecker that generates a report with all available info from accounts found across 3000+ sites.
- [**TheScrapper**](https://github.com/champmq/TheScrapper) — scrape emails, phone numbers, and social-media accounts from a website.
- [**InfoHunter**](https://github.com/sweetnight19/InfoHunter) — open-source OSINT tool to search, collect, and analyze information online.
- [**YaSeeker**](https://github.com/HowToFind-bot/YaSeeker) — gather all available information about a Yandex account by login/email.
- [**Marple**](https://github.com/soxoj/marple) — scrape search-engine results for a given username.

## Testing

```sh
python3 -m pytest tests/test_e2e.py -n 10 -k 'not cookies' -m 'not github_failed and not rate_limited'
```

**Every new scheme must have an e2e test** in `tests/test_e2e.py` hitting a real URL/API. Unit tests with inline fixtures (`tests/test_socid_improvements.py`) are also required but do not replace e2e coverage. See [docs/testing-and-ci.md](docs/testing-and-ci.md) for details.

Developer documentation (architecture, modules, CI) lives in [docs/](docs/).

## Contributing

See the [contributing guide](https://github.com/soxoj/socid-extractor/blob/master/CONTRIBUTING.md) if you want to add a new scheme or fix anything.
