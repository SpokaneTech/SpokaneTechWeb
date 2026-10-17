# Search discovery implementation and rollout

Updated: October 17, 2026. Implements the repository work approved in the
[SEO and organic traffic plan](SEO_AND_ORGANIC_TRAFFIC_PLAN.md). Production
deployment, account configuration, profile ownership, and publishing remain
operator actions; this document does not claim that they have occurred.

## What changed and why

Public pages now have distinct titles, descriptions, canonical HTTPS URLs, Open
Graph and Twitter previews, and metadata derived from actual events and groups.
The same metadata follows HTMX navigation and history restoration. Content remains
available in the initial server-rendered HTML.

`/sitemap.xml` advertises preferred static pages, enabled groups, and active future
events associated with enabled groups or no group. Past and cancelled events
remain accessible through their existing detail URLs, with accurate content and
links to upcoming events, but are omitted from the sitemap. Disabled groups and
their events are noindexed without changing existing access behavior. Filtered
directories, minimal fragments, calendars, authentication, administration, and
utility pages are noindexed. Canonicals consolidate directory aliases and strip
campaign parameters; `/index/` redirects to `/` for full-page requests.

`robots.txt` reflects the actual `/console/` administration route. Crawler
directives do not provide access control. Full and partial responses vary on
HTMX request headers; shared caches must respect `Vary` rather than serving a
fragment as a full page. A history-cache miss returns the full document.

Two public guides provide original first-meetup and community-selection advice,
with current groups and upcoming events from the database. Detail pages offer
copy-link controls. Campaign-ready notification links are an explicit opt-in,
retain direct provider RSVP links, and do not enable any posting task.

## 1. Configure and deploy the application

1. Back up the production database and retain the prior application image and
   proxy configuration for rollback. Build and release through the existing
   Docker Compose process.
