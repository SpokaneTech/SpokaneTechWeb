# SpokaneTech.org Homepage Redesign Implementation Plan

## Purpose

Implement the next iteration of the SpokaneTech.org landing page using the supplied visual reference and image assets.

This is a redesign of the existing SpokaneTech site, not a greenfield rewrite. Preserve the existing Django application, data model, URLs, event/group functionality, authentication behavior, HTMX behavior, analytics, and backend integrations unless a UI change explicitly requires a small template/view adjustment.

The redesign should make SpokaneTech feel like the front door to Spokane's technology community: local, modern, welcoming, useful, and clearly focused on discovering events and communities.

## Supplied design assets

Place these files in the project's appropriate static/image directory and use optimized web derivatives as needed:

- `homepage-design-reference.png` — overall visual target. This is a design reference, not an image to embed in the site.
- `hero-spokane-twilight.png` — homepage hero background.
- `spokane-community-illustration.png` — illustration for the "One community. Many technologies." section.

Do not regenerate or replace these assets unless explicitly requested. Preserve the originals in the repository and create optimized versions if necessary.

## Core product goals

The homepage should answer three questions immediately:

1. What is SpokaneTech?
2. What is happening next in Spokane's tech community?
3. How can I find a group or get involved?

The primary user journey is:

**Find an event -> Find a community -> Get involved**

Do not make the page look like a SaaS marketing site. It should feel like a polished civic/community hub with a technical edge.

## Implementation principles

- Work within the existing architecture and conventions.
- Inspect the current templates, template inheritance, static assets, CSS/Tailwind/Bootstrap setup, HTMX patterns, views, context processors, event/group models, and tests before modifying anything.
- Reuse existing event/group data. Do not hard-code production event or group content that already exists in the database.
- Prefer server-rendered Django templates and existing HTMX patterns over unnecessary JavaScript.
- Do not introduce a frontend framework.
- Keep dependencies minimal.
- Preserve existing URLs and SEO-friendly routes where practical.
- Maintain or improve accessibility.
- Maintain responsive behavior from small mobile screens through wide desktop displays.
- Avoid destructive database changes. This redesign should ideally require no schema migration.
- Do not invent counts, event details, group names, venues, or social URLs. Derive them from existing data/configuration.
- If the current codebase differs from assumptions in this document, adapt the implementation to the codebase rather than forcing a new architecture.

## Visual direction

Use `homepage-design-reference.png` as the primary visual reference.

The visual language should include:

- dark navy hero/header area;
- bright blue/cyan accents;
- clean white/light-gray content background;
- large, confident sans-serif typography;
- generous spacing;
- restrained rounded corners;
- subtle borders and shadows;
- compact technology/topic pills;
- dark navy community CTA/statistics section near the bottom;
- Spokane-specific imagery rather than generic technology stock photography.

Avoid excessive gradients, glassmorphism, neon/cyberpunk styling, oversized shadows, or card-on-card visual clutter.

The page should feel contemporary but durable enough that it will not look dated quickly.

## Suggested design tokens

First inspect existing project tokens and reuse them where reasonable. Consolidate new values rather than scattering arbitrary values through templates.

Suggested palette:

- Navy 950: `#07182c`
- Navy 900: `#0b1f38`
- Navy 800: `#123252`
- Blue 600: `#2563eb`
- Blue 500: `#3b82f6`
- Cyan 400: `#38bdf8`
- Slate 900: `#0f172a`
- Slate 700: `#334155`
- Slate 500: `#64748b`
- Slate 200: `#e2e8f0`
- Slate 100: `#f1f5f9`
- White: `#ffffff`

These are starting points, not a requirement to reproduce every hex value exactly. Tune them to match the reference and existing brand assets.

Use a consistent radius scale, approximately 10-16px for cards and controls.

Use shadows sparingly. Borders and tonal separation should do most of the work.

## Page architecture

### 1. Global header/navigation

Create a compact dark header that visually flows into the hero.

Left:
- existing SpokaneTech logo/wordmark.

Primary navigation:
- Events
- Groups
- Resources
- About

If changing the existing top-level navigation would break established routes or features, keep the routes but simplify their presentation. If Calendar remains a standalone page, it can stay accessible from Events or the footer.

