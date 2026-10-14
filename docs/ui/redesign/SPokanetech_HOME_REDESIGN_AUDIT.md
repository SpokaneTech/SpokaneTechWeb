# SpokaneTech homepage audit and implementation

Completed October 8, 2026. Read alongside `SPokanetech_HOME_REDESIGN_PLAN.md`.

## Phase 1: findings recorded before implementation

- No applicable `AGENTS.md` files were found in the repository or ancestor directories. Read `.github/CONTRIBUTING.md` and `.github/STYLE_GUIDE.md`.
- Existing user edits in README, pyproject, models, settings, URLs, deployment files, and the supplied redesign documents were preserved. The only redesign addition to the already edited settings file is a context-processor registration.
- Both `/` and `/index/` resolve to `web.views.IndexContentView`, a django-handyhelpers `HtmxOptionView`.
- A normal request used `web/full/custom/index.html`, extending `core/templates/base.htm`. Its empty `#body_main` loaded `web/partials/custom/index.htm` through HTMX, and that partial made another HTMX request to `/events/minimal`.
- The original page offered About and Develop buttons, an upcoming-event list, Events/Groups/Calendar navigation, and Discord/GitHub/LinkedIn/Facebook links in the footer. Event rows linked to their external source. Internal event detail pages already expose the source link.
- The base template owns analytics, metadata, Bootstrap modals, HTMX, jQuery, Popper, and Bootstrap scripts. Existing HTMX navigation targets `#body_main` and pushes URLs. Authentication routes, ingestion integrations, and monthly calendar/modal behavior are separate and remain in place.
- Styling uses Bootstrap 5 and Font Awesome from the local static `node_modules` directory. `spokanetech.scss` imports Bootstrap and compiles to committed `spokanetech.css`. There is no frontend framework or required homepage JavaScript build.
- `Event` has start/end datetimes, optional group, image, tags, source URL, and venue fields. `TechGroup` has `enabled`, image, Font Awesome icon, tags, and links. Both already provide internal detail URLs. No schema change is needed.
- Existing event queries include all events starting at or after the current instant, including ungrouped events. That scope is retained. `enabled=True` defines the homepage's active groups, matching the directory.
- Middleware activates `America/Los_Angeles`; all dates must preserve that timezone, including PST/PDT and local calendar dates.
- Social URLs were embedded in the footer, rather than centrally configured. No public search or Resources page exists. There is an About page and a Develop page.
- Reusable partial conventions already exist for event/group lists, detail content, and modals. New homepage cards use the same include convention without changing internal-page card layouts.
- Metadata includes a description, Open Graph fields, favicon links, and the existing `noindex, nofollow` directive. No canonical or structured-data implementation was found in the homepage/base templates. Existing metadata and robots behavior were preserved.
- Reviewed the main reference, the equivalent `SpokaneTech Community Landing Page.png` reference, and both supplied artwork originals. The mockup is a hierarchy/style reference; its sample events, groups, and counts are not application content.

### Baseline verification

The default pytest run stopped at the first existing failure. A complete baseline run with fail-fast disabled finished with **117 passed, 3 failed**:

1. `/events/li` returned 400.
2. `/events/list` selected the compact partial instead of the existing list template.
3. `/techgroups/marquee` returned 400.

The installed handyhelpers view requires recognized display modes and explicit list-template selection. These were small compatibility discrepancies between existing view attributes/routes and the current dependency.

The first browser capture exposed missing local HTMX, jQuery, Font Awesome, and animation assets. Existing copies were restored from `staticroot` into the ignored local dependency directory; no dependency or package definition changed. The working baseline was then captured at 1280px and 360px. It showed two upcoming events from the existing database snapshot, two homepage h1 elements, and no horizontal overflow.

## Proposed changes communicated before editing

- Add bounded real-data queries to the existing homepage view; repair the three event/group display compatibility failures.
- Server-render the initial homepage, keeping the same partial for HTMX navigation.
- Add event, group, and tag partials, then the supplied hero, upcoming events, enabled groups, illustration/topics, live statistics, and involvement sections in that order.
- Update the shared header/footer and keep existing routes, scripts, analytics, modals, and social destinations.
- Add consolidated design tokens and homepage-scoped CSS rather than recompiling or globally replacing the established Bootstrap theme.
- Generate optimized static image derivatives, retaining the supplied PNG originals under `docs/ui/redesign`.
- Centralize public social links in a context processor with optional settings overrides.
- Add homepage regression coverage and save QA evidence.

