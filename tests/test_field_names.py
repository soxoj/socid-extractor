"""Guard the field ontology in FIELDS.md against drift.

Every name a scheme can return has to be either documented in FIELDS.md or
listed in KNOWN_FIELD_NAMES below, which records the names that predate this
check. The point is not to bless that backlog -- it is to stop it growing:
a new scheme either reuses a standard name or documents the one it needs.

The backlog still holds near-misses of documented fields -- post_count beside
posts_count, emails beside email -- so reusing one of those will pass. They
are here rather than renamed because renaming a field already in a release
breaks whoever reads the output.
"""
import re
from pathlib import Path

from socid_extractor.schemes import schemes

ROOT = Path(__file__).parent.parent

# the names that predate this check. Do not add to this list: document the
# name in FIELDS.md instead
KNOWN_FIELD_NAMES = """
HistoryPublic InviteOnly Role RoomPublic about account_id account_type achievement_count
address all_views_count allowCrawler alternative_fullname ambassador answers_count
appreciations articles_count arxiv_ids au_id author_id author_name awards
awards_given_karma awards_got_karma badge_count badges_list birth_date blog
blog_description blog_id blog_title blog_url bluesky_handle bluesky_username
board_count boards bots_count broadcasts_count bubok bunq_invite_username
business_email business_title cards challenges_authored challenges_completed
channel_url cited_by_count clan cloudcast_count codecademy_is_pro_gold college
commentCount comment_score comments_karma company_founder_id company_info
contacts contribution contribution_level contributions_count created_count
credit_name crypto_wallet cssbattle_games_played cssbattle_id cssbattle_score
cssbattle_username dblp_pid description developer_name digg_count discord_invite
discord_username disqus_username draws_count edit_count education education_degree
education_school emails envato_marketplace experience external_ids external_url
eyeem_id eyeem_username facebook facebook_id facebook_pixel_id facebook_url
faceit_elo faceit_game faceit_region faceit_skill_level fake_gaia_id fans
favorite_count favorites_count favourites_count featured_count feed_url first_name
firstname flickr_id flickr_nickname flickr_username forums_count forums_following_count
fromLanguage full_name games_count gd_account_id gifs_count github_uid github_url
gog_achievements gog_games_owned gog_hours_played google_analytics_id gravatar_email_md5_hash
gravatar_id groups h_index hackernews_username has_2fa_enabled has_ban has_banned_in_search_suggestions
has_never_replies has_search_ban has_tracks has_tweets has_user_profile hash_code
hashed_user_id headline hearts_count hide_from_robots honor huggingface_datasets
huggingface_models huggingface_papers huggingface_spaces i10_index iban identifications_count
image_cdn images imgur_profile_avatar_url imgur_username impact instagram_url
institutions isMuted isPrivate isProfileStatusActive is_active is_ad_free
is_admin is_adult is_adult_content is_anonymous is_bad_content is_bad_or_shock
is_beta_user is_blocking is_community is_community_user is_creator is_deboosted
is_developer is_email_verified is_excluded_from_rating is_exists is_family_safe
is_following is_forbid is_from_q is_hidden_name is_identity is_indexed is_joined_recently
is_km is_looking_for_job is_medius is_mod is_moderator is_muting is_news is_nsfw
is_official is_online is_org is_organization is_paid is_partner is_passport
is_performer is_permanent is_personal is_power_contributor is_premium is_private_social_profiles
is_private_statistics is_pro is_profile_visible is_protected is_readonly is_restricted
is_scratchteam is_secret is_service is_streamer is_supporter is_thanks_dev_user
is_trackers_disabled is_twitter_verified is_verified_merchant is_video_channel
is_vip is_website_verified is_working_remotely keywords known_usernames language
languages last_answer_at last_name leaderboard_position learningLanguage legacy_id
lens_namespace lens_score level lichess_is_patron lichess_is_tos_violation
liked_albums liked_artists liked_by_users liked_photos liked_users likes likesArePublic
link linked_social linkedin_url listen_count locale losses_count lulu magazines_count
mail_id mail_uid mal_uid mal_username mastodon_id mastodon_url mastodon_username
max_description max_icon max_participants_count max_rank max_rating max_title
medium_id medium_username messenger_values messengers mime_type name name_alternatives
nft_count nickname observations_count ok_id ok_user_name_id openalex_id openpgp_key
opgg_level opgg_summoner_name opgg_tagline orcid org_domain org_name organization
organization_uuid osu_country_rank osu_global_rank osu_hit_accuracy osu_play_count
osu_pp other_names owner_uuid paragraph_user_id patreon_id patreon_username
payerId periscope_username phone phone_id photos picsart_id picsart_username
pinterest_username play_time_seconds points position_held post_count post_counts
post_karma post_score previous_usernames primaryCurrencyCode primary_account_id
primary_account_type primary_account_username profile_hits profile_type profile_url
pronouns protected_domains provider provider_id public_gists_count public_repos_count
publication_bio publication_name publication_subdomain purchased_at rank rank_score
ranking rarible_id rarible_owner rarible_ref rarible_type rating ratings_count
real_name reddit_id reddit_username registered_domains registration_status
reports_count reputation reputation_count reputation_label reputation_name
review_count reviews_count roblox_user_id sale_price sc_fluency sc_organization_rank
sc_sid school score sex skills skype slideshow_count smashwords smile_count
snapcode_image social_accounts soundcloud_username species_count stack_exchange_uid
state status statuses_count steam_nickname store_id subscribe_price subscriber_count
tagCount tagline teaser tier tiktok_url tiktok_username timezone tinder_username
title ton_wallet topics totalXp total_karma trust_level twitch_channel_id
twitch_url twitch_username twitter twitter_id twitter_screen_name twitter_uid
twitter_url type ugc_tracks_count uidme_uguid update_pic_at uploadCount upvotes_count
url usernames uuid verified verified_categories verified_email verified_reason
video_count videos viewer_uid vk_id wallet_address weebly_site_id weibo_id
wikidata_qid wikidot_account_type wikimapia_uid wins_count wishlist_count
work xenforo_points yandex_messenger_guid yandex_phone_id yandex_public_id
yandex_uid yandex_znatoki_id yelp_userid your_cpf your_emails your_ls_uid
your_name your_phone your_uid your_username your_wallet_balance your_yuid
youtube_channel youtube_url youtube_username
""".split()


