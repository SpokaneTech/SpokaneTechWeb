# ADR 0001: Persistent filesystem storage for event images

- Status: Accepted
- Date: 2026-10-13
- Scope: Meetup/Eventbrite image ingestion and the single-VPS Docker Compose deployment

## Context

SpokaneTech runs Django and Celery in Docker Compose on one VPS without an object
store. Events already have an `image` ImageField, and the shared cards display
that image before falling back to a group image or placeholder. Provider URLs
should not be used as the site's permanent image storage. Downloads must not
block event metadata ingestion or overwrite editor uploads.

## Decision

Use Django's filesystem storage and a persistent named Docker volume,
`spokanetech_media`. Django and the Celery worker mount it read/write at
`/app/media`; a separate Nginx `media` service mounts it read-only at `/srv/media`.
The media service listens on host loopback port 8081. The existing VPS reverse
proxy forwards `/media/` to it. This keeps Django out of production file serving
and avoids requiring host Nginx to locate Docker-managed volume directories.

A named volume survives container replacement and can be shared by these
containers on the same VPS. It does not provide replication or protection from
VPS/disk loss, and it must be included in off-host backups. This follows Docker's
[volume lifecycle and sharing model](https://docs.docker.com/engine/storage/volumes/).

Django uses `MEDIA_ROOT` and `MEDIA_URL` with its default storage backend, rather
than writing files directly to arbitrary paths. See Django's
[file storage documentation](https://docs.djangoproject.com/en/5.2/topics/files/).
No new Python dependency or external storage account is required; Pillow is
already installed. Static assets and uploaded media remain separate.

## Ingestion behavior

1. Meetup extracts the requested event's `featuredEventPhoto.source`, with
   `displayPhoto.source` as a fallback. Group/recommended event images are excluded.
2. Eventbrite reads destination `image` or API `logo` metadata, preferring the
   original URL. The organizer-list response supplies a fallback when necessary.
3. Scheduled ingestion queues `web.ingest_event_image` after the database commit.
   The standalone `runscript ingest_events` explicitly requests synchronous images:
   the same image task executes locally after commit and finishes before the
   script returns, without an image worker or image task publication to the broker.
   Both modes retry transient HTTP/storage errors up to three times. Synchronous
   retry failures are logged while retaining the saved event metadata.
4. Downloads accept only HTTPS URLs on Meetup/Eventbrite image CDN domains;
   redirects are revalidated. Requests have connection/read timeouts, a 10 MiB
   byte limit, and a 20-million-pixel limit. Only JPEG, PNG, and WebP are decoded.
5. Images are resized within 1600 × 1600, preserving aspect ratio, normalized to
   WebP, and saved through `Event.image` under `tech_events/`. Transparency is
   flattened onto white and source metadata is omitted.
6. An unchanged source with an existing managed file is skipped. Changed sources
   replace managed files, and the previous managed file is deleted after commit.
   Missing files are downloaded again on the next ingestion.
7. Missing source images and rejected downloads retain the existing image. If
   there is no image, existing template fallbacks continue to work.

Migration `0007` adds:

| Field | Purpose |
| --- | --- |
| `image_source_url` | Latest accepted provider URL requested by ingestion |
| `image_synced_url` | Source URL of the successfully saved file |
| `image_managed_name` | Storage filename owned by image ingestion |

An image whose filename differs from `image_managed_name` is treated as an editor
upload and is preserved. Clearing an image allows ingestion to populate it again.
The task rechecks ownership and source URL under a row lock after downloading,
so an obsolete job cannot overwrite an editor's replacement or a newer source.
Image updates do not trigger event-announcement signals.

The image task is registered when Celery discovers `web.tasks`, which imports
`web.image_tasks`. No separate queue or beat schedule is required. Existing
future events pick up images on their next provider ingestion. Historical events
outside the ingestion window are not automatically backfilled.

A stable source URL is treated as unchanged; replacing its bytes without changing
its URL is not automatically detected. To refresh that image, clear
`image_synced_url` or the saved image and re-run normal ingestion.

## Local development

Default settings are `MEDIA_ROOT=<django_project>/media` and `MEDIA_URL=/media/`.
Override `MEDIA_ROOT` in the local environment if desired. With `DEBUG=True`,
Django's development server serves `/media/`. Uploaded files are ignored by Git.

Apply migrations before running ingestion:

```bash
python src/django_project/manage.py migrate
```

From the directory containing `manage.py`, run:

```bash
./manage.py runscript ingest_events
```

This command captures metadata and downloads provider images synchronously. The
`image_synced_url` and `image_managed_name` fields are populated only after a
successful download/save. Image failures are logged; the existing image and
metadata remain intact. Re-running ingestion retries missing images and skips
unchanged saved images. Scheduled background ingestion still requires a Celery
worker. Existing event-announcement scheduling follows its separate settings.

Tests use temporary media directories and mocked HTTP/Celery calls. They do not
post messages, download real images, or write into production media.

## VPS rollout

The checked-in Compose file and `src/docker/media-nginx.conf` implement the mounts
and media service. Compose explicitly sets `/app/media` and `/media/` for Django
and the worker. `MEDIA_HTTP_PORT` can override 8081 through Compose interpolation
(the shell or Compose's `.env` file, not a service's `env_file`). Keep the proxy
upstream port in sync. File permissions must allow Django/Celery to write and
Nginx to read; if changing container user IDs, adjust volume ownership accordingly.

Before replacing old containers, locate and copy any existing uploads into the
new media volume, preserving the `tech_events/` and `techgroups/` paths recorded
in the database. Legacy uploads with no configured MEDIA_ROOT may be in the
application working directory. Back up the database and files first.

After building/pulling the updated application image, stop ingestion workers,
apply the migration, and recreate services with the shared volume:

```bash
docker compose --env-file src/envs/.env.docker-compose -f src/docker/docker-compose.yaml stop worker beat
docker compose --env-file src/envs/.env.docker-compose -f src/docker/docker-compose.yaml run --rm django python manage.py migrate
docker compose --env-file src/envs/.env.docker-compose -f src/docker/docker-compose.yaml up -d django worker beat media
```

If the VPS reverse proxy is Nginx, add this location to its existing HTTPS server,
then validate and reload that proxy using the normal deployment procedure:

```nginx
location /media/ {
    proxy_pass http://127.0.0.1:8081;
}
```

For another reverse proxy, configure the equivalent `/media/` route to the same
loopback upstream. The proxy must preserve `/media/` in the upstream request. For a containerized reverse
proxy on the same Compose network, use `http://media:80` instead. If the proxy is
in another Compose project, explicitly connect it to a shared network. The media
service is not publicly exposed on its own. Directory listing is disabled, and
non-media paths return 404. Generated filenames change on replacement, allowing
seven-day response caching without serving stale replacements.

The Compose update also declares the previously referenced `redis_data` volume
and puts Redis on the same default Compose network as Django and Celery, replacing
its undeclared isolated network reference.

Verify a saved image returns HTTP 200 from both the media service and public site,
that both app services see the same file, and that a container recreation retains
it. These VPS operations are deployment steps, not performed by the code update.

## Backup and recovery

Back up the database and the complete `spokanetech_media` volume together. Pause
image-writing workers during the snapshot to keep file replacements consistent.
Store copies off the VPS. For example, with `/srv/backups/spokanetech` already
created on the host:

```bash
docker run --rm \
  -v spokanetech_media:/media:ro \
  -v /srv/backups/spokanetech:/backup \
  alpine tar czf /backup/media-backup.tgz -C /media .
```

Use a dated destination filename in the actual backup job. Restore the archive
into an empty media volume and restore the matching database before restarting
writers. Restore tests should check that stored image paths resolve. Avoid
`docker compose down -v` and volume-pruning operations that remove this volume.

## Alternatives and consequences

A host bind mount also works, but the named volume avoids dependence on a specific
VPS directory layout. Object storage adds no needed capability for the current
single-host deployment and can be introduced later through Django's storage API.
Hotlinking avoids local disk use but leaves image delivery dependent on external
URLs. Saving only a source URL would not satisfy the persistence requirement.

Disk usage must be monitored. Managed files are cleaned up on replacement, but
manual uploads and images belonging to deleted events are not automatically
removed. Storage writes are not database-transactional; exceptional commit/cleanup
failures can leave orphan files. A future maintenance command can reconcile those
files after checking database references. Multiple VPS workers would require
shared storage or object storage rather than independent local volumes.

## Implementation validation

The full suite passed with 180 tests and 26 subtests, including worker-free
synchronous image saving, local retry/failure reporting, script mode selection
for both providers, and default background queuing.
Coverage includes both ingestion paths, photo fallback/references, decoding and
resizing, host/redirect validation, byte/pixel limits, manual-image preservation,
unchanged-source skipping, replacement cleanup, invalid-download preservation,
and post-commit queuing. `mypy src`, Ruff, formatting, migration drift checks, and
`git diff --check` passed. Compose configuration validated using non-secret test
environment values. The VPS proxy, running Nginx container, and production volume
backup/restore remain rollout checks; this implementation does not deploy them.