## Final files affected

| Files | Purpose |
| --- | --- |
| `src/django_project/web/views.py` | Homepage queries and existing display-route compatibility |
| `src/django_project/web/utilities/icons.py` | Extract current/legacy Font Awesome classes without rendering stored HTML |
| `src/django_project/web/templates/web/full/custom/index.html` | Initial server render and retained HTMX history container |
| `src/django_project/web/templates/web/partials/custom/index.htm` | Six homepage sections |
| `src/django_project/web/templates/web/partials/home/{event_card,group_card,tags}.htm` | Reusable cards and database tags |
| `src/django_project/core/templates/base.htm` | Dark shared navigation/footer, real hrefs, menu labels, skip link |
| `src/django_project/core/context_processors.py` | Shared existing public community links |
| `src/django_project/core/settings.py` | Register that processor; preserve prior edits |
| `src/django_project/core/static/spokanetech/css/homepage.css` | Tokens and scoped responsive presentation; directly served CSS |
| `src/django_project/core/static/spokanetech/js/navigation.js` | Close the existing Bootstrap mobile menu after HTMX navigation |
| `src/django_project/core/static/spokanetech/js/group-carousel.js` | Native group scrolling, arrow controls, keyboard navigation, and HTMX lifecycle support |
| `src/django_project/core/static/spokanetech/img/*spokane*.{webp,jpg}` | Five optimized derivatives of the two supplied originals |
| `src/django_project/tests/unit/web/test_homepage.py` | Data, time, links, empty-state, authentication, icon, and query tests |
| This document and `qa/*.jpg` | Audit and before/after review evidence |

## Implementation decisions

- Four chronologically ordered future events, with deterministic ordering for equal timestamps. The nearest event is labeled **Next event**. Total upcoming counts include all matching records, not just the displayed cards.
- All enabled groups ordered by name in a horizontal carousel, with upcoming counts annotated in one query. Images take precedence over group icons, with initials as the final fallback.
- Group icons in existing data often contain legacy `<i>` HTML. Only Font Awesome CSS classes are extracted; arbitrary markup, event handlers, and unrelated classes are discarded.
- Event cards link to existing internal detail pages, where users can access the original event source. Group labels inside cards are plain text to avoid nested links. The existing event/group list and calendar/detail/modal routes remain available.
- Missing event photography uses a navy code-symbol/group-name fallback. No stock photography or invented event metadata is used.
- Community pills come only from enabled groups or upcoming events, deduplicated and capped at twelve. Event/group tags use prefetched relations.
- Anonymous populated homepage rendering uses at most seven data queries. A regression test checks that this bound does not grow as the card counts increase. Anonymous and authenticated rendering both pass.
- Public community links retain the original destinations. Deployments can set `COMMUNITY_DISCORD_URL` and `COMMUNITY_SOCIAL_LINKS`; empty values omit those links. Integration webhook/token settings are never used as public URLs.
- Dates include year and Pacific timezone; semantic timestamps include the local UTC offset. Multi-day events include the end date.
- No migration, model change, frontend framework, or dependency change was introduced by the redesign.
- The existing theme and unused legacy hero rules remain untouched so internal pages can migrate separately.

### Image derivatives

| Asset | Dimensions | Approximate size |
| --- | --- | --- |
| Desktop hero WebP | 1920 × 768 | 299 KiB |
| Mobile hero WebP | 960 × 384 | 98 KiB |
| Desktop hero JPEG fallback | 1920 × 768 | 357 KiB |
| Illustration WebP | 1100 × 367 | 49 KiB |
| Illustration JPEG fallback | 1100 × 367 | 69 KiB |

Pillow, already a project dependency, produced WebP at quality 82/method 6 and optimized JPEG at quality 82. The hero loads through CSS with a JPEG fallback and a smaller mobile source. The illustration uses a lazy-loaded picture with explicit dimensions. Originals remain unchanged in the redesign directory.

## Final QA