def documented_names():
    doc = (ROOT / 'FIELDS.md').read_text()
    # first column of every table row, plus the bare names in the code blocks
    names = set(re.findall(r'^\| `([a-z_0-9]+)`', doc, re.M))
    names |= set(re.findall(r'^([a-z_0-9]+)\s+#', doc, re.M))
    return names


def scheme_field_names():
    found = {}
    for name, scheme in schemes.items():
        fields = set(scheme.get('fields') or {})
        if scheme.get('regex'):
            try:
                fields |= set(re.compile(scheme['regex']).groupindex)
            except re.error:
                pass
        for field in fields:
            if not field.startswith('_'):
                found.setdefault(field, name)
    return found


def test_field_names_are_documented_or_known():
    allowed = documented_names() | set(KNOWN_FIELD_NAMES)
    undocumented = {f: s for f, s in scheme_field_names().items() if f not in allowed}

    assert not undocumented, (
        'These field names are neither in FIELDS.md nor in the '
        'KNOWN_FIELD_NAMES list in this file:\n'
        + '\n'.join(f'  {f!r} in {s!r}' for f, s in sorted(undocumented.items()))
        + '\n\nCheck FIELDS.md for a standard name first -- "subscribers" is '
          'follower_count, "joined" is created_at. If the data really has no '
          'standard equivalent, add the name to FIELDS.md rather than here.'
    )