2. Apply migrations using the deployed application's normal management-command
   entry point:

   ```shell
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

   Migration `web.0009_event_search_review` adds one boolean, defaulting to false.
   Existing events, images, tags, status, URLs, and ingestion are preserved.
3. Set these values in the **production** environment used by the web service:

   ```dotenv
   PUBLIC_SITE_URL=https://www.spokanetech.org
   SEO_INDEXING_ENABLED=True
   GA4_MANUAL_PAGE_VIEWS=False
   PROMOTE_SITE_LINKS=False
   SEO_VERIFIED_PROFILE_URLS=
   ```

   `PUBLIC_SITE_URL` is the configured HTTPS origin, with no path, query, or
   credentials. `www` is the implementation default and matches the README;
   confirm certificates, existing links, and Search Console signals before
   release. If a different host is chosen, update this setting and the proxy
   together. Do not derive canonicals from visitor-controlled Host headers.
4. Recreate/restart the affected services so settings take effect. Notification
   services must use the same `PUBLIC_SITE_URL` if promotion is later enabled.
   Leave development and staging `SEO_INDEXING_ENABLED=False`, its default.
   With that value, pages carry noindex, robots disallows crawling, and the
   sitemap contains no URLs. Do not rely on `DEBUG` to control indexing.
5. Keep `POST_TO_DISCORD` and `POST_TO_LINKEDIN` at their existing intended
   values. Nothing in this implementation authorizes a new channel or enables
   posting. `PROMOTE_SITE_LINKS` changes payload links only.

## 2. Consolidate the public hostname at the VPS proxy

The public TLS reverse proxy is not supplied in this repository.
`src/docker/media-nginx.conf` serves media, so editing it would not consolidate
the application hostnames. Apply the equivalent redirect at the proxy that
actually terminates the site's public requests.

For Nginx, the alternate HTTPS server block should retain its valid certificate
and existing TLS settings and return a path/query-preserving redirect:

```nginx
server {
    listen 443 ssl;
    server_name spokanetech.org;
    # Retain this host's existing certificate and TLS configuration here.
    return 308 https://www.spokanetech.org$request_uri;
}
```

This is a configuration fragment, not a replacement for a working TLS server
block. Redirect HTTP variants to the preferred HTTPS origin as well. Keep the
preferred-host application and media routing intact. Validate configuration
before reloading the proxy. Check its Host and scheme forwarding and trusted
proxy boundary before introducing Django HTTPS redirects; this change does not
enable them or assume that every forwarded header is trustworthy.

Check a real event path with a harmless campaign query on both hosts. The alternate
host must redirect to exactly the same path and query on the preferred host, which
must return 200 without a loop. Confirm normal pages, media URLs, calendar modals,
and administrator sign-in still work.

## 3. Review event structured data

Home emits Organization and WebSite data. Event/group detail pages emit
breadcrumbs. Event JSON-LD is emitted only when `event_schema_verified=True`,
the event is public, and a venue name and address are present. Review this field
in Django administration for individual events:

1. Confirm that the listing describes a real, public, physical event, with an
   accurate venue/address, local date/time, and an appropriate public detail page.
   Do not approve an online-only event or a listing whose eligibility is unclear.
2. Check title and description quality against the source. Imported descriptions
   are not evidence that every event meets Google's eligibility rules.
3. Enable the field, save, and inspect the rendered JSON-LD. Dates include the
   Pacific UTC offset. The stored full address is represented without guessing
   missing street/city components. Unknown prices, availability, attendance,
   accessibility, and offers are not invented.
4. Test representative pages in Google's
   [Rich Results Test](https://search.google.com/test/rich-results) and inspect
   them in Search Console after deployment. Fix errors before approving a batch.

Ingestion clears approval when source title, description, venue/address, or source
URL changes. An unchanged poll or cancellation alone retains approval; cancelled
event markup retains the original schedule and reports `EventCancelled`. A human
must re-review other material changes. Review manually edited details as well.
No bulk approval is performed automatically. See
[Google's Event requirements](https://developers.google.com/search/docs/appearance/structured-data/event).

The sitemap deliberately omits `lastmod`: ingestion's `updated_at` can change on
an unchanged poll and is not a reliable content-change timestamp. This follows
[Google's guidance on accurate sitemap dates](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).
Before approaching 50,000 URLs, split the sitemap into indexed sections/pages;
the current flat sitemap is intended for the existing community directory scale.

## 4. Validate analytics before using the scorecard

Use the existing GA4 property and `GOOGLE_ANALYTICS_TAG_ID`. Tags load only for
public pages when production indexing is enabled. Custom events are intent
signals, not proof of attendance or membership:

| Event | Meaning | Parameters supplied by the app |
| --- | --- | --- |
| `rsvp_click` | A user follows an active event's RSVP/source link | Canonical `page_path`, destination `link_domain`, numeric `event_id` |
| `community_link_click` | A group connection or Discord link is followed | Canonical `page_path`, destination `link_domain` |
| `share_click` | A copy-link control is used | Canonical `page_path` |
| `page_view` in manual mode | One public full-page, HTMX, or history navigation | Current title and canonical location, with allowlisted campaign parameters |

1. Inspect the GA4 web stream's Enhanced Measurement settings. The default
   `GA4_MANUAL_PAGE_VIEWS=False` leaves existing automatic page-view behavior
   intact. Do not turn on manual views while browser-history automatic views
   are enabled.
2. If existing automatic history tracking does not provide the correct title,
   URL, and single count, disable its browser-history page views in GA4, then set
   `GA4_MANUAL_PAGE_VIEWS=True` and restart the web service. The initial config
   then suppresses its automatic page view and the app sends explicit views.
   See Google's [single-page application measurement guidance](https://developers.google.com/analytics/devguides/collection/ga4/single-page-applications).
3. In DebugView/Realtime and browser network tools, check a fresh page, HTMX
   event/group navigation, back, forward, and history restoration. Expect one
   intended view for each navigation and the corresponding title/location.
   Opening or dismissing a modal must not count as another page view.
4. Check one RSVP, group connection, Discord, and copy-link action. Preserve the
   existing provider RSVP destination. Do not count generic automatic outbound
   `click` events again when reporting custom RSVP/community actions. Configure
   selected key events only after validating their meaning.
5. Use campaign values such as `utm_source=partner`,
   `utm_medium=organic_social`, and `utm_campaign=weekly_events`. Names should
   contain only letters, numbers, underscores, or hyphens. Do not use email
   addresses, names, tokens, or other personal information in URLs. App-supplied
   locations keep only these validated UTM values; independently audit GA4's
   own automatic collection and property settings for your privacy requirements.

Actual GA4 delivery and account-side settings require owner validation. Local
tests use an intercepted fake tag and do not send measurements to production.

## 5. Check indexing and search accounts

After deployment, check the preferred host:

```shell
curl -sS -D /tmp/spokanetech-home-headers.txt https://www.spokanetech.org/ -o /tmp/spokanetech-home.html
curl -sS https://www.spokanetech.org/robots.txt
curl -sS https://www.spokanetech.org/sitemap.xml
```

Inspect the saved HTML and headers: public pages should have `index, follow`, a
preferred-host canonical, distinct title/description, and no noindex header.
Check representative event/group/guide pages and media images. Utilities,
calendar pages, disabled groups, and HTMX fragments should retain noindex.
Confirm 404s remain 404s and old event/group links still work.

Google ownership setup is complete for planning while verification confirmation
is pending. Keep the Namecheap TXT record. Once access is available, follow the
[ownership setup guide](SEARCH_ENGINE_OWNERSHIP_SETUP.md), export a dated baseline,
submit `https://www.spokanetech.org/sitemap.xml` to Google and Bing, and inspect
representative URLs. Check the chosen canonical and indexing exclusions after
recrawling. Submission and valid markup do not guarantee indexing or rankings.

