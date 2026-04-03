# socid_extractor Field Ontology

Standard field names for extraction schemes. When adding a new scheme,
use existing names from this document. Create platform-specific fields
(with a prefix) only when data does not fit any standard category.

## Identity

| Field | Description | API mapping examples |
|-------|-------------|----------------------|
| `uid` | Numeric or string account ID on the platform | `id`, `user_id`, `pk`, `userid`, `steamid`, `did` |
| `username` | Unique login / handle (what appears in URL) | `login`, `screen_name`, `handle`, `slug`, `vanity` |
| `fullname` | Display name | `name`, `displayName`, `display_name`, `full_name`, `screenname`, `personaname` |
| `id` | Alternative to `uid` (legacy, prefer `uid`) | -- |

**Rule:** If the API returns `name` as a display name, map it to `fullname`.
If `name` is a login/handle, map it to `username`.

## Profile

| Field | Description | API mapping examples |
|-------|-------------|----------------------|
| `bio` | Biography / profile description | `description`, `about`, `signature`, `status_message`, `tagline` |
| `image` | Avatar / profile picture URL | `photo`, `avatar`, `profile_pic_url`, `avatar_url`, `profileImageURL` |
| `image_bg` | Background / banner image URL | `banner`, `cover`, `bannerImageURL`, `cover_250_url` |
| `website` | Personal website URL | `url`, `domain_url`, `external_url`, `blog_url` |
| `email` | Public email | -- |

## Demographics

| Field | Description | API mapping examples |
|-------|-------------|----------------------|
| `gender` | Gender | `sex` |
| `country` | Country | `country_code` (normalize to name) |
| `city` | City | -- |
| `location` | Location (free text, city+country) | `address` |
| `birthday` | Date of birth | `birth_date`, `dateOfBirth` |

## Dates

| Field | Description | API mapping examples |
|-------|-------------|----------------------|
| `created_at` | Registration / account creation date | `joinedAt`, `registration`, `registration_date`, `history.joined`, `joined` (unix), `created_time` (unix), `createdAt` |
| `updated_at` | Last profile update date | `modifyDate`, `updatedAt` |
| `latest_activity_at` | Last visit / activity / online time | `last_online` (unix), `last_seen_at`, `active` |

## Counters

| Field | Description | API mapping examples |
|-------|-------------|----------------------|
| `follower_count` | Followers / subscribers | `followers`, `followers_count`, `followersCount`, `subscribers_count`, `numFollowers` |
| `following_count` | Following / subscriptions | `following`, `friends_count`, `followingCount`, `numFollowing` |
| `posts_count` | Number of posts / publications | `postsCount`, `media_count`, `buzz_count`, `numPosts` |
| `comments_count` | Number of comments | `numPosts` (Disqus counts comments as posts) |
| `likes_count` | Received likes | `numLikesReceived`, `likes_count`, `heartCount` |
| `views_count` | Views | `all_views_count`, `profile_views`, `profile_hits` |
| `videos_count` | Number of videos | `videos_total`, `nb_videos` |
| `photos_count` | Number of photos | `photoCount`, `photos_count` |
| `friends_count` | Friends (mutual relationship) | `totalFriends` |

**Rule:** Always use singular noun + `_count`:
`follower_count` (not `followers_count`), `video_count` / `videos_count`.

## Boolean flags

| Field | Description | API mapping examples |
|-------|-------------|----------------------|
| `is_verified` | Verified account | `verified`, `isVerified`, `has_verified_badge` |
| `is_private` | Private profile | `isPrivate`, `text_post_app_is_private` |
| `is_banned` | Banned account | `isBanned` |
| `is_deleted` | Deleted account | -- |
| `is_suspended` | Suspended account | `suspended` |
| `is_business` | Business account | -- |
| `is_employee` | Platform employee | `isEmployee`, `scratchteam` |

**Rule:** Boolean fields start with `is_` and are stored as strings `'True'`/`'False'`.
Never use bare `verified` — always `is_verified`.

**Common mistakes to avoid:**
- `verified` → `is_verified`
- `joined` → `created_at`
- `last_online` → `latest_activity_at`

## Cross-platform links

| Field | Description | API mapping examples |
|-------|-------------|----------------------|
| `links` | List of external links | `socialLinks`, `websites` |
| `social_links` | Linked social accounts (structured) | -- |
| `twitter_username` | Twitter/X handle | `twitterUsername`, `twitter_screen_name` |
| `facebook_uid` | Numeric Facebook ID | Also extracted from `graph.facebook.com/{id}/picture` in avatar URLs |
| `facebook_username` | Facebook username | -- |
| `instagram_username` | Instagram handle | -- |
| `telegram_username` | Telegram handle | -- |
| `vk_username` | VK handle | -- |
| `github_username` | GitHub username | -- |

## Platform-specific fields

Fields with unique meaning that have no standard equivalent. Use a platform
prefix **only** for such fields:

```
# Correct -- unique platform-specific data:
youtube_channel_id    # UC... format, unique to YouTube
tiktok_id             # differs from username and uid
sec_uid               # TikTok-specific secondary UID
steam_id              # Steam64 ID
gaia_id               # Google Account ID
karma                 # Reddit/Habr/Lesswrong
heart_count           # TikTok
streak                # Duolingo

# Wrong -- should use standard names:
xvideos_user_id       # -> uid
xvideos_username      # -> username
chess_user_id         # -> uid
twitchtracker_username # -> username
```

## API response mapping examples

### JSON API (Bluesky)
```python
'fields': {
    'uid': lambda x: x.get('did'),          # did:plc:... -> uid
    'username': lambda x: x.get('handle'),   # jay.bsky.team -> username
    'fullname': lambda x: x.get('displayName'),
    'bio': lambda x: x.get('description'),
    'image': lambda x: x.get('avatar'),
    'follower_count': lambda x: x.get('followersCount'),
    'following_count': lambda x: x.get('followsCount'),
    'posts_count': lambda x: x.get('postsCount'),
    'created_at': lambda x: x.get('createdAt'),
}
```

### HTML regex (XVideos)
```python
'regex': r'"id_user":(?P<uid>\d+),"username":"(?P<username>[^"]+)","display":"(?P<fullname>[^"]*)"'
         r'[\s\S]*?"sex":"(?P<gender>[^"]*)"'
         r'[\s\S]*?Country:</strong>\s*<span>(?P<country>[^<]*)</span>'
         r'[\s\S]*?Subscribers:</strong>\s*<span>(?P<follower_count>[^<]*)</span>'
         r'[\s\S]*?Signed up:</strong>\s*<span>(?P<created_at>[^(<]*)'
```

### og:meta (Habr)
```python
# og:title = "Name aka username" -> fullname + username
'regex': r'og:title" content="(?P<fullname>.+?) aka (?P<username>\w+)'
```

## When to create a new field

1. Check this document -- is there a standard equivalent?
2. Does the data fit a standard field? -> Use it with mapping in the lambda.
3. Is the data unique to the platform with no equivalent? -> Create with platform prefix.
4. Is the data useful across multiple platforms but not listed here? -> Add it to this document as a new standard field.
