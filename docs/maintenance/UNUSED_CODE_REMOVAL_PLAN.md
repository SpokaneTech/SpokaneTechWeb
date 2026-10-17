# Unused code and file removal plan

Reviewed: 2026-10-17. Repository baseline: `260e124`.
Status: confirmed cleanup implemented on 2026-10-17; conditional items retained.
See the implementation record below for completed work, evidence, and deferred gates.

## Scope and standard of evidence

Reviewed 236 tracked files, including 100 Python files, 34 templates, and 24
static files. Inspected Python definitions/imports, string-based references,
Django URL/settings/template configuration, Celery registration, initialization
scripts, packaging, Docker Compose, CI workflows, tests, and installed dependency
metadata. Reference searches covered tracked application and configuration files;
documentation-only mentions were distinguished from runtime references.

An absent text reference is evidence, not a guarantee: Django discovers modules,
Celery task names can live in a database or queue, and a publicly served URL can
have callers outside this repository. Each batch below has a verification gate.
Anything with unresolved runtime use stays in place. Removing a current route,
changing rendered content, changing encryption, or deleting user data is not an
acceptable side effect of this cleanup.

This audit did not inspect production task schedules, broker queues, access logs,
reverse-proxy configuration, external callers, or production Compose overrides.
It did not perform live ingestion, send external notifications, edit application or
production databases, or delete media. Tests used their isolated test database.

## 1. File candidates with no current application references

Paths in this table are relative to `src/django_project/`. These nine files total
514,232 bytes (about 502 KiB). That is repository/source size, not an estimate of
page-download savings: the old stylesheet and script are already unloaded.

| ID | Candidate | Evidence | Removal gate |
| --- | --- | --- | --- |
| F1 | `core/backend.py` | Empty tracked file; no backend implementation or references. The project does not configure this module as an authentication backend. | Django checks and authentication/host smoke tests still pass. |
| F2 | `web/forms.py` | Contains only commented import placeholders; no form definitions or references. | No local imports or registered helper forms point to this module; checks and route tests pass. |
| F3 | `core/static/spokanetech/js/bgicons.js` | Legacy random background-icon generator; no script include or import. Current carousel/navigation/tab scripts are separate and loaded in `base.htm`. | Browser network checks confirm it is not requested; homepage layout remains unchanged. |
| F4 | `core/static/spokanetech/css/index-styles.css` | Old green/translucent layout and modal stylesheet; no stylesheet link/import. Current base loads `spokanetech.css` and `homepage.css`. | Confirm no deployment-specific template injects it; normal and HTMX page screenshots match baseline. |
| F5 | `core/static/spokanetech/img/bg-01.jpg` | No tracked source reference. | Check static access logs/custom templates before removal. |
| F6 | `core/static/spokanetech/img/bg-02.jpg` | Its only tracked reference is F4, the unloaded stylesheet. | Remove with/after F4; confirm no external/custom template uses the image. |
| F7 | `web/templates/web/partials/custom/calendar_mobile.htm` | An include-only alias for `calendar.htm`, with no incoming references. `EventCalendarView` uses one responsive calendar template. | Calendar tests and mobile/desktop full and HTMX rendering pass. |
| F8 | `web/templates/web/partials/modal/event_information_modal.htm` | An include-only alias for `event_information.htm`, with no incoming references. The event modal view selects the responsive canonical template directly. | Event/group modal tests and mobile preview/dismissal checks pass. |
| F9 | `web/templates/web/partials/marquee/events.htm` | No view, include, or test selects this old event marquee. The event view still uses `partials/li/events.htm` for its supported minimal/`li` output. | Verify `/events`, `/events/list`, and `/events/li` compatibility. Keep the working minimal template and its view attributes. |

Remove these in small commits: F1–F2, F3–F6, then F7–F9. Re-run reference searches
immediately before each commit; cancel the deletion if a new consumer exists.
Keep static assets through a compatibility interval if access logs reveal legacy
clients still requesting them. Do not delete all similarly named templates.

## 2. Uncalled Python utility routines

