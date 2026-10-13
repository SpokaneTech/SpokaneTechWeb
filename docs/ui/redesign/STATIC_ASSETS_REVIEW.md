# Static assets and CDN review

Reviewed October 8, 2026 following the homepage redesign.

## Recommendation

Retain Bootstrap for the existing Django/handyhelpers component behavior and use the scoped homepage CSS for the reference design. The homepage already uses native CSS grid/flex, custom typography, spacing, colors, and cards. A Tailwind migration would also need to address internal-page classes, Bootstrap modal templates, and navigation behavior; it is not needed to reproduce this reference.

No framework switch was made. Any future replacement of Bootstrap should be confirmed separately. Tailwind's [Play CDN documentation](https://tailwindcss.com/docs/installation/play-cdn) limits that option to development; a production Tailwind migration would require an appropriate CSS build.

## Findings and changes

- `base.htm` had seven runtime references to local `node_modules` packages. All were replaced with version-pinned jsDelivr URLs.
- Versions match the previously installed packages; this is a delivery change, not a dependency upgrade.
- Each package stylesheet/script has a SHA-384 integrity hash calculated from the downloaded asset and `crossorigin="anonymous"`.
- Bootstrap's bundle includes Popper, so the separate Popper script is no longer necessary. This follows the [official Bootstrap CDN guidance](https://getbootstrap.com/docs/5.3/getting-started/introduction/).
- Kept jQuery to preserve the existing global environment for integrations and partials.
- `spokanetech.scss` imported Bootstrap's Sass from local `node_modules`. Removed that import and retained the existing theme through CSS-variable and component overrides.
- Regenerated `spokanetech.css` and its source map. The local CSS contains only theme/site rules, reducing it from 278,348 bytes to approximately 16 KB. Bootstrap's complete stylesheet loads once from CDN.
- The CSS source map now references only `spokanetech.scss`.
- Favicons, supplied image derivatives, site CSS, and `navigation.js` remain Django static assets. Those files belong to this application and do not depend on handyhelpers packaging.
- The handyhelpers modal include is a server-side template dependency and remains intact. It does not require local package assets.

| Package | Pinned version | Delivery |
| --- | --- | --- |
| Bootstrap CSS and JS bundle | 5.3.8 | jsDelivr |
| Font Awesome Free CSS/fonts | 6.2.0 | jsDelivr |
| Animate.css | 4.1.1 | jsDelivr |
| HTMX | 1.9.6 | jsDelivr |
| jQuery | 3.6.1 | jsDelivr |
| Popper | 2.11.8, included by Bootstrap | Bootstrap bundle |

The existing Ubuntu font import continues to use Google Fonts. Homepage typography uses the system font stack in `homepage.css`.

## Changed files

- `src/django_project/core/templates/base.htm`: CDN package URLs and integrity attributes.
- `src/django_project/core/static/spokanetech/css/spokanetech.scss`: independent theme source.
- `src/django_project/core/static/spokanetech/css/spokanetech.css`: regenerated theme-only CSS.
- `src/django_project/core/static/spokanetech/css/spokanetech.css.map`: regenerated source map.
- README and audit/review documentation: current asset delivery/build instructions.

## Build and validation

The committed site CSS is served directly; deployments do not need npm, node_modules, or Sass. To regenerate it after editing the source, run from the repository root:

```bash
sass --style expanded src/django_project/core/static/spokanetech/css/spokanetech.scss src/django_project/core/static/spokanetech/css/spokanetech.css
```

Standalone Sass compilation succeeded from a temporary directory containing only the source file, with no local package directories. All sixteen solid/outline button palettes retain their original normal, hover, active, focus, and disabled variables.

Relevant automated tests: **30 passed and 8 subtests passed** (existing web view tests and homepage tests). Django preview system checks and `git diff --check` passed.

Chromium verified the actual CDN scripts, icon fonts, responsive homepage at 360/768/1280/1440px, mobile navigation, HTMX navigation, and group-modal open/close behavior. Local `/static/node_modules/**` requests were deliberately blocked. Computed button, text/background, and form colors were compared with the previous compiled stylesheet. No package files were copied into production static assets as fallbacks.

## Separate finding: calendar context compatibility

The installed handyhelpers `CalendarView` supplies `cal_data` and an `event_list` of dictionaries containing `object`, `day`, `month`, `year`, and `pk`. The existing desktop calendar template expects `cal_data_str` and direct event model objects. A real October 2026 request returned 200 but rendered no event controls despite event records in the database snapshot.

This is a pre-existing view/template data-contract mismatch, independent of CDN asset loading. No calendar templates or backend views were changed in this asset-delivery update. Calendar compatibility should be repaired and covered by a positive event-rendering test separately.

Resolved in the subsequent calendar redesign: the application now builds its
own Pacific-time month/day context and renders real events directly. See the
[calendar audit](SPokanetech_HOME_REDESIGN_AUDIT.md#calendar-repair-and-redesign)
for implementation and validation.