Right:
- search control if search already exists or can be implemented cleanly using current functionality;
- prominent `Join Discord` CTA if the project already has the Discord URL configured.

Requirements:
- sticky behavior is optional; do not add it unless it feels natural and does not create mobile issues;
- mobile navigation must be keyboard accessible;
- visible focus states;
- no horizontal overflow.

### 2. Hero

Use `hero-spokane-twilight.png` as the hero background.

Desktop:
- full-width image;
- content constrained to the normal site max width;
- text primarily on the left;
- dark navy/black overlay or gradient on the left to ensure excellent text contrast;
- preserve the most recognizable Spokane scenery toward the center/right.

Recommended copy:

Eyebrow:
`SPOKANE'S TECH COMMUNITY`

Headline:
`Connect with Spokane's tech community.`

Supporting copy:
`Discover local developer groups, meetups, workshops, and opportunities to connect with people building technology in the Inland Northwest.`

Primary CTA:
`Explore Upcoming Events`

Secondary CTA:
`Find a Tech Group`

Optional tertiary link:
`Join the community on Discord`

The primary CTA should scroll/navigate to upcoming events or the events page according to existing site conventions. The secondary CTA should go to the groups page.

Responsive behavior:
- maintain legibility without relying on the image;
- on narrow screens, reposition/crop the background intentionally;
- keep the hero reasonably compact on mobile;
- never put important text over a bright part of the image without sufficient overlay.

### 3. "Next up in Spokane Tech" / upcoming events

This is the most important functional section after the hero.

Heading:
`Next up in Spokane Tech`

Small eyebrow:
`WHAT'S HAPPENING`

Include:
- one visually prominent next/featured event;
- several additional upcoming events;
- `View all upcoming events` link.

Data:
- derive events from the existing event query/model;
- sort chronologically;
- do not show past events;
- if an existing featured-event concept exists, use it; otherwise the nearest upcoming event can be visually featured without adding a database field.

Featured card should prioritize:
- date;
- event title;
- group;
- day/time;
- venue/location if available;
- topic/category tags if existing data supports them;
- event detail link.

Secondary cards should be more compact but show the same essential information.

Do not fabricate event photography. If the existing data includes event/group images, use them. Otherwise use a graceful branded fallback (gradient, group mark, or neutral illustration) rather than random stock photos.

Empty state:
If there are no upcoming events, replace the grid with a friendly empty state and links to Groups/Calendar rather than leaving an empty section.

### 4. Explore Spokane's tech communities

Heading:
`Explore Spokane's tech communities`

Supporting copy:
`Local groups. Real people. All are welcome.`

Display a responsive grid of active groups.

Each group item should contain, where data is available:
- group logo/icon;
- group name;
- upcoming event count;
- concise tags/categories;
- link to group detail.

Use real project data. Do not hard-code Python/Go/Rust/etc. solely because they appear in the mockup.

Limit the homepage to a useful number of groups (for example 5-8), with:
`View all groups`

If logos are visually inconsistent, normalize them inside a fixed-size logo area without altering source images.

### 5. "One community. Many technologies."

This section provides identity and visual breathing room.

Use `spokane-community-illustration.png` on the left or as a left-side/background visual. The reference image should not be stretched or distorted.

Eyebrow:
`ONE COMMUNITY. MANY TECHNOLOGIES.`

Headline:
`Whatever you build with, there's a place for you here.`

On the right or below the headline, show a restrained set of technology/community tags based on actual group/event categories if such data exists. Example labels in the reference include Python, Go, Rust, JavaScript, AWS, Linux, AI, DevOps, Security, Data, and Web, but these are illustrative only.

If the application does not currently model tags/categories reliably, use a curated static list only if there is already an appropriate site configuration/content mechanism. Otherwise omit the pills for the first implementation.

### 6. Community statistics + get involved

Create a dark navy panel inspired by the reference.

Left:
`Our community in numbers`

Show useful live counts that can be calculated cheaply, such as:
- active local tech groups;
- upcoming events.

Do not use the mockup's literal numbers.

Only show metrics that are meaningful and backed by actual data. Do not add expensive per-request aggregation if it can be avoided; use efficient queries/context or existing cached values.

Right:
`Don't just browse. Join us.`