| ID | Proposed removal | Evidence and follow-up |
| --- | --- | --- |
| P1 | `web/utilities/html_utils.py::find_target()` and `TargetNotFoundError` | No callers/importers in tracked production code or tests. The exception is only used by this function. Remove `Tag`, `NavigableString`, and `PageElement` imports if they remain unused afterward. Keep `fetch_content()`, `FetchContentError`, `fetch_content_with_playwright()`, and `convert_html_to_text()`, which are active. |
| P2 | `web/utilities/scrapers/eventbrite.py::filter_events_by_date()` | No callers/importers. It filters by event creation date; current discovery uses a start-date window and pagination. Remove the `datetime` import if still exclusive to this function; retain `timedelta` and Django `timezone`. |
| P3 | `web/utilities/scrapers/meetup.py::get_end_datetime()` | No callers/importers. Current `get_event_information()` calculates end times using a parsed duration, including overnight events. Remove the standard-library `timezone` import if still exclusive to this function; retain `datetime` and `timedelta`. |

These functions are not documented as supported public package entry points.
Nevertheless, check private automation imports before removal. Run the scraper,
ingestion, lifecycle, and image tests plus type/security checks after the batch.
Do not remove code simply because its only explicit callers are tests: Django
callbacks, model properties, and registered tasks can have implicit callers.

## 3. CSS cleanup after file removal

Edit Sass sources and regenerate committed CSS together. Never delete the compiled
`spokanetech.css` just because templates do not reference its `.scss` source.

### Narrow rules with no remaining local consumer

In `homepage.css`:

- `.st-group-back`: the event/group back links were intentionally removed.
- `.st-event-directory .st-directory-card-action` and
  `.st-group-detail .st-directory-card-action`: those event-card labels were removed.
  Keep the generic `.st-directory-card-action` and its blog-specific rule;
  Develop still uses them.
- `.st-modal-description > :last-child`, `.st-modal-description pre/table`, and
  the `.st-modal-description a` selector: both description previews now render
  escaped plain text using `striptags`. Keep `.st-modal-description` itself and
  split out/preserve `.st-modal-links a`, which styles real community links.

### Rules/assets requiring a broader rendered-template check

`spokanetech.scss` contains old `.social-icon-link .social-icon`,
`.spaced-bordered-items`, `.note-link-*`, and `.hero` rules. No current local
consumer was found for the first three; current page headers use `st-*` classes.
The host page has `id="hero"`, not `class="hero"`; the latter stylesheet selector
does not match that ID. If rendered helper/custom templates also do not use the
`.hero` rules, remove those rules and then retire `img/hero.jpg` (774,286 bytes).
It is currently still referenced by both Sass and compiled CSS, so it is not an
independently unused image.

Keep Bootstrap palette/component overrides, form/focus styling, general layout,
and utility styles without broader proof. The installed helper exposes additional
routes and templates; searching only the redesigned homepage is insufficient.
Do not remove `.hover-grow`/`.hover-bg-light`: the supported minimal event partial
still uses them. Compare Sass output and source-map references after rebuilding.

## 4. Conditional candidates: do not delete in the initial batches

| Item | Finding | Required decision/evidence |
| --- | --- | --- |
| `web.test_task` and `core.celery.debug_task` | Diagnostic tasks with no production Python callers; `debug_task` has tests. Both are registered dynamically. | Check `django_celery_beat` task names, manual monitoring, and pending broker messages in every deployment. Retain until confirmed unused; drain/deprecate task names before deletion. Do not touch ingestion/reminder/summary launchers on the same basis. |
| `src/docker/docker-compose.yaml::volumes.static_volume` | Declared but not mounted by any checked-in service. | Check merged production Compose configuration/overrides, then remove only the unused declaration. Do not delete an actual volume or run `docker compose down -v`. Persistent media/database/Redis volumes are active. |
| `core/static/site.webmanifest`, Android icons, and `favicon.ico` | No manifest link in the base template; the manifest's Android icon URLs do not match their actual static locations. | Decide whether to wire up/correct the manifest or retire the unused asset set after checking clients/access logs. Keep currently linked Apple touch and 16/32px favicons. Do not assume public icon URLs have no external consumers. |
| jQuery and Animate.css CDN includes in `base.htm` | No current application JavaScript uses jQuery, and no local template uses `animate__*`. | Review rendered helper/account/admin/modal pages and any external HTML/widget content. Remove one include at a time only after browser interaction/network checks. Keep Bootstrap, HTMX, and Font Awesome, which are active. |
| `django-braces` direct dependency | No project imports/configuration references found. | Verify clean development and Docker installs, dependency metadata, and routed helper features before dropping the direct declaration. The existing virtualenv contains unrelated distributions, so its dependency graph alone cannot prove safety. |
| `packaging` direct dependency | No direct project imports; installed Celery/Kombu and developer tools use it transitively. | Consider dropping only the direct declaration after clean-install checks. Do not uninstall the transitive package. |
| `redis` direct declaration alongside `celery[redis]` | Potentially redundant declaration, but Redis is an active broker/backend dependency. | Validate the extra provides the required version in a clean resolver run; this is metadata deduplication, not removal of Redis support. |
| `django-debug-toolbar` repeated in runtime and dev lists | The dev declaration duplicates a base dependency; local/dev settings actively enable the app. | It is safe to consider removing the duplicate dev-list entry. Do not remove the runtime dependency or app configuration without a separate change to installation behavior. |
| Unreferenced dev tools/configuration (`black`, `isort`, `coveralls`, related extras) | No direct invocation found in current checked-in workflows/hooks; Ruff is in active use. README still has an Isort workflow badge, but that workflow is absent. | Check contributor tooling and reusable GitHub Actions before removing optional tools/config. Fix/remove the stale badge separately. Retain active Ruff, Bandit, mypy, pytest, FawltyDeps, Radon, and their workflows. |