- **130 tests passed, plus 8 subtests.** Includes the ten new homepage tests and all three repaired baseline failures.
- Django system check: no issues.
- Changed production Python files: Ruff lint/format, isort, mypy, and Bandit passed. `git diff --check` passed. isort uses `--src-path src/django_project` to recognize the repository's application imports.
- Chromium browser checks at **360, 390, 430, 768, 1024, 1280, and 1440px**: all sections fit; no page overflow, failed HTTP responses, missing assets, or JavaScript errors.
- Verified keyboard skip link, menu toggle and expanded state, visible focus, menu closing after navigation, existing HTMX URL push, back/forward history, reduced-motion styling, and initial homepage/navigation with JavaScript disabled.
- Verified illustration loading and inspected mobile/desktop screenshots. Explicit image dimensions reserve layout space. No obvious layout shift was observed.
- Exercised four-event layouts and long unbroken titles/topics using browser-only DOM copies, with no overflow at mobile, tablet, laptop, and desktop widths. Production queries/templates contain no mock data.
- Unit tests verify empty events/groups, no unused/inactive tags, real internal links, event ordering and limits, live total/group counts, PST/PDT rollover, authenticated rendering, optional community links, and safe icon normalization.
- Checked representative normal-text color pairs: blue button/white text 5.17:1; muted text/white 6.13:1; section eyebrow/light background 5.60:1; tag text/background 9.46:1. Dark surfaces use light text; mobile hero imagery has a strong overlay. Focus rings use blue on light surfaces and cyan on navy surfaces.

Reproduce the server-side suite from the repository root:

```bash
ENV_PATH=src/envs/.env.test venv/bin/python -m pytest
ENV_PATH=src/envs/.env.test venv/bin/python src/django_project/manage.py check
```

Browser verification used a temporary copy of `spokanetech_test_restore.sqlite3`, containing real application records. Existing databases were not migrated or edited. Screenshots reflect that snapshot's data and the audit date; their counts are not production constants.

### Review screenshots

- Before: [desktop](qa/before-1280.jpg), [mobile](qa/before-360.jpg)
- After: [360px](qa/after-360.jpg), [768px](qa/after-768.jpg), [1280px](qa/after-1280.jpg), [1440px](qa/after-1440.jpg)

## Intentional differences and follow-up

- Keep the existing wordmark, Calendar, About, and Develop routes. Omit Resources and search because there is no suitable existing implementation.
- Use actual group icons/tags and actual event imagery or fallbacks, rather than sample technology logos and meetup photos from the reference.
- Show two meaningful live metrics; omit the reference's decorative third community count.
- Show fewer event cards when fewer upcoming records exist. An empty state links to Groups and Calendar.
- No remaining work is required for this homepage implementation. Search, Resources, and migration of internal-page content to the new visual system are separate optional iterations.

## Subsequent static-assets review

Third-party packages now load from pinned CDNs rather than handyhelpers' local
`node_modules` directory. The theme source no longer imports Bootstrap Sass,
and its compiled CSS/source map contain only application theme rules. Bootstrap
was retained; no framework switch was made. See
[the static assets review](STATIC_ASSETS_REVIEW.md) for the delivery inventory,
validation, and a separate calendar context-compatibility finding.

## Subsequent group carousel update

The community section now shows all enabled groups in one horizontally scrollable
row. It keeps the existing cards and detail links, adds left/right page controls,
and uses native CSS scrolling with card snapping. Mobile shows a partial next
card to make the horizontal interaction apparent. Keyboard users can focus the
region and use arrows, Home, or End; tabbing still reaches individual group links.
There is no automatic rotation. Reduced motion disables animated button scrolling.
Native scrolling remains available when JavaScript is disabled, and enhancement
controls initialize after HTMX swaps and history restoration.

Removed the six-group query limit; annotations and tag prefetching keep the
homepage query count at the same bound. The regression test now checks all ten
enabled groups in its expanded fixture, including groups beyond the old limit,
while excluding disabled groups. Homepage tests: **10 passed, 8 subtests passed**.
Ruff, isort, JavaScript syntax, and diff checks passed.

