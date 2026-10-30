# Luma public calendar integration (initial Idaho AI Agents pilot)

Status: **code proposed in PR; not scheduled or deployed**. Tracking: #51, #112, #113.

## Data source and scope

Luma advertises a public, automatically refreshing iCalendar subscription.
The **build_cda** feed used for the initial pilot is:

    https://api.luma.com/ics/get?entity=calendar&id=cal-yFU7dz3kUHXxUDR

Public Luma page: https://luma.com/build_CDA

The calendar is broader than the BuildCities **Idaho AI Agents** network.
As of the captured 2026-10-29 snapshots, the four upcoming Luma events
below were independently confirmed to belong to Idaho AI Agents by comparing
their exact Luma RSVP URLs against a BuildCities network-scoped GraphQL
response. Only those URLs are eligible for the initial import:

- https://luma.com/build-3wx2 (Nov 10, 2026)
- https://luma.com/build-gbf9 (Nov 24, 2026)
- https://luma.com/build-rnaq (Dec 8, 2026)
- https://luma.com/build-vdqc (Dec 22, 2026)

**Never import every event from build_cda into Idaho AI Agents.** For future
events, verify group association first and add each public event permalink as
a new \`Link\` with name \`Idaho AI Agents Luma approved event\`. The
\`Idaho AI Agents Luma feed\` Link holds the calendar subscription. This
allowlist is intentionally conservative, not automatic future discovery.
Additional groups can use the same link naming conventions and parser.

## Data handling

- Parse \`VCALENDAR\` / \`VEVENT\` using the maintained \`icalendar\` library.
- Use stable \`UID\` as \`Event.social_platform_id\` and group-scoped
  \`save_source_event()\`, not a date-bearing BuildCities URL slug.
- Copy only factual fields: title, start/end, city/venue, public RSVP URL.
  The description is an original short pointer back to Luma, **not** an
  excerpt of the hosted event description. Do not download event images.
- Check every imported event has a verified public RSVP URL, a physical
  street address explicitly in Coeur d'Alene, Idaho, and a previously
  authorized link in the matching \`TechGroup\` allowlist.
- In this snapshot all 254 records have \`STATUS:TENTATIVE\` and the same
  \`SEQUENCE\`. **Do not infer cancellation, reinstatement or changed
  status from them, or from missing records**. Follow ADR 0002.
- The iCal file lacks a BuildCities network ID. A host named \`Nick Smoot\`
  is not proof of Idaho AI Agents network membership.
- Suppress outbound creation/change notifications for this pilot, including
  on transactions that commit. Existing other providers are unaffected.

## Setup and validation

1. Run existing \`initialize_data\` via the project's standard
   \`django-extensions runscript\` mechanism. It idempotently seeds the
   \`Luma\` platform and initial group/links. No Django migration is needed.
2. In a review/test environment, make sure outbound LinkedIn/Discord
   publishing is disabled independently of the importer.
3. Once the deployment host can retrieve the public feed with a normal HTTPS
   request and the owner approves a controlled import, run:

       python manage.py shell -c "from web.models import TechGroup; from web.tasks import ingest_future_luma_events; g=TechGroup.objects.get(name='Idaho AI Agents'); print(ingest_future_luma_events(g.pk))"

   This is a manual operation, not a recurring Celery Beat schedule.
4. Verify the four approved UIDs, the corresponding original RSVP links,
   venue and times; rerun and confirm no duplicates.
5. Approve recurring polling separately, respecting the feed's advertised
   12-hour refresh interval. New future occurrences need approved event URLs
   under this conservative network-specific scope.

## Rights and service reliability

A public iCal calendar subscription supports external calendar-client use.
It does not grant a general license to republish full descriptions and images.
Link to the Luma source for registration and event details; confirm any
broader content-use arrangement with the host if needed.

The downloader validates the fixed HTTPS calendar endpoint to avoid SSRF,
limits response size, uses a finite timeout, and preserves previously saved
events if the network or parser fails. Empty or missing events are never
interpreted as cancelled.

The integration is intentionally dormant (no new Beat entry or launcher).
Tests use synthetic .ics samples; no live Luma requests are made by tests.