Retain `django-filter==25.1`: helper/REST dependencies use django-filter even
though the app does not import it directly. Keep Pillow, psycopg2, WhiteNoise,
Flower, django-extensions, and django-celery-beat: their consumers are respectively
images, the production DB backend, middleware/static serving, Compose, runscript,
and the database scheduler. FawltyDeps' ignore list is not evidence of dead code.
Do not upgrade dependencies as part of deletion commits; preserve the validated
versions to avoid mixing cleanup with helper/API changes.

## 5. Encryption fallback: separate compatibility investigation

The tracked root-level `encrypted_fields/` package is not ordinary dead code.
Its `EncryptedTextField` subclass is a plain `models.TextField` fallback; the
required `django-fernet-encrypted-fields` dependency implements the real field.

Observed with this virtualenv:

- Running Python from the repository root resolves `encrypted_fields` to this
  repository's fallback package.
- Running Python from `src/django_project` resolves it to the installed dependency.
- Model and migration imports use the same `encrypted_fields.fields` module name.
  Setuptools discovers only packages under `src/django_project`, and the Dockerfile
  copies that application tree rather than the root fallback package.

This difference can change field behavior across launch/test environments. Do
not classify the fallback as harmless just because Docker does not copy it.
Investigate and retire it in a separate patch only after clean installs verify
that the declared encryption dependency is present for all supported entry points.
Test import origins, migration replay, encrypted save/load round trips, and reading
existing records from an isolated database copy from both working directories.
Do not rewrite credentials or existing data as a side effect of cleanup. Keep the
real dependency, `SALT_KEY`, encrypted model fields, and historical migrations.

## 6. Explicitly retained functionality

- All Django migrations and package `__init__.py` files required for package/app,
  migration, signal, management-command, or script discovery.
- `manage.py`, its `spokanetech-manage` entry point, ASGI/WSGI, app `ready()` hooks,
  signal receivers, context processors, authentication/admin routes, and host view.
- `web/partials/marquee/groups.htm`: still selected by the group minimal/marquee
  route and covered by tests. Also retain `web/partials/li/events.htm`, the group
  list wrapper, and both canonical event/group modal templates and endpoints.
- `/blogs/blog_posts/` and its view/template: still a public routed endpoint with
  tests even though Develop now reads stored posts directly. Keep blog models,
  tags/series, initialization scripts, and migrations.
- All registered ingestion, image, reminder, weekly-summary, and notification
  tasks. No Python caller is needed for a task named in a database schedule.
- Initialization and ingestion scripts: `runscript` discovers their `run()` entry
  points; README references them. Internal script helper functions are called by
  `run()` even when they have no imports elsewhere.
- Model methods/properties such as `get_past_events()`/`past_events`: they call
  one another and/or are resolved by templates. Do not delete them from a naive
  external-reference count.
- Current homepage imagery and all documented format fallbacks; `.jpg` fallback
  images remain referenced alongside `.webp` assets.
- Sass source, compiled styles, and its currently linked source map; QA screenshots,
  redesign references/plans, ADRs, legal/community documents, CI workflows, and
  the Git hook are maintained artifacts rather than runtime dead-code candidates.

