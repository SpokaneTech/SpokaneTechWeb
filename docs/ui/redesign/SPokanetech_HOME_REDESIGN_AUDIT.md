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
