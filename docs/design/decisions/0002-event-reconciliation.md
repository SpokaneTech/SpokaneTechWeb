# Event changes, cancellations, and reconciliation

Status: accepted. Date: 2026-10-16.

## Context

Discovery alone is insufficient for keeping events current: a cancelled event
may disappear from upcoming listings, and a rescheduled event may move outside
the discovery window. A missing listing, 404, failed request, or incomplete HTML
page does not establish that an event was cancelled.

## Decision

Retain events and store explicit `active`/`cancelled` status. Existing records
migrate to active; this migration does not infer historical cancellations.
Store `source_last_checked_at` when a usable source snapshot is merged. Do not
advance it for failed or empty responses. Admin exposes status and the last
successful check. The default manager continues to include cancelled records
so direct links, admin, and historical records remain available.

Both existing ingestion jobs now combine discovery with rechecking stored
future events for that group, including previously cancelled future events:

- Meetup reuses stored event URLs, or reconstructs a URL from a numeric ID and
  the configured group link. It reads explicit cancellation/scheduled status
  from the requested event's embedded JSON or matching JSON-LD. Recommended
  events and unrelated statuses cannot cancel the requested event.
- Eventbrite discovery follows all result pages. Known IDs missing from discovery
  are fetched directly from the authenticated event endpoint using the existing
  `EVENTBRITE_API_KEY`, outside the discovery date window.
- Source errors are logged per request. Known records are retained and other
  events continue processing. Listing failures still permit direct rechecks.
- Events are matched within their group by provider ID, or by the existing
  name/start-time fallback when no ID is available. Group-row locks serialize
  ingestion, including creation, on databases supporting row-level locking.
- A cancellation requires explicit provider evidence. A cancelled event becomes
  active again only after explicit scheduled/live/published evidence. Missing
  or unknown status never reinstates it.

Missing or invalid metadata is preserved rather than treated as deletion.
Venue fields update together when enough data is available; an unconfirmed empty
or partial venue cannot erase a confirmed venue. Explicit online events and
Meetup's explicit TBD venue can clear obsolete physical location/map fields.
Dates must be timezone-aware. A cancellation-only snapshot can update an existing
record, but a new record needs a name and valid start time.

Imported tag names are tracked separately. Subsequent authoritative topic lists
remove obsolete imported topics and preserve unrelated locally assigned topics.
Missing topic data leaves tags unchanged. Existing tags are initially treated as
local because the migration cannot establish their provenance. A topic that is
both manually assigned and subsequently imported shares one relationship; there
is no separate per-assignment ownership for that same topic.

## Display and notifications

Cancelled events are excluded from the homepage, upcoming directory, calendar,
upcoming group events, upcoming counts/topics, reminders, and weekly summaries.
Their detail and modal URLs remain available with a cancellation notice and no
RSVP button. Past group events remain as history and show cancelled labels.

Changes to title, date/time, venue/address/map, source URL, or status queue
explicit update/cancellation/reinstatement messages after transaction commit.
Description-only, image, tag, and last-check changes do not generate announcements.
Identical ingestions do not generate another change message. `change_version`
allows workers to discard queued messages superseded by a newer change. Update
messages use factual text rather than AI-generated invitations.

Discord and LinkedIn respect their existing posting settings and credentials.
Cancelled events are also checked at worker execution time so queued creation
posts/reminders cannot promote them. SPUG's existing create-only integration is
retained; this change does not invent an upstream update/delete API.

Notifications retain the existing Celery delivery model, not a transactional
outbox: broker/provider failures can still prevent delivery, and externally
published creation posts are not edited or deleted. No live ingestion or social
posts are required to deploy this change.

## Operation and limits

Apply migration 0008 with `python manage.py migrate`. The existing scheduled
launchers now perform reconciliation on every run; no additional beat schedule
is required. Actual refresh frequency remains the configured beat frequency.
`python manage.py runscript ingest_events` invokes the same ingestion synchronously
and continues to download images inline; notification tasks still use Celery.

Deploy migrations before restarting web/worker/beat processes on the new code.
Provider rechecks increase requests per ingestion run. Monitor task duration and
source-error logs for large groups. Stored events without usable source identity
cannot be rechecked reliably. Events whose stored start time is already past are
not periodically rechecked by this future-event job.

A deleted/private Meetup page may expose no cancellation status at all. Such
records remain unchanged; inspect the source and set status in admin when needed.
Likewise, Eventbrite authentication errors and missing/inaccessible events do not
prove cancellation. This deliberately favors retaining a record over inventing
a cancellation.

## Validation

Regression coverage includes disappearing listings, source failures, explicit
cancellation/reinstatement, partial locations, rescheduling identity, group-scoped
IDs, authoritative versus missing topics, pagination, notification settings,
transaction rollback, obsolete queued jobs, and cancelled-event visibility.
All network and publishing calls in automated tests are mocked.

Provider references: [Eventbrite event status](https://www.eventbrite.com.au/platform/docs/events),
[Eventbrite pagination](https://www.eventbrite.co.uk/platform/new/api),
[Meetup cancellation behavior](https://help.meetup.com/hc/en-us/articles/360002881471-Canceling-an-event).

Validation results: full suite **214 tests and 42 subtests passed**, with Ruff,
formatting, and `mypy src` (79 files). Migration 0008 applied successfully to an
isolated database copy. Chromium checked cancellation detail/modal notices,
RSVP removal, no horizontal overflow, and Escape dismissal at 390, 768, and
1280px. No live provider ingestion or outbound social posting was performed.