Ignored/untracked `src/local_test`, local environment files, SQLite databases,
media uploads, `staticroot`, node_modules, caches, and local Docker overrides are
not source-removal candidates. Do not blanket-delete them; they may contain user
data, credentials, local configuration, or useful debugging work. Regenerable
cache cleanup is a separate opt-in operation, not part of this plan.

## 7. Execution sequence and acceptance gates

1. **Record a baseline.** Capture working dependency versions; run the full suite
   from `src/django_project` with `.env.test`, plus mypy, Ruff, and Bandit. Record
   route/rendering checks and representative desktop/mobile screenshots. Keep the
   working tree clean so every later commit is easy to revert.
2. **Remove F1–F9 in their small batches.** No URL, model, migration, task-name,
   environment, or dependency changes. Run checks and relevant directory/calendar/
   modal tests after each batch. Run the full suite before accepting the phase.
3. **Remove P1–P3 and exclusive imports.** Run ingestion/scraper/lifecycle/image
   tests and the full static checks. Verify the standalone script still uses
   synchronous image handling and scheduled jobs still queue image tasks.
4. **Trim proven CSS leftovers.** Rebuild Sass and keep generated CSS/source maps
   consistent. Check homepage, lists, details, calendar, modals, About, Develop,
   host, and reachable helper/account pages, including HTMX/history, keyboard
   navigation, responsive layouts, image fallbacks, and missing optional data.
5. **Handle each conditional candidate separately.** Obtain the runtime evidence
   in section 4; retain anything unproven. Resolve the encryption fallback in its
   own tested compatibility patch, not a bulk deletion.
6. **Validate delivery.** In isolated environments, test editable and wheel
   installations, the packaged management command, and the Docker web/worker/beat/
   Flower/media configuration. Run `pip check` against the pre-cleanup baseline,
   collect static assets to a temporary output directory, and check for newly
   introduced missing templates/static requests. Validate `.env.template` settings
   without exposing actual credentials.
7. **Stage and retain rollback.** Deploy only reviewed cleanup commits; smoke-test
   known public URLs and observe errors/static access requests/task execution over
   at least a complete configured scheduler cycle. Revert the responsible batch
   if behavior changes. This cleanup should require no schema/data migration.

Suggested checks (with the virtualenv activated):

```bash
# Repository root
python -m bandit src -c pyproject.toml -r
python -m mypy src
python -m ruff check src
python -m ruff format src --check

# Application directory; isolated test settings, not production credentials
cd src/django_project
ENV_PATH=../envs/.env.test DEBUG=False python -m pytest
ENV_PATH=../envs/.env.test DEBUG=False python manage.py check
ENV_PATH=../envs/.env.test DEBUG=False python manage.py makemigrations --check --dry-run
```

Accept a removal batch only with its concrete file list, a fresh reference scan,
passing relevant/full tests, and the required runtime checks. Static analysis alone
cannot prove zero impact. Stop deletion for
that batch if a reference, active schedule, external consumer, or regression is found.

## Audit baseline results

Completed on the unmodified application using this environment:

- Full pytest suite: **218 passed, 60 subtests passed** (79.16 seconds).
- `mypy src`: no issues in 81 source files.
- `ruff check src`: passed.
- Django system checks with test settings: no issues.
- `bandit src -c pyproject.toml -r`: no issues identified.
- Import-origin checks confirmed the root/project-directory encryption difference.
- Only this plan document was added; no source, configuration, or data deletion.

These are pre-removal baselines. The proposed deletions have not been implemented
or tested as a modified application. No production runtime/access-log checks or
clean Docker/wheel dependency-resolution experiments were performed during this
read-only audit; those are explicit gates in the plan.


## Implementation record — 2026-10-17

### Completed source cleanup

- Removed F1–F4 and F7–F9: the empty backend, commented forms module, unused
  background-icon script/stylesheet, mobile include aliases, and unrouted event
  marquee template. Fresh searches found no live source references. Current
  pages never requested the removed script or stylesheet in browser checks.
- Removed P1–P3, `TargetNotFoundError`, and their exclusive imports. Current
  discovery, duration parsing, event reconciliation, and image ingestion remain
  covered by the full test suite.
- Removed the listed unused `homepage.css` rules while retaining blog card action
  and community-link styling. Removed unused social-icon, spaced-list, note-link,
  and old hero Sass rules. Regenerated committed CSS and its source map with the
  documented Sass command. Bootstrap palette/form/focus rules and supported
  minimal-card hover styles remain.