Suggested copy:
`Meet developers, share projects, learn something new, or help organize the next event.`

CTAs:
- `Join Discord`
- `Find a Meetup` or `Explore Events`

Use existing configured community links.

### 7. Footer

Use a dark footer that visually continues the community panel.

Include:
- SpokaneTech logo/wordmark;
- concise community tagline;
- primary navigation;
- existing social/community links;
- copyright or existing footer information.

Suggested tagline:
`Built by Spokane's tech community.`

Do not remove required legal/privacy links if they exist.

## Event and group component design

Build reusable template components/partials rather than duplicating markup.

Potential partials:
- event card;
- featured event card;
- group card;
- tag/pill;
- section heading;
- CTA button;
- empty state.

Follow the repository's existing include/component conventions.

Event cards:
- make the whole interaction obvious;
- avoid invalid nested links;
- ensure keyboard users can reach the detail action;
- use semantic `<time datetime="">` markup where appropriate;
- use icons decoratively with `aria-hidden="true"` when adjacent text already conveys meaning.

Group cards:
- consistent logo treatment;
- concise content;
- equal visual rhythm without forcing identical content height at the expense of mobile usability.

## Responsive design

Test at minimum around:
- 360px mobile;
- 390/430px mobile;
- 768px tablet;
- 1024px laptop/tablet landscape;
- 1280px desktop;
- 1440px+ desktop.

Expected behavior:
- hero CTAs stack cleanly on narrow screens;
- event cards become a vertical list or sensible horizontal scroller only if accessibility is preserved;
- group grid collapses progressively;
- illustration/text section stacks with image first;
- stats/CTA panel stacks;
- footer columns collapse cleanly;
- no tiny text, clipped controls, or horizontal page scrolling.

Prefer CSS grid/flex responsive layouts over JavaScript-driven layout.

## Accessibility requirements

Treat accessibility as part of the implementation, not a cleanup task.

Required:
- semantic heading hierarchy;
- one clear page `<h1>`;
- WCAG AA text contrast;
- visible keyboard focus states;
- all interactive controls keyboard usable;
- meaningful image alt text where images convey content;
- decorative imagery uses empty alt text/background treatment;
- nav has appropriate semantic structure;
- mobile menu communicates expanded state;
- links make sense out of context;
- icons do not replace accessible labels;
- respect `prefers-reduced-motion`;
- do not auto-rotate carousels;
- avoid unnecessary animation.

The hero image is decorative context and can be implemented as CSS background imagery. The Spokane illustration is also primarily decorative and should not produce noisy screen-reader output.

## Performance and image handling

Preserve the supplied originals and generate web-optimized derivatives.

For the hero:
- create AVIF/WebP if the existing pipeline supports them;
- retain an appropriate fallback;
- size it for realistic desktop hero rendering rather than shipping an unnecessarily huge original;
- consider responsive image variants if straightforward;
- because it is above the fold, do not lazy-load the primary hero background if doing so creates a visible flash.

For the lower illustration:
- optimize aggressively;
- lazy-load when implemented as `<img>`;
- specify width/height or aspect ratio to prevent layout shift.

Avoid adding large JavaScript bundles for this redesign.

## SEO / metadata

Preserve current metadata and improve it where appropriate.

Homepage should clearly describe SpokaneTech as a Spokane/Inland Northwest technology community/events resource.

Preserve:
- canonical behavior;
- Open Graph/Twitter metadata if present;
- structured data if present;
- sitemap behavior;
- meaningful title/description.

Do not make SEO changes unrelated to the redesign unless correcting an obvious problem.

## Backend/query considerations

Before implementing, inspect how the current homepage gets:
- upcoming events;
- groups;
- event counts;
- site statistics;
- social links.

Prefer a small number of efficient queries. Avoid N+1 queries when rendering group/event cards. Use `select_related`, `prefetch_related`, annotations, or existing services/managers where appropriate.

Do not change model structure just to match the mockup.

## HTMX behavior

Preserve existing HTMX conventions, including any existing URL push behavior and custom response headers/toasts.

Do not convert simple navigation into HTMX just for the redesign. Use HTMX where it already improves existing interactions such as filters, pagination, or dynamic event/group content.