Browser checks passed at 360, 390, 430, 768, 1024, 1280, and 1440px with the
snapshot's 24 enabled groups. Verified a single card row, no page overflow,
first/last group reachability, control boundary states, keyboard scrolling,
reduced motion, HTMX swap/history behavior, native horizontal mouse scrolling
with scripts disabled, and a mobile touch swipe.

Previews: [desktop carousel](qa/group-carousel-1280.png),
[mobile carousel](qa/group-carousel-360.png).

## Subsequent color palette consolidation

The shared Sass theme now defines the action blue (`#2563EB`), action hover/pressed
blue (`#1D4ED8`), accent for dark surfaces (`#91C4FF`), and one pale-blue tint
(`#E5EEFB`). It emits shared CSS tokens consumed by the homepage and aligns
Bootstrap's primary buttons, links, and component colors with the same palette.
Compiled CSS and the source map were regenerated without package dependencies.

The wordmark, dark navigation hover, social icons, and hero accents use the same
light blue. Buttons and links on light backgrounds use the action colors.
Secondary metadata and eyebrows use slate; tags and pale-blue surfaces share one
tint. Removed the cyan accent, individual light-blue values, and alternating tag
colors. Supplied imagery and real group images remain unchanged.

Chromium verified computed colors, primary/outline Bootstrap button states,
header hover, social hover, dark/light focus rings, and layouts at 360, 768,
1280, and 1440px. No JavaScript errors were observed. Text contrast checks passed:
white on action blue 5.17:1, white on hover blue 6.70:1, light accent on navy
9.82:1, slate on the pale-blue surface 5.24:1, and tag text on that surface
15.26:1. Sass compilation and `git diff --check` passed.

Previews: [desktop palette](qa/palette-1280.png), [mobile palette](qa/palette-360.png).

### Subtle blue accents restored

After visual feedback, restored the existing dark action-blue token to eyebrows,
event/group labels, upcoming counts, and tag text, and the existing light accent
to group labels on featured dark cards. No new accent hue was introduced. The
community section uses a 40% mix of the existing pale-blue tint with white for a
lighter backdrop. Headings and paragraph copy keep their neutral colors.

Browser checks passed at 360 and 1280px. Accent text contrast is 6.70:1 on white,
5.73:1 on tag backgrounds, and 6.30:1 on the lighter community background.
Previews: [desktop](qa/subtle-blue-1280.png), [mobile](qa/subtle-blue-360.png).

## Group directory redesign

The groups list now shares the homepage typography, subtle blue palette, and
card component. A left-aligned introduction and live group total lead into a
responsive four/three/two/one-column grid. Cards use stored logos or normalized
icons, plain-text description excerpts, upcoming event counts, and existing tags.
Missing descriptions are omitted rather than replaced with invented content.
Semantic headings and real detail links support keyboard navigation and HTMX.

Affected application files: `web/views.py`, `web/utilities/html_utils.py`,
`web/templates/web/full/list/groups.html`, the list partials `groups.htm` and
`wrapper_list.htm`, shared `home/group_card.htm`, and `homepage.css`. The full
page renders its directory immediately, including when JavaScript is disabled.
Existing routes, query filters, HTMX response headers, and history remain intact.
Upcoming counts are annotated and tags prefetched; directory data takes two
queries regardless of group count. No migrations or dependencies were added.
Search and topic-filter controls remain a later enhancement, as proposed.

Validation: **137 tests passed, 10 subtests passed**. New directory tests cover
full/partial rendering, safe excerpts, actual stored data, disabled groups,
empty states, filtering, authentication, and query growth. An existing homepage
assertion was aligned with the current event CTA. Ruff, formatting, isort,
targeted mypy and Bandit checks, and `git diff --check` passed.

Chromium checks passed at 360, 390, 430, 768, 1024, 1280, and 1440px using a
local copy of the application's 24 enabled groups. Verified no page overflow,
keyboard detail navigation, back history, HTMX Groups navigation, homepage card
reuse, empty filtered results, and initial rendering without scripts. No
JavaScript errors or failed requests were observed.

Previews: [desktop directory](qa/group-directory-1280.png),
[mobile directory](qa/group-directory-390.png).

## Event directory redesign