- Removed the duplicate dev-extra `django-debug-toolbar` declaration and stale
  README Isort badge. Effective dependency sets for base, dev, Docker, and
  dev+Docker installations are identical before/after this metadata cleanup.

### Separately validated encryption fallback retirement

Removed the two root `encrypted_fields/` shim source files. The required real
`django-fernet-encrypted-fields` package is now selected consistently from the
repository root and application directory. The real dependency remains declared;
production/Docker imports already used it. No model definitions, existing field
import paths, encryption keys, or migrations were changed.

A clean temporary environment installed Django 5.2.18,
django-fernet-encrypted-fields 0.3.1, and cryptography 46.0.4. Isolated database
checks verified encrypted storage, decryption, and readability of synthetic
legacy plaintext values. New regression tests verify import origins from both
working directories and ORM encryption/legacy read behavior. No actual stored
credentials were read, rewritten, or logged. Legacy plaintext readability is the
real library's compatibility behavior; this cleanup does not automatically
re-encrypt existing plaintext rows.

### Items retained because their gates remain unresolved

| Item | Disposition |
| --- | --- |
| F5/F6: `bg-01.jpg`, `bg-02.jpg`; and `hero.jpg` | Retained. Their unused CSS references were retired, but production asset access/legacy-client evidence is unavailable. |
| Diagnostic Celery tasks | Retained. Production beat records, manual monitoring, and queued messages were not inspected. |
| `static_volume` declaration | Retained. Merged production overrides are not available; no Docker volumes were deleted. |
| Manifest, Android icons, `.ico` asset | Retained pending the manifest/client-usage decision. |
| jQuery and Animate.css CDN includes | Retained pending comprehensive helper/widget/externally supplied HTML verification. |
| Other dependency/tool declarations and constraints | Retained. No resolver upgrades or removals were applied to the user's virtualenv. |

Initialization scripts, public/minimal routes, registered production tasks,
canonical modals/calendar, package entry points, migrations, live static assets,
QA/design documents, user media, ignored local files, and environment files were
preserved. Production deployment/observation remains a follow-up gate; this
implementation did not publish or change running production services.

### Verification results

- Full suite from `src/django_project`: **221 passed, 62 subtests passed**.
- Full suite from repository root: **221 passed, 62 subtests passed**.
- Bandit: no issues; mypy: no issues in 80 source files; Ruff checks/formatting
  and `git diff --check`: passed.
- Django system checks: no issues. `makemigrations --check --dry-run`: no changes.
- Compared 20 page/viewport captures at 390px and 1280px across home, event/group
  lists/details, calendar, About, Develop, host, and admin login. Main content and
  geometry matched, except the expected host start-time display after restarting
  the isolated server. A lazy-loaded homepage illustration required a second
  capture after image decoding; original versus cleaned CSS then produced
  pixel-identical homepage screenshots at both widths.
- Browser interaction checks cover group carousel keyboard scrolling, canonical
  event/group modals, Escape dismissal, and HTMX/history navigation.
- Built the wheel from a temporary tracked-source copy. Installed the wheel with
  dev+Docker extras in a clean temporary environment, checked the installed
  management command from outside the repository, replayed all migrations into
  a fresh temporary SQLite database, and ran `uv pip check` successfully.
- Collected static assets from the installed wheel into a temporary directory:
  active styles/scripts were present and removed styles/scripts were absent.
  Verified ingestion/image/reminder task registration without connecting to a
  broker or posting messages. Editable installation of the temporary source copy
  and its management command also passed.
- No live ingestion, external notification, media deletion, application database
  migration, or production deployment was performed. The Docker image and live
  web/worker/beat/media service stack were not rebuilt or launched; package/extra
  checks do not replace that staging gate.

**Dependency validation note:** reproducing every installed version as constraints
initially failed because the existing virtualenv has Redis 7.1.0, while
Kombu 5.6.2's Redis extra requires Redis below 6.5. Ordinary `pip check` did not
report this extra-specific mismatch. The clean wheel installation allowed the
resolver to choose Redis 6.4.0; all other captured version constraints were kept.
The user's installed Redis/client configuration was not modified. Since the
effective dependency requirements are unchanged, this is a pre-existing
reproducibility issue to address separately rather than a dependency change in
this cleanup.