If event filters are enhanced later, structure the event-card partials so they can be reused in HTMX responses.

## Search

The mockup shows a search field, but search is not required for the first redesign milestone unless the site already has a suitable search implementation.

If search does not exist:
- either omit the header search for this iteration;
- or create a separate follow-up issue.

Do not build a rushed client-side search just to visually match the mockup.

## Motion and interaction

Use subtle interaction only:
- modest button/card hover transitions;
- slight border/shadow changes;
- no large transforms;
- no parallax;
- no auto-playing animation.

Respect reduced-motion preferences.

## Implementation phases

### Phase 1 - Audit

Before writing code:
1. inspect repository structure and AGENTS.md/project instructions;
2. identify homepage view/template and base layout;
3. identify CSS framework/build process;
4. identify event/group models and current homepage context;
5. identify existing reusable components;
6. identify social link configuration;
7. run the current test suite or relevant tests;
8. capture the current homepage behavior so functionality is not lost.

Summarize the intended file changes before implementing.

### Phase 2 - Foundation

1. Add approved image assets to static assets.
2. Add/consolidate design tokens.
3. Update base/header/footer styling as required.
4. Create reusable homepage partials/components.
5. Preserve existing global behavior.

### Phase 3 - Homepage sections

Implement in this order:
1. hero;
2. upcoming events;
3. groups;
4. community/technology illustration;
5. statistics/get-involved panel;
6. footer refinements.

After each major section, verify desktop and mobile behavior.

### Phase 4 - Polish

1. refine typography/spacing;
2. optimize images;
3. verify hover/focus/active states;
4. verify empty states and long-content behavior;
5. verify dates/times;
6. verify mobile menu;
7. verify accessibility;
8. remove obsolete homepage CSS/markup only when confirmed unused.

### Phase 5 - Tests and QA

Run all relevant automated tests and add/update tests for changed server-side behavior.

At minimum verify:
- homepage returns successfully;
- upcoming events are chronological and exclude past events;
- event links are correct;
- group links are correct;
- empty upcoming-event state renders;
- live counts reflect query data;
- authenticated and anonymous users both render correctly if applicable;
- existing navigation routes still work.

If Playwright/browser tests already exist, add visual/interaction coverage using project conventions.

Manually verify:
- 360px;
- 768px;
- 1280px;
- 1440px;
- keyboard-only navigation;
- reduced motion;
- no console errors;
- no missing static assets;
- no obvious layout shift;
- no N+1 query regression.

## Acceptance criteria

The work is complete when:

- The homepage closely follows `homepage-design-reference.png` in hierarchy, tone, spacing, and component styling without requiring pixel-perfect reproduction.
- `hero-spokane-twilight.png` is used for the hero.
- `spokane-community-illustration.png` is used in the community/technology section.
- Existing SpokaneTech functionality and URLs continue to work.
- Upcoming events and groups come from real application data.
- No mock event/group/count data remains in production templates.
- The page is polished at mobile, tablet, and desktop widths.
- Accessibility is maintained or improved.
- Images are web optimized.
- No unnecessary JavaScript/framework is introduced.
- Tests pass.
- No unrelated refactor is mixed into the redesign.
- The final diff is understandable and appropriately scoped.

## Non-goals for this iteration

Unless already supported and trivial to expose, do not expand scope into:
- new authentication flows;
- new event ingestion sources;
- a new CMS;
- new database schema solely for design metadata;
- a React/Vue/Svelte frontend;
- full-text search;
- personalized recommendations;
- major redesigns of every internal page.

The homepage should establish the new design system so Events, Groups, Resources, and other pages can be migrated incrementally afterward.

## Codex execution guidance

Work incrementally and preserve a reviewable git diff.

Before changing code, report:
1. the current homepage/template architecture;
2. the styling/build approach in use;
3. the files you expect to modify;
4. any discrepancy between this plan and the actual repository.

Then implement the redesign.

Do not stop merely because the mockup cannot be reproduced pixel-for-pixel. Use the supplied reference as design intent and make pragmatic decisions consistent with the existing codebase.

When finished, report:
- files changed;
- key implementation decisions;
- tests run and results;
- any remaining follow-up work;
- any places where the implementation intentionally differs from the mockup and why.