## 6. Start organic outreach and maintain it

Follow the [outreach playbook](ORGANIC_OUTREACH_PLAYBOOK.md). Establish one owned
channel, preview posts, check current event information, and obtain permission
before posting in anyone else's community. Only then consider enabling
`PROMOTE_SITE_LINKS=True` in notification services. Confirm all existing posting,
credential, duplicate-prevention, retry, and cancellation rules still apply.

Set `SEO_VERIFIED_PROFILE_URLS` only to comma-separated HTTPS profiles that a
maintainer has verified belong to SpokaneTech. Empty is intentional; existing
social links do not prove ownership. Do not add partner profiles as the site's
Organization `sameAs` identities.

Track weekly results in [the scorecard](ORGANIC_TRAFFIC_SCORECARD.csv) and
[outreach register](OUTREACH_REGISTER.csv). Leave unknown counts blank. Establish
a baseline before setting growth targets. Feed subscriptions, new topic hubs,
image variants, and package removal remain optional future work requiring demand
or performance evidence; they are not included in this release.

## Repository validation

Automated coverage in `tests/unit/web/test_seo.py` checks production/staging
indexability, canonical hosts, sitemap contents, metadata parity, HTMX cache and
history behavior, response lengths, JSON escaping, event-review invalidation,
campaign parameters, bounded notification previews, and read-only draft output.
Existing event/group, calendar, ingestion, image, and notification tests are also
part of the regression suite.

An isolated browser check with a temporary SQLite database covered fresh pages,
HTMX transitions, back/forward restoration, correct head metadata and JSON-LD,
copy-link feedback, RSVP/community intent, one manual view per public navigation,
no modal view inflation, and noindex metadata when visiting a disabled group.
Guides and detail pages were checked at 390px and 1280px widths without horizontal
overflow. A fake intercepted GA tag verified the queued events without sending
measurements. These checks do not validate production's proxy, analytics account,
indexing status, or search/social preview services.

## Rollback

For an application regression, restore the prior image and corresponding proxy
configuration through the normal release process; the added boolean can remain
in the database during an application rollback. Set `PROMOTE_SITE_LINKS=False`
to revert promotion links, and coordinate GA4 settings if reverting manual views.
Do not use `SEO_INDEXING_ENABLED=False` as a routine production rollback switch:
it intentionally withdraws the site from crawling/indexing and can affect search
visibility. Keep development/staging safeguards regardless of the release state.
