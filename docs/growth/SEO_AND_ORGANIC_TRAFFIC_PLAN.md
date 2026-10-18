# SpokaneTech discoverability and organic traffic plan

Reviewed: October 17, 2026. Source baseline: `96a1791`.
Status: **repository implementation approved and completed; production rollout
and account-side validation pending**. See the
[implementation and rollout guide](SEO_IMPLEMENTATION_AND_ROLLOUT.md) and
[organic outreach playbook](ORGANIC_OUTREACH_PLAYBOOK.md).

## 1. Objective, constraints, and decisions

Primary outcome: help local people discover upcoming events, find relevant tech
communities, and take a useful next step. Prioritize Spokane and the Inland
Northwest rather than general software-development traffic.

Confirmed by the owner:

- Use **organic outreach only**. No advertising spend, paid SEO tools, or paid
  placements are included in this plan.
- No social/community channels are currently managed by the owner. Existing
  profile links, invite URLs, credentials, and notification code are not evidence
  of an active, owned distribution channel.
- Google Analytics is used. Public registration, marketing emails, and payments
  are not currently offered.
- The owner controls DNS through Namecheap and has started Google Search Console
  ownership verification. **Treat Google ownership setup as complete for planning
  purposes.** Google's verification confirmation is still pending and is not a
  blocker for preparing the technical SEO changes. Follow the
  [search engine ownership setup guide](SEARCH_ENGINE_OWNERSHIP_SETUP.md) for
  verification troubleshooting and subsequent Bing setup.

Operator decisions and account checks before production rollout:

1. Bing Webmaster Tools setup status and access to existing GA4 reports and
   data-stream settings. Google ownership setup is accounted for; access to
   Google's reports and verification-dependent tools can be confirmed once
   verification finishes. Neither pending Google confirmation nor Bing setup
   blocks preparation of the indexability, metadata, or sitemap changes.
2. Preferred public hostname. Recommend `https://www.spokanetech.org` because the
   README already identifies it, subject to checking existing search signals,
   links, certificates, and proxy configuration.
3. Which existing social profiles and Discord invite belong to the project or
   an approved community partner, and who can manage them.
4. A named technical owner and community/editorial owner; these can be the same
   person. Establish a sustainable weekly time allowance before choosing channels.

The owner approved implementation after reviewing this plan. Repository changes
are prepared for review; deployment, contacting organizers, posting messages,
creating accounts, and changing external analytics settings remain operator
actions. No live messages or account changes were made by the implementation.

### Implementation record

| Scope | Repository delivery | Remaining operational work |
| --- | --- | --- |
| Phase 1 | Explicit indexing setting, route policy, corrected robots directives, canonical origin, `/index/` redirect, HTMX cache/history safeguards | Deploy with production indexing enabled; preferred-host proxy redirect; Google confirmation, Bing setup, and report baseline |
| Phase 2 | Real page metadata and social previews, public sitemap, reviewed-event JSON-LD, breadcrumbs, homepage Organization/WebSite data | Review event eligibility; Rich Results Test and URL Inspection; submit sitemap; validate public media accessibility |
| Measurement | Optional manual HTMX/history page views; RSVP/community/share intent events; safe campaign parameters | Inspect GA4 stream settings, prevent automatic/manual duplication, verify live collection and define qualified sessions |
| Organic distribution | Opt-in first-party links in existing notification payloads, preserved provider RSVP links, bounded Discord summaries, read-only preview command | Confirm profile ownership and permissions; review drafts; publish manually before enabling automation |
| Useful content and referrals | Two original guides backed by real groups/events, navigation links and copy-link controls; outreach playbook, blank register and scorecard | Maintain guides, establish one channel, request appropriate referrals, collect weekly results |
| Optional later work | Deliberately deferred subscription feeds, extra topic hubs, and performance changes | Establish demand or measured performance evidence before a separate implementation |

The audit findings below describe the pre-implementation baseline, not the new
code's behavior or a claim that production has already changed. Safe defaults
retain noindex until the production operator explicitly enables indexing.

## 2. Audit findings and evidence

Read-only checks covered templates, URL configuration, views, event/group models,
ingestion/image processing, notification payloads, frontend navigation, static
assets, policy constraints, and a small set of public HTTP requests. No application
or production database was changed. No analytics account or search-console
reports were accessed, so traffic levels, current rankings, and acquisition costs
are unknown.

### Live checks on October 17, 2026

