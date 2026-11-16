# Luma public calendar integration (initial Idaho AI Agents pilot)

Status: **code proposed in PR; not scheduled or deployed**. Tracking: #51, #112, #113.

## Data source and scope

Luma advertises a public, automatically refreshing iCalendar subscription.
The **build_cda** feed used for the initial pilot is:

    https://api.luma.com/ics/get?entity=calendar&id=cal-yFU7dz3kUHXxUDR

Public Luma page: https://luma.com/build_CDA

All upcoming events in the configured calendar are imported into its TechGroup,
including online events and events outside Coeur d'Alene. This calendar-wide
scope is intentional; individual event approval links are no longer required.
The `Idaho AI Agents Luma feed` Link holds the calendar subscription.
Additional groups can use the same link naming conventions and parser.

## Data handling

- Parse `VCALENDAR` / `VEVENT` using the maintained `icalendar` library.
- Use stable `UID` as `Event.social_platform_id` and group-scoped
  `save_source_event()`, not a date-bearing BuildCities URL slug.
- Copy only factual fields: title, start/end, city/venue, public RSVP URL.
  The description is an original short pointer back to Luma, **not** an
  excerpt of the hosted event description. Do not download event images.
- Require a public Luma RSVP URL and a valid timezone-aware start time.
  Missing locations do not prevent import or erase an existing location.
- In this snapshot all 254 records have `STATUS:TENTATIVE` and the same
  `SEQUENCE`. **Do not infer cancellation, reinstatement or changed
  status from them, or from missing records**. Follow ADR 0002.
- Suppress outbound creation/change notifications for this pilot, including
  on transactions that commit. Existing other providers are unaffected.

## Setup and validation

1. Run existing `initialize_data` via the project's standard
   `django-extensions runscript` mechanism. It idempotently seeds the
   `Luma` platform and initial group/links. No Django migration is needed.
2. In a review/test environment, make sure outbound LinkedIn/Discord
   publishing is disabled independently of the importer.
3. Once the deployment host can retrieve the public feed with a normal HTTPS
   request and the owner approves a controlled import, run:

       python manage.py shell -c "from web.models import TechGroup; from web.tasks import ingest_future_luma_events; g=TechGroup.objects.get(name='Idaho AI Agents'); print(ingest_future_luma_events(g.pk))"

   This is a manual operation, not a recurring Celery Beat schedule.
4. Verify upcoming calendar events, their RSVP links, locations and times;
   rerun and confirm no duplicates.
5. Approve recurring polling separately, respecting the feed's advertised
   12-hour refresh interval. New future occurrences are discovered automatically.

## Rights and service reliability

A public iCal calendar subscription supports external calendar-client use.
It does not grant a general license to republish full descriptions and images.
Link to the Luma source for registration and event details; confirm any
broader content-use arrangement with the host if needed.

The downloader validates the fixed HTTPS calendar endpoint to avoid SSRF,
limits response size, uses a finite timeout, and preserves previously saved
events if the network or parser fails. Empty or missing events are never
interpreted as cancelled.

`web.scripts.ingest_events.run()` includes Luma ingestion. The Celery task
`web.launch_luma_event_ingestion` queues ingestion for every enabled Luma group.
No recurring Beat entry is configured by this integration.
Tests use synthetic .ics samples; no live Luma requests are made by tests.