The event list now shares the directory introduction, live result count, subtle
blue palette, and homepage event cards. Events remain chronological, with a
three/two/one-column responsive grid. Cards show stored event imagery, group
imagery or the existing fallback, date badges, organizers, start/end times in
the application's timezone, available locations, and up to three stored topics.
The directory variant uses h2 titles and real detail links enhanced with HTMX;
the homepage keeps its featured card and h3 titles. No mock content was added.

Affected files: `web/views.py`, `web/templates/web/full/list/events.html`,
`web/templates/web/partials/list/events.htm`, shared `home/event_card.htm`,
`homepage.css`, and new `tests/unit/web/test_event_directory.py`. Initial pages
render their content directly. Existing query filters, minimal list display,
detail routes, HTMX headers, and history are preserved. Group joins and tag
prefetching bound the directory data to two queries as the list grows. The
empty state links to the groups directory. No migrations or dependencies.

Validation: **142 tests passed, 12 subtests passed**. Event regression coverage
checks full/partial rendering, real event metadata, ordering, past-event
exclusion, filters, minimal display, missing-data fallbacks, empty results, and
query growth. `mypy src` passes for all 68 files. Ruff, formatting, isort, and
`git diff --check` pass.

Chromium checks passed at 360, 390, 430, 768, 1024, 1280, and 1440px using the
copied application's two upcoming events. Verified grid columns, no overflow,
chronological dates, keyboard detail links, back history, homepage card reuse,
HTMX Events navigation, empty-state group navigation, and initial rendering
with JavaScript disabled. No JavaScript errors or failed requests occurred.

Previews: [desktop events](qa/event-directory-1280.png),
[mobile events](qa/event-directory-390.png).

## Tech group detail redesign

Group detail pages now share the directory palette, typography, spacing, and
cards. A group logo/icon/initial header includes stored topics and a link back
to all groups. About content retains the existing rich description; a Connect
panel displays stored community links when available. Missing descriptions and
events have explicit empty states. No mock community or event data was added.

Upcoming events reuse the homepage cards with date badges, images or existing
fallbacks, times, locations and addresses, topics, and internal detail links.
Original event website links remain separately available. Past events use a
compact newest-first list with dates, times, locations, detail links, and source
websites. All upcoming and past records remain available, with no nested scroll
areas. Semantic headings and keyboard focus styles replace click-only content.

Affected files: `web/views.py`, `web/templates/web/full/detail/group.html`,
`web/templates/web/partials/detail/group.htm`, shared `home/event_card.htm`,
`homepage.css`, and new `tests/unit/web/test_group_detail.py`. Initial content
renders directly; HTMX detail navigation and browser history are preserved.
Legacy icons use the same normalized class parser as the directory. Related
group links/topics and event topics are prefetched, and a single timestamp
separates upcoming and past events. Rendering takes five data queries regardless
of event/link count. No migrations or dependencies were added.

Validation: **147 tests passed, 14 subtests passed**. Tests cover full and HTMX
content, retained rich descriptions and real links, icon normalization, event
ordering and isolation, empty sections, logo images, missing groups, and query
growth. `mypy src` passes for all 69 files. Ruff, formatting, isort, and diff
checks pass.

Chromium verified the Python group at 360, 390, 430, 768, 1024, 1280, and 1440px,
including its full description, community links, and all 21 past events. A
second real group verified upcoming cards at desktop, tablet, and mobile widths.
Checks cover no overflow, date ordering, keyboard event navigation, HTMX
directory/detail navigation, back history, and rendering without JavaScript.
No JavaScript errors or unexpected request failures; font requests canceled by
navigation are excluded from request-failure assertions.

Previews: [desktop group detail](qa/group-detail-1280.png),
[mobile group detail](qa/group-detail-390.png),
[group with upcoming events](qa/group-detail-upcoming-1280.png).

### Tighter detail layout and event tabs

Upcoming and past events now occupy separate tabs with live counts. Upcoming
is selected initially; keyboard arrows, Home, and End switch tabs. Tab panels
have accessible labels and focus support. The local `event-tabs.js` enhancement
initializes after initial rendering, HTMX swaps, and history restoration; a
restored page retains its selected tab. Without JavaScript the controls remain
hidden and both event sections stay available with their original headings.