| Request | Observed result |
| --- | --- |
| `https://www.spokanetech.org/` | HTTP 200; title `Spokane Tech`; robots meta `noindex, nofollow`; no canonical link; no `X-Robots-Tag` response header. |
| `https://spokanetech.org/` | HTTP 200 at the non-www hostname without redirecting; same title and robots directive; no canonical link. |
| `https://www.spokanetech.org/robots.txt` | HTTP 200; disallows `/__debug__/`, `/accounts/`, and `/admin/`; no sitemap reference. |
| `https://www.spokanetech.org/sitemap.xml` | HTTP 404. |

The live sample is not a complete crawl. Do not infer the indexing status of every
URL, TLS/proxy behavior for every hostname, or Google's selected canonical from
these requests alone. Production event/group pages and Search Console need
verification during rollout.

### Source findings

Paths below are relative to the repository root.

| ID | Finding | Evidence and implication |
| --- | --- | --- |
| F1 — critical | Global indexing prohibition | `core/templates/base.htm`, under `src/django_project/`, hard-codes `noindex, nofollow`. The live homepage confirms it is deployed. Google's crawler can exclude the page from results when it reads this directive. Fix this before scaling promotion. [Google noindex guidance](https://developers.google.com/search/docs/crawling-indexing/block-indexing). |
| F2 — high | Identical metadata on all full pages | The base hard-codes the title, description, and two Open Graph text fields. Event and group pages have no dedicated search titles or summaries; there is no canonical, social image, or `og:url`. |
| F3 — high | Duplicate hosts and route aliases | Both HTTPS hostnames serve content. `web/urls.py` serves `/` and `/index/`, event/group directory display variants, and several calendar forms. Consolidation should preserve existing public links. [Canonicalization guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls). |
| F4 — high | No sitemap implementation | No sitemap route or classes exist; the live default sitemap URL is 404. Crawlers have no maintained list of preferred public group and event pages. A sitemap helps discovery but does not guarantee indexing. [Sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview). |
| F5 — medium | Robots policy does not match actual administration route | `core/views.py` disallows `/admin/`, but `core/urls.py` mounts Django admin at `/console/`. `/host/`, helper routes, modal endpoints, and minimal fragments also need an explicit indexing policy. Robots rules are not access controls. |
| F6 — high | No event structured data | Event models already provide names, dates, locations, images, source links, groups, and cancellation status. Templates do not emit Event JSON-LD. Eligibility still depends on actual event data and Google's rules. [Event documentation](https://developers.google.com/search/docs/appearance/structured-data/event). |
| F7 — high | Existing promotion sends visitors to providers | Discord embed links, LinkedIn article links, and weekly digest RSVP links predominantly use `event.url`, the Meetup/Eventbrite/source destination. They do not create a deliberate discovery path through SpokaneTech. See `web/utilities/notifiers/discord.py`, `linkedin.py`, and `web/tasks.py`. |
| F8 — high | Acquisition/conversion measurement needs validation | GA initialization is present in the base, but no app-level tracking strategy exists for RSVP clicks, group/community actions, campaign naming, or HTMX navigation. GA4 may already track history changes and outbound clicks depending on configuration; missing or duplicate counts must be tested rather than assumed. [Enhanced measurement](https://support.google.com/analytics/answer/9216061). |
| F9 — medium | Topics do not lead to discovery pages | `web/partials/home/tags.htm` renders tag spans. There are no curated, indexable topic hubs or newcomer guides. Tags exist in real data and could support useful navigation after editorial review. |
| F10 — medium | Existing blog content points elsewhere | `blogs/models.py` stores external article URLs; blog cards and Develop page links send readers to those sources. There are no first-party article detail routes. This is useful attribution, but it does not supply an owned library of local community guides. |
| F11 — medium | Calendar can create a very large URL space | Calendar navigation supports years 1 through 9998 and many empty months. Avoid submitting or encouraging indexing of an unbounded set of thin calendar pages. |
| F12 — measure first | Performance opportunities are unmeasured | Third-party CSS/JS includes jQuery and Animate.css as well as active Bootstrap/HTMX/Font Awesome. Existing hero assets are about 306 KB desktop WebP and 100 KB mobile WebP before delivery compression. Event downloads already become metadata-free WebP thumbnails capped at 1600 pixels. Measure actual page weight and Core Web Vitals before removing packages or changing image handling. |
| F13 — foundation | Public content is server-rendered and linked | Full views render event/group content in initial HTML and cards contain real `href` values. Preserve this advantage; HTMX can enhance navigation without becoming a requirement for discovery. |

The old meta-keywords field is not a useful optimization priority; descriptive
content and indexability matter more. Google explicitly ignores meta keywords.
[Google SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide).

## 3. Implementation order and release gates

Estimates are planning ranges for a maintainer familiar with the code, not fixed
quotes or promises of calendar completion. Community work requires continuing
ownership. No framework replacement or URL-slug migration is proposed.

### Phase 1 — Make public pages eligible and establish a baseline

Priority: **P0**. Indicative technical effort: 1–2 days, plus remaining account
tasks. Google ownership setup is complete for planning purposes.

1. Define explicit production indexability, for example an opt-in
   `SEO_INDEXING_ENABLED` setting with a safe default for development/staging.
   Do not infer publication solely from `DEBUG=False` or an incoming Host header.
2. Replace the base-wide prohibition with a documented per-page policy. Allow
   the homepage, useful event/group directories, approved group/event details,
   About, and appropriate editorial pages. Keep non-production and utility,
   authentication, administrative, modal, and fragment-only pages out of results.
3. Correct robots route coverage, including `/console/`, and add the preferred
   sitemap location when it is deployed. If an already indexed URL must be
   removed, ensure Google can read its noindex response; a robots disallow alone
   prevents that reading and is not a guaranteed removal mechanism.
4. Confirm a preferred HTTPS hostname and redirect its alternate at the actual
   VPS reverse proxy, retaining paths and relevant query parameters. Inspect
   proxy scheme forwarding before enabling application-level HTTPS redirects to
   avoid loops. The public-site proxy configuration is not supplied in this repo;
   `src/docker/media-nginx.conf` only serves media.
5. **Google ownership setup: complete for planning; confirmation pending.** Once
   Google confirms verification, check access and export existing indexing and
   performance reports if available to record a dated baseline. Set up Bing
   Webmaster Tools separately, importing the verified Google property when
   available. Keep these account follow-ups separate from technical delivery;
   do not wait for verification propagation to prepare SEO changes.

Acceptance:

- Public production HTML has no accidental noindex directive, including headers;
  staging/utility behavior remains intentional and tested.
- Preferred/alternate hostname checks are correct without redirect loops.
- Google URL Inspection can retrieve representative full pages and read assets.
- Access controls remain intact; crawler directives are not substituted for auth.

Verification-dependent checks, report exports, and sitemap submissions are
operational follow-ups once account access is available. While Google's
confirmation is pending, validate technical work with automated tests and public
HTTP checks and retain the account checks as tracked follow-ups. This planning
status does not claim that Google has verified or indexed the site.

### Phase 2 — Improve search snippets, sharing, and crawl consistency

Priority: **P1**. Indicative technical effort: 2–4 days.

1. Add a shared SEO context/helper with plain-text, escaped descriptions and
   verified absolute URLs. Prefer a configured public origin over untrusted
   request-header construction. Normalize campaign parameters out of canonical
   URLs; retain meaningful content differences such as genuine pagination.
2. Add route-specific title/description blocks and self-canonicals. Examples:
   - Home: `Spokane Tech Events, Meetups & Groups | SpokaneTech`.
   - Events: `Upcoming Tech Events in Spokane | SpokaneTech`.
   - Group: `<actual group name> — Spokane Tech Community | SpokaneTech`.
   - Event: `<actual event name> — <actual local date> | SpokaneTech`.
   Descriptions should reflect actual content, not keyword lists or invented
   attendee counts. Titles/descriptions influence presentation; Google can rewrite
   snippets and no placement is guaranteed.
3. Add Open Graph and social-card fields with event imagery when appropriate,
   a stable project-owned fallback image, image descriptions, and absolute HTTPS
   URLs. Verify image accessibility from the media service. Choose preview sizes
   after checking actual assets instead of inventing dimensions.
4. Redirect genuinely duplicate full-page aliases to preferred URLs while
   preserving supported HTMX/minimal routes. Preserve existing numeric event and
   group permalinks; descriptive slugs are not the first priority.
5. Treat filtered/empty/topic/calendar views deliberately. Start by keeping
   arbitrary filters and dated calendar grids out of search results; keep a useful
   canonical directory as the search landing page. Do not canonicalize materially
   different content to an unrelated page merely to suppress it.
6. Add Django's built-in sitemap support with only canonical, indexable URLs.
   Include enabled public groups and suitable upcoming event pages, not fragment
   endpoints, query combinations, disabled groups, or every possible month.
   Retain useful past/cancelled event permalinks with visible status and relevant
   next-event links rather than redirecting all old events to the homepage.
   Use truthful content-change timestamps for `lastmod`, not every ingestion poll
   or sitemap request. Audit existing `updated_at` writes before relying on them.
7. Update titles and other necessary document metadata on HTMX navigation and
   history restoration while preserving correct server-rendered head content on
   a direct request. Validate cache variation for `HX-Request` so crawlers and
   visitors cannot receive a cached fragment as a full page.

Acceptance:

- Distinct event/group pages have accurate metadata, one preferred canonical, and
  equivalent content on direct and enhanced navigation.
- Sitemap URLs return the expected successful full page, not an alias/fragment;
  sitemaps are valid, bounded, and submitted through the verified tools.
- Real social-preview checks show useful titles and images. Existing navigation,
  filters, calendar, modals, and links still work.

### Phase 3 — Describe real events to search engines and improve content value

Priority: **P1/P2**. Indicative effort: 2–4 technical days plus editorial review.

1. Emit safely serialized Event JSON-LD on individual eligible event pages only.
   Use real name, description, start/end times with correct UTC offsets, image,
   organizer, URL, and known location. Preserve cancellation status using the
   appropriate schema value. Serialize untrusted source text without creating
   executable markup or breaking a script element.
2. Do not fabricate ticket prices, availability, venue coordinates, postal codes,
   age restrictions, or organizer identities. The model lacks verified pricing,
   structured address components, and explicit public-admission/attendance flags.
   Assess source coverage before proposing optional fields or a migration. Omit
   unverifiable optional data; omit event-rich-result markup when required data
   or eligibility cannot be established.
3. Google currently requires a physical component and public bookability for its
   event experience. A virtual-only or members-only meetup can remain a useful
   page without qualifying for that feature. Do not invent a Spokane venue for
   online events. Valid schema alone does not guarantee a rich result.
   [Event eligibility rules](https://developers.google.com/search/docs/appearance/structured-data/event#guidelines).
4. Add truthful Organization/WebSite identity and breadcrumbs where they match
   visible content. Use only verified project profiles for `sameAs`; do not imply
   that SpokaneTech owns organizers' venues or is the organizer of every listing.
5. Improve group introductions through organizer-approved, first-hand summaries:
   audience, topics, meeting format, accessibility information when confirmed,
   and how a newcomer can participate. Keep original source attribution and
   direct RSVP links. Avoid competing with providers through copied volume alone.
6. Validate representative physical, virtual, cancelled, missing-image, and
   missing-location records. Any future rescheduling markup must use real history;
   `change_version` alone is not evidence of a previous start time.

Acceptance:

- Google Rich Results Test has no critical errors for eligible samples; visible
  text and structured data agree. Ineligible samples are handled honestly.
- Missing data does not result in bogus free tickets, addresses, dates, or events.
- Ingestion updates and cancellations remain reflected on public pages.

### Phase 4 — Measure useful actions before expanding distribution

Priority: **P1**, can run alongside phases 2–3. Effort: 1–2 days plus GA4 access.

1. Validate exactly one intended page view for a full load, HTMX navigation, and
   back/forward navigation. Inspect enhanced-measurement history tracking before
   adding manual page views. Set the correct page title and location; exclude
   modal opens from page-view inflation unless they represent distinct pages.
2. Define a small, documented event vocabulary: `rsvp_click`,
   `community_link_click`, and, if implemented, `calendar_subscribe`/`share_click`.
   Group-detail visits are engagement measures, not completed group memberships.
   Reuse existing outbound measurement where suitable instead of counting the
   same interaction twice. Restrict parameters to necessary public identifiers;
   never send credentials, email addresses, or sensitive query values.
3. RSVP clicks and Discord/community outbound clicks are **intent proxies**, not
   verified attendance, completed RSVPs, or accepted group invitations. Confirmed
   participation needs separate organizer feedback or an explicitly designed
   integration; do not represent clicks as completed conversions.
4. Standardize outbound promotion links using source/medium/campaign parameters.
   Example, after confirming the preferred domain:

   ```text
   https://www.spokanetech.org/events/list?utm_source=linkedin&utm_medium=organic_social&utm_campaign=weekly_events
   ```

   Use distinct partner sources and an offline source for QR cards. Do not add
   UTM parameters to internal navigation or fragment canonicals.
   [Google campaign URL guidance](https://support.google.com/analytics/answer/10917952).
5. Build a lightweight weekly dashboard from Search Console and GA4, with a
   28-day pre-change baseline where available. If historical data is missing,
   start the baseline after instrumentation validation and label that limitation.

Acceptance: DebugView/realtime checks and navigation tests demonstrate accurate,
nonduplicated actions; campaign URLs preserve functionality and attribution;
privacy documentation matches any measurement changes. No new marketing-email
collection, advertising pixels, or invasive tracking is included.

## 4. Organic distribution and content program

Start after the relevant destination pages and measurement pass their release
gates. Channel activity below is a proposal, not permission to contact anyone.

### A. Verify identity and launch one primary channel

- Inventory the existing Discord, LinkedIn, Facebook, and GitHub links in
  `core/context_processors.py`. Verify ownership, valid invites, branding, and
  management access before promoting them or including them in identity schema.
  Correct or retire unverified destinations only after owner confirmation.
- Recommend LinkedIn as the first channel to test for the local professional
  audience, provided the project can establish an owned page. This is a working
  audience hypothesis, not a claim of proven reach or a required account purchase.
- Introduce the site through relevant existing communities with moderator consent
  rather than creating another Discord server by default. Choose a second owned
  channel only when a maintainer can sustain it.
- Update verified profiles to point to the canonical site and explain the value:
  one place to discover local tech events and communities.

### B. Publish a useful weekly roundup

- Once per week, share a short, human-reviewed selection of real upcoming events:
  event name, date, host, topic, and a clear link to discover details on SpokaneTech.
  Check ingestion freshness, local timezone boundaries, cancellations, and
  duplicate records before posting. Avoid AI-generated claims or stale schedules.
- Adapt the existing notifier/digest code after a channel is approved: offer a
  SpokaneTech detail link with campaign attribution and preserve an explicit
  direct RSVP route. Do not force an intermediate redirect on people who only
  want the organizer's event page. Compare meaningful actions, not raw page views.
- Preserve `POST_TO_DISCORD`, `POST_TO_LINKEDIN`, credential handling, version checks,
  and cancellation behavior. Confirm Beat schedules, rate/length limits, and
  retry/idempotency behavior before enabling any automatic publishing. The existing
  task registration is not proof that a production schedule is configured.
- Begin with manual approval of posts. Automate only after a few reliable cycles.

### C. Recruit referral partners, not purchased links

Suggested first experiment: a maintainer contacts five relevant organizers or
resource owners over a month, using personalized requests and an explicit owner
approval for outreach. Five is an operational target, not a forecast of results.

- Start with organizers already represented in seed data, such as Spokane Python,
  .NET, Rust, Go, DevOps, and UX communities; confirm which are active in current
  application data. Ask for corrections and permission to share their public
  events, then offer a relevant group-page link for their resource pages or slides.
- Explore mutual usefulness with local resource owners, not assumed partnerships:
  [EWU computing clubs](https://www.ewu.edu/cstem/csee/clubs/),
  [Gonzaga career events](https://www.gonzaga.edu/student-life/career-services/about-us/cpd-events-listing),
  and [Greater Spokane Inc.'s events/resources](https://web.greaterspokane.org/).
  These sources establish relevance only; no relationship or acceptance is implied.
- For startup-focused overlap, evaluate the existing local calendar operated by
  [StartUp Spokane/Spokane Public Library](https://www.spokanelibrary.org/wp-content/uploads/StartUp-Spokane-Launches-Comprehensive-Business-Events-Calendar.pdf)
  before proposing a cooperative listing. The announcement is historical; confirm
  current ownership, scope, and submission rules before using it.
- Offer a small QR/link card for event slides: "Find your next Spokane tech event."
  Use a stable, relevant destination and campaign tagging; no printing budget is
  assumed. Measure referred sessions and useful actions per partner.
- Do not buy backlinks, require manipulative reciprocal-link exchanges, or post
  repeated promotional messages to communities without moderator approval.
  [Google spam policies](https://developers.google.com/search/docs/essentials/spam-policies).

### D. Add a small set of first-party, locally useful pages

Start with two maintained pages, not a large publishing calendar:

1. A newcomer guide to finding a first Spokane tech meetup, with links to real
   groups and an automatically maintained upcoming-event selection.
2. A human-reviewed overview of local developer communities by topic, linking to
   the actual group profiles and including beginner/experience expectations only
   when verified with organizers.

After reviewing search queries and user feedback, consider a curated topic hub
such as Python meetups or AI events. Create it only when there is enough real,
maintained content to serve visitors. Render topic links as useful anchors; do
not make every sparse tag or city/topic combination indexable automatically.
Queries such as "Spokane tech events" and "Spokane programming meetups" are topic
hypotheses; no keyword volume or ranking difficulty has been measured.

Keep externally sourced developer-blog cards attributed and linked to their
original publications. Do not duplicate those articles as first-party content
just to increase page count. Keep the attendee goal distinct from the developer
contribution funnel on `/develop/`.

## 5. Return visits and performance — later, evidence-led work

- Add event sharing/copy-link controls after metadata is ready. Sharing should
  work without introducing a mandatory social login or third-party widget bundle.
- Evaluate RSS and/or iCalendar subscriptions as a low-maintenance return path
  without collecting email. A calendar feed needs stable UIDs, correct timezones,
  updates, and retained cancellation notices; an active-upcoming-only feed can
  leave stale events in subscribers' calendars. Scope this separately and test it.
- Keep the existing WebP processing and lazy loading. Use a real mobile performance
  trace to decide whether responsive event-image variants, LCP prioritization,
  compression, cache headers, or third-party asset reduction will help.
- Measure homepage, directory, and detail templates separately. Use field data
  where available and lab tests when traffic is too small for field reports.
  Aim for good Core Web Vitals; do not promise rankings or claim performance
  failures from file sizes alone. [Google page-experience guidance](https://developers.google.com/search/docs/appearance/core-web-vitals).
- Do not create a Google Business Profile merely because the site mentions a city:
  online-only organizations and some ongoing meetings at third-party venues are
  ineligible. Assess a genuine eligible in-person operation first, if one exists.
  [Google Business Profile eligibility](https://support.google.com/business/answer/13763036).
- A newsletter would be a separate product and operational decision requiring
  opt-in, unsubscribe handling, ownership, provider costs, and policy updates.
  It is not part of this organic-first implementation proposal.

## 6. Proposed affected files and deliverables

Exact implementation details are subject to approval of each batch. Paths marked
"new" do not exist yet. Existing model/schema changes are not a prerequisite for
phase 1; any structured-data model extension needs its own migration review.

| Batch | Likely affected files/resources | Main checks |
| --- | --- | --- |
| Indexability/origin | `src/django_project/core/settings.py`, `core/context_processors.py`, `core/views.py`, `core/urls.py`, `core/templates/base.htm`, `src/envs/.env.template`, actual VPS proxy configuration and deployment docs | Production/staging and public/utility route matrix; header/meta behavior; HTTPS/domain redirect loops; existing access control. |
| Metadata/canonicals | New `src/django_project/web/seo.py` or equivalent shared helper; `web/views.py`, `web/urls.py`, full and partial templates, `core/templates/base.htm`, `core/static/spokanetech/js/navigation.js` | Real data escaping, direct/full/HTMX/history equivalence, aliases, meaningful filters, share previews, cache variation. |
| Sitemap | New `src/django_project/web/sitemaps.py`; `core/urls.py`, applicable settings, robots response; no new third-party sitemap package needed | Valid XML; correct origin/lastmod; bounded, public, enabled, canonical records; correct status codes. |
| Event schema | SEO/serialization helper and detail templates; optional future `web/models.py`/ingestion changes only after source-data assessment | Safe JSON, timezones, cancellation updates, incomplete/ineligible data, visible-content parity, Rich Results Test. |
| Analytics | Base template, navigation/tracking JS, event/group/action links, GA4/Search Console settings, privacy text if practices change | One intended page view; accurate outbound attribution; no PII; no modal inflation or double counting. |
| Organic publishing | `web/utilities/notifiers/discord.py`, `linkedin.py`, `web/tasks.py`, applicable tests; approved profile ownership and schedules | Existing opt-outs, duplicate/retry guards, source RSVP preserved, freshness/cancellations, campaign URLs, no live test messages. |
| Helpful content/referrals | New approved guide/topic templates and routes; current tag partial; editorial/source records; manually maintained outreach sheet and optional share assets | Useful original material; active real groups/events; source attribution; relevant links; owner-approved outreach. |
| Optional subscriptions/performance | Separately scoped `web/feeds.py`/routes, optional image variants and static delivery configuration | Stable feed updates/cancellations; mobile traces; existing media safety/storage; measured improvement. |

Paths abbreviated as `core/...` or `web/...` above are under
`src/django_project/`. Proposed tests belong under `src/django_project/tests/` and
should exercise behavior and regressions rather than mirror helper internals.

## 7. Rollout, owners, and measurement

| Window after approval | Technical owner | Community/site owner | Exit condition |
| --- | --- | --- | --- |
| Week 1 | Indexing controls, hostname/redirect review, initial baseline | Confirm accounts, domain, data visibility rules, profile ownership | Representative public pages crawlable; no unintended utility/staging exposure. |
| Weeks 2–3 | Metadata, sitemap, sharing previews, analytics validation; eligible event schema | Validate listings and snippets; establish one owned channel | Tests pass; sitemap accepted; previews and measured actions verified. |
| Weeks 3–6 | Safe notification-link improvements and small content support | Weekly roundup; first organizer/resource outreach; two useful guides | Sustainable publishing cadence and attributable referrals. |
| Weeks 6–12 | Fix issues identified by indexing/field reports | Compare channels and queries; refresh guides; decide whether subscriptions help | Continue only the activities producing useful discovery/engagement. |

This sequence is dependency-based, not a promise of search ranking changes within
these weeks. Assess search results over several weeks; crawling and indexing
can lag deployment. [Google's timing guidance](https://developers.google.com/search/docs/fundamentals/seo-starter-guide#how-long-until-i-see-impact-in-search-results).

### Weekly scorecard

| Metric | Source | Interpretation |
| --- | --- | --- |
| Eligible/canonical pages discovered and indexed; exclusion reasons | Google Search Console and Bing Webmaster Tools | Index coverage and problems, not guaranteed traffic. |
| Non-branded local-query impressions, clicks, CTR, and landing pages | Search Console; manually reviewed local-topic query grouping | Discoverability for useful searches, rather than only brand recognition. |
| Qualified sessions by organic search, partner, and social campaign | GA4 acquisition reports | Compare channels using consistently named campaigns; verify available geographic reporting before using it. |
| Sessions with RSVP/community outbound intent; action rate | Validated GA4 events and session reporting | Intent proxies; report separately from confirmed membership/attendance. |
| Returning visitors and useful guide/group engagement | GA4, subject to consent and measurement limitations | Whether people find recurring value. |
| Active verified referral placements and their useful actions | Maintainer outreach sheet + campaign reports | Partner quality, not a raw link-count target. |
| Broken links, stale/cancelled listings, and ingestion freshness | App checks and maintainer/organizer feedback | A traffic gain is not useful if visitors see incorrect information. |

Set numerical growth targets after collecting a trustworthy baseline. Do not
invent current traffic, promise ranking positions, or optimize for followers and
page views without useful actions. No paid advertising experiment is scheduled.

## 8. Validation and approval checklist

Before approving an implementation batch, review its concrete changes, affected
files, tests, and operational ownership. Before deployment:

- Test indexability for the preferred host, alternate host, staging, static public
  pages, enabled/disabled groups, upcoming/past/cancelled events, empty/filter
  results, historical calendars, modals, and minimal responses.
- Verify 404/deleted-record behavior and existing deep links. No blanket redirect
  of removed content to unrelated pages; no mass deletion of historical events.
- Confirm fresh full HTML contains real event/group content without JavaScript.
- Validate sitemap and JSON-LD, malicious source text escaping, absolute URLs,
  image accessibility, and current metadata on full/HTMX/history navigation.
- Run applicable unit/regression, Django, type, lint, and security checks. Notification
  tests must mock providers; do not send test messages to real communities.
- Have the owner perform Search Console, Bing, preview, and GA4 checks with proper
  access. These account changes are not implied by code review.
- Check production HTML/headers after deployment, then monitor indexing reports
  and error rates. Maintain a rollback for application and proxy changes. Keep
  development/staging safeguards if rolling back public indexing behavior.

**Release next step:** review and deploy the prepared repository changes using
the [rollout guide](SEO_IMPLEMENTATION_AND_ROLLOUT.md), then complete the
account-side checks. Confirm ownership and permissions before enabling organic
distribution. Google ownership setup remains complete for planning while its
verification confirmation is pending.
