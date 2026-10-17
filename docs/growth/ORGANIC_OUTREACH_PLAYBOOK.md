# Organic outreach playbook

Updated: October 17, 2026. Goal: help local people find an event or community,
without advertising spend. These are reviewable drafts and operator procedures;
no accounts have been created and no messages have been sent.

## Establish one maintained channel

The owner has no currently managed social/community channels. Start with one
project-owned LinkedIn presence if a maintainer can sustain it, or use an existing
organizer-approved channel if that is more practical. Record the responsible
person, recovery arrangements, and approved posting locations privately. Inventory
existing LinkedIn, Discord, and other website destinations before treating them
as project-owned. Repair stale links through normal review.

Use this profile description after reviewing it for the chosen channel:

> Discover technology groups and upcoming meetups in Spokane and the Inland
> Northwest. Explore local communities, check event details, and RSVP with the
> organizer at SpokaneTech.org.

Link the profile to the preferred public site. Use a consistent SpokaneTech name,
the existing brand artwork, and current About-page wording. Add only confirmed
owned profiles to `SEO_VERIFIED_PROFILE_URLS`. Do not create a Google Business
Profile using an event venue or a virtual address for this directory.

## Prepare and review a weekly roundup

Run from `src/django_project` in the configured environment:

```shell
python manage.py preview_growth_posts --source linkedin
python manage.py preview_growth_posts --source discord
python manage.py preview_growth_posts --source partner
```

The command reads up to ten active events from enabled groups over the next seven
days. It outputs real titles, hosts, Pacific start times, first-party campaign
links, and unchanged provider RSVP URLs. It does not invoke AI, modify events,
or publish. An empty array means no matching events, not permission to invent a
roundup. Use actual current listings for later weeks as well.

Before publishing, check each source page for cancellation, venue/time changes,
cost, and participation requirements. Choose a few relevant events rather than
copying every description. Link to SpokaneTech for discovery and retain the
organizer's RSVP link. Attribute the organizer; do not imply that SpokaneTech
runs the event. Do not promise free admission, beginner friendliness, or available
seats without checking.

Draft format, replacing every bracketed field with reviewed preview data:

```text
This week in Spokane tech

[Actual event name] — [actual local date and time]
Hosted by [actual group]. [One factual sentence explaining the topic.]
Explore: [discovery_url]
RSVP and current attendance details: [rsvp_url]

Find more upcoming events: https://www.spokanetech.org/events/list?utm_source=linkedin&utm_medium=organic_social&utm_campaign=weekly_events
```

Publish manually for the first two cycles and check links and measurements.
Existing notification code can use first-party discovery links later with
`PROMOTE_SITE_LINKS=True`; posting controls remain separate. Do not enable
automation for a channel until its owner has approved its use and cadence.

## Ask organizers and local resources for useful referrals

Build a small list of relevant public contact pages: listed tech-group organizers,
local libraries, colleges, coworking communities, and regional technology
organizations. Start with up to five suitable resources as a manageable trial,
not a volume target. Verify each contact and its submission policy. Record the
actual resource, permission, placement, and campaign link in
[OUTREACH_REGISTER.csv](OUTREACH_REGISTER.csv); do not scrape personal contacts
or send bulk messages.

Suggested message for an organizer or resource owner, sent only after review:

```text
Hello [name/team],

I help maintain SpokaneTech.org, a community directory of technology groups
and events in Spokane and the Inland Northwest. [One specific, accurate reason
the directory could help their audience.]

Would a link to our upcoming-events directory be useful on [relevant resource
page or approved channel]? We link visitors to organizers for RSVP and current
attendance details. Please let us know if any information about your group
needs correcting.

[Reviewed first-party campaign URL]

Thank you,
[actual maintainer name and contact]
```

Respect a refusal or no-promotion rule. Ask moderators before sharing in a
community you do not own. Do not buy links, request reciprocal links as a condition,
or add irrelevant directory placements. A plain, useful editorial link is enough.
For a confirmed partner, a non-personal source identifier such as `local_library`
can distinguish referrals; use `utm_medium=referral` for resource-page links.
The preview command's partner default is `organic_social`; adjust the medium
when the actual placement is a resource page rather than a social post.

## Maintain useful first-party content

The new first-meetup and community-selection guides use current application data.
Review their advice monthly and after organizer feedback. Share a guide when it
answers a question; avoid repetitive event-link posts. Add a topic hub only when
there are enough relevant enabled groups, useful original advice, and a named
maintainer to keep it accurate. Do not generate thin pages for every tag.

Offer organizers the existing detail-page copy-link control for sharing their
group or event. Use the directory's actual canonical link in any printed or QR
material and test it on a phone before distributing. Such material should
identify SpokaneTech as the directory, not as the event organizer.

## Weekly operating routine and measurement

Proposed initial allowance: roughly two hours per week, to be confirmed by the
maintainer. Spend it checking listings and preparing one roundup, responding to
organizer corrections, reviewing a few relevant referral opportunities, and
recording results. Reduce the cadence if it cannot be maintained accurately.

Use [ORGANIC_TRAFFIC_SCORECARD.csv](ORGANIC_TRAFFIC_SCORECARD.csv) for weekly
snapshots after completing the [rollout checks](SEO_IMPLEMENTATION_AND_ROLLOUT.md).
Record date range, timezone, acquisition filters, and metric definitions in
notes so comparisons remain consistent. Keep account exports and contact
details private; the committed CSV files are blank templates.

Report RSVP/community-link actions as intent proxies. Compare sessions with at
least one such action against qualified sessions; do not add raw clicks together
and label them attendees. Search Console reports search performance, while GA4
measures on-site activity and may differ because of collection limitations.
Leave unavailable values blank and explain why. Establish numerical targets only
after a trustworthy baseline exists.

At weeks six and twelve, review which queries, guides, and referral placements
lead to useful actions. Continue what helps local discovery, correct stale links,
and retire unsustainable posting. Consider calendar/feed subscriptions only when
there is demonstrated demand and an owner for update/cancellation semantics.