Reduced header/panel spacing and kept the mobile logo beside the title. Past
events now have separate cards with 12px gaps, full-item hover/focus backgrounds,
borders, and shadows. Their title links cover the whole item while website links
remain independently clickable. Upcoming cards get the same hover/focus effect;
their original website links now live inside the cards. Homepage and directory
card layouts are preserved. All event records and ordering remain intact.

Affected files: the group detail partial, shared event card, `homepage.css`,
`base.htm`, and new `event-tabs.js`. No query or dependency changes.
Validation: **20 relevant tests passed, 12 subtests passed**; JavaScript syntax
and diff checks passed. Chromium verified both tabs at 360, 390, 768, 1280, and
1440px, no overflow, item spacing, full-card hover and click behavior, independent
website links, keyboard tabs, HTMX navigation/history, and the no-script fallback.
No JavaScript errors were observed.

Previews: [desktop tabs](qa/group-tabs-1280.png), [mobile tabs](qa/group-tabs-390.png),
[past event cards](qa/group-tabs-past-1280.png),
[upcoming event card](qa/group-tabs-with-events-1280.png).

### Shared card hover and focus

Moved the detail-page card effect into the shared event/group card rules in
`homepage.css`. Homepage, group directory, and event directory cards now use
the same pale-blue hover/focus background, action-blue border, and subtle shadow
as group-detail event items. The featured dark homepage card uses navy-soft for
its interactive background to preserve white-text contrast. Reduced motion
continues to disable transitions.

Chromium verified identical computed hover and keyboard-focus styles across
the light cards on all three pages, dark featured-card colors, no overflow at
390px, reduced-motion behavior, and no JavaScript errors. Diff checks passed.

## Homepage 30-day event carousel

“Next up in Spokane Tech” now renders all events starting from the request's
current timestamp up to, but excluding, 30 days later. The four-event cap is
removed. The full event directory, group upcoming counts, and global upcoming
total continue to cover all future events. The homepage introduction and empty
state explain the 30-day window, while its all-events link remains available.

Events use the groups carousel's shared native-scrolling enhancement and 32px
chevron controls. Both tracks have hidden scrollbars, snapping, independent
boundary states, arrow/Home/End keyboard controls, reduced-motion behavior, and
HTMX/history initialization. Events use wider three-column desktop slots,
two-column tablet slots, and a partial next card on mobile. The first event
keeps its featured appearance. Native scrolling works without JavaScript.

Affected files: `web/views.py`, the homepage partial, `homepage.css`,
`group-carousel.js`, and homepage tests. Both tracks now use shared
`data-carousel` and `data-carousel-scroll` attributes. Removed obsolete homepage
event-grid styles. Existing card hover styles and real event metadata remain.

Validation: **147 tests passed, 14 subtests passed**. Regression checks cover
both window boundaries, all matching events beyond four, chronological order,
unchanged global/group totals, and bounded query growth. The summer timezone
test now uses a summer request timestamp to keep its event inside the window.
Ruff, formatting, JavaScript syntax, `mypy src`, and diff checks passed.

Chromium verified 360, 390, 430, 768, 1024, 1280, and 1440px with stored event
and group data: one event row, no page overflow, hidden scrollbar, controls only
when needed, first/last boundary states, independent tracks, keyboard scrolling,
HTMX navigation/history, and native scrolling with scripts disabled. No
JavaScript errors were observed.

Previews: [desktop event carousel](qa/event-carousel-1280.png),
[mobile event carousel](qa/event-carousel-390.png).

## Calendar repair and redesign

The old calendar expected `cal_data_str` and direct event objects, while the
installed helper supplies `cal_data` and dictionaries wrapping each event. Its
full-page template also loaded the current-month route rather than displaying
the requested month. The application now builds a dedicated month/day context
and renders the selected month immediately for full-page and HTMX requests.

Event queries use Pacific-time midnight boundaries and each event's local date,
including UTC dates that fall in a different Pacific month. Today highlights
compare the complete local date. Previous/next/Today links retain real hrefs,
HTMX navigation, and history. Invalid dates return 400. Event tiles keep the
existing detail modals, with real internal detail URLs as their hrefs.

The page shares the directory header, restrained blue palette, typography, and
whole-card hover/focus treatment. Desktop shows a Monday-first month grid with
event times and organizers. Below 768px a day-by-day agenda shows start/end times
and available locations without horizontal overflow. One responsive template
replaces user-agent-dependent calendar markup; the former mobile partial is a
compatibility include. Empty months have an explanatory state. All content comes
from stored events; no migrations or dependencies were added.

Affected files: `web/views.py`, the full calendar template, desktop/mobile
calendar partials, new `home/calendar_event.htm`, `homepage.css`, and new
`tests/unit/web/test_calendar.py`. Events and related organizers load in one
data query regardless of event count. Explicit timezone labels also handle the
repeated daylight-saving hour, where Django's `date:"T"` filter yields no label.

Validation: **160 tests passed, 23 subtests passed**. New coverage verifies real
event rendering, initial and HTMX months, Pacific month/day boundaries, current
month routes, today highlighting, year rollover, DST's repeated hour, empty
months, invalid dates, and constant query counts. Ruff, formatting, `mypy src`
(70 files), and diff checks passed.

Chromium checks passed at 360, 390, 430, 768, 1024, 1280, and 1440px with the
copied application's seven October events. Verified grid/agenda switching,
hover, no overflow, month navigation, keyboard event modals, full-detail links,
history, empty months, mobile modals, and no-script rendering/navigation. The
final timezone change was rechecked at 390 and 1280px. No JavaScript errors.

Previews: [desktop calendar](qa/calendar-1280.png),
[mobile agenda](qa/calendar-390.png).

## About page styling

The About page now shares the directory typography, left-aligned introduction,
subtle blue palette, borders, and spacing. Its existing mission, audience,
learning opportunities, and invitation are reorganized into readable sections
with shorter copy. The sidebar reuses the community illustration and includes
the configured Discord link and real group-directory navigation. Event and group
links preserve HTMX navigation with real hrefs. The layout becomes one column on
tablet/mobile, and the full page renders content immediately without a second
load request. No new assets, application data, dependencies, or migrations.

Affected files: `web/templates/web/partials/custom/about.htm`, the full About
template, and scoped About rules in `homepage.css`. Validation: **3 relevant
tests passed, 6 subtests passed**, plus diff checks. Chromium verified 360, 390,
430, 768, 1024, 1280, and 1440px, artwork rendering, no overflow, keyboard links,
HTMX navigation/history, and initial rendering without scripts. No JavaScript
errors were observed.

Previews: [desktop About page](qa/about-1280.png),
[mobile About page](qa/about-390.png).

## Develop with us page and About contribution link

The developer page now shares About's responsive story/sidebar layout, community
illustration, typography, and blue palette. It retains the contribution
invitation, original GitHub repository, and development-post resources, with
the configured community Discord link alongside the repository CTA. About's
“Help shape what's next” section now links directly to Develop with us using
a real href and HTMX navigation.

Development posts render immediately from enabled blog platforms, with newest
stored records first. Cards show real titles, safe plain-text summaries, optional
images/authors/series, and prefetched topics; no mock posts or publication dates
are introduced. All matching records remain reachable in the native carousel.
The shared carousel enhancement now supports blog cards, including chevron
controls, keyboard arrows/Home/End, hidden scrollbars, and history initialization.
Cards use the same whole-item hover/focus effect as groups and events. Removed
the old inline style/script blocks and duplicate page/blog load requests. The
existing blog partial endpoint remains available.

Affected files: `web/views.py`, full/partial developer templates, About partial,
`homepage.css`, shared `group-carousel.js`, and new `test_develop.py`. Post data
takes two queries regardless of record/tag count. No dependencies or migrations.

Validation: **184 tests passed, 28 subtests passed**, plus Ruff, formatting,
JavaScript syntax, `mypy src` (74 files), and diff checks. New regression checks
cover full/HTMX real post rendering, platform filtering, safe excerpts, resources,
the About contribution link, empty states, and bounded queries. Chromium verified
360, 390, 430, 768, 1024, 1280, and 1440px using nine stored blog posts, including
control boundaries, keyboard scrolling, whole-card hover, no overflow, repeated
About/Develop HTMX visits, focus, history, and native scrolling without scripts.
No JavaScript errors were observed.

Previews: [desktop developer page](qa/develop-1280.png),
[mobile developer page](qa/develop-390.png).
