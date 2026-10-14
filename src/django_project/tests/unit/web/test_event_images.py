"""Provider extraction, bounded downloads, and managed image lifecycle."""

import json
import os
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from model_bakery import baker
from PIL import Image
from web.image_tasks import ingest_event_image, queue_event_image
from web.tasks import ingest_future_eventbrite_events, ingest_future_meetup_events
from web.utilities.event_images import ImageDownloadError, download_event_image, eventbrite_image_url
from web.utilities.scrapers.meetup import _get_event_image

URL = "https://secure.meetupstatic.com/photos/event/example.jpeg"


def image_bytes():
    output = BytesIO()
    Image.new("RGB", (1800, 900), "blue").save(output, format="JPEG")
    return output.getvalue()


class ImageDownloadTests(TestCase):
    def response(self, content):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status_code = 200
        response.headers = {}
        response.iter_content.return_value = [content]
        return response

    @patch("web.utilities.event_images.requests.get")
    def test_download_validates_decodes_and_resizes(self, get):
        get.return_value = self.response(image_bytes())
        result = download_event_image(URL)
        with Image.open(BytesIO(result)) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (1600, 800))
        self.assertFalse(get.call_args.kwargs["allow_redirects"])
        self.assertTrue(get.call_args.kwargs["stream"])

    @patch("web.utilities.event_images.requests.get")
    def test_rejects_untrusted_hosts_and_redirects_before_following(self, get):
        for url in (
            "http://secure.meetupstatic.com/image.jpg",
            "https://127.0.0.1/image.jpg",
            "https://meetupstatic.com.evil.test/image.jpg",
        ):
            with self.assertRaises(ImageDownloadError):
                download_event_image(url)
        get.assert_not_called()
        response = self.response(b"")
        response.status_code = 302
        response.headers = {"Location": "http://localhost/private"}
        get.return_value = response
        with self.assertRaises(ImageDownloadError):
            download_event_image(URL)
        get.assert_called_once()

    @patch("web.utilities.event_images.requests.get")
    def test_rejects_invalid_oversized_or_excessive_pixel_content(self, get):
        get.return_value = self.response(b"<svg>not a raster image</svg>")
        with self.assertRaises(ImageDownloadError):
            download_event_image(URL)
        get.return_value = self.response(image_bytes())
        with patch("web.utilities.event_images.MAX_DOWNLOAD_BYTES", 20), self.assertRaises(ImageDownloadError):
            download_event_image(URL)
        get.return_value = self.response(image_bytes())
        with patch("web.utilities.event_images.MAX_IMAGE_PIXELS", 20), self.assertRaises(ImageDownloadError):
            download_event_image(URL)

    def test_provider_metadata_selects_current_event_and_original_image(self):
        payload = {
            "events": [
                {"__typename": "Event", "id": "999", "featuredEventPhoto": {"source": "wrong"}},
                {
                    "__typename": "Event",
                    "id": "123",
                    "featuredEventPhoto": {"source": URL},
                    "displayPhoto": {"source": "fallback"},
                },
            ]
        }
        soup = BeautifulSoup(f"<script>{json.dumps(payload)}</script>", "html.parser")
        self.assertEqual(_get_event_image(soup, "https://www.meetup.com/example/events/123/"), URL)
        self.assertEqual(
            eventbrite_image_url({"logo": {"original": {"url": "original"}, "url": "thumbnail"}}), "original"
        )
        self.assertEqual(eventbrite_image_url({"image": {"url": "destination-image"}}), "destination-image")
        self.assertEqual(eventbrite_image_url({"logo": None}), "")

    def test_meetup_photo_references_and_display_fallback(self):
        payload = {
            "Event:123": {"__typename": "Event", "id": "123", "featuredEventPhoto": {"__ref": "PhotoInfo:1"}},
            "PhotoInfo:1": {"__typename": "PhotoInfo", "source": URL},
        }
        soup = BeautifulSoup(f"<script>{json.dumps(payload)}</script>", "html.parser")
        self.assertEqual(_get_event_image(soup, "https://www.meetup.com/example/events/123/"), URL)
        payload["Event:123"] = {"__typename": "Event", "id": "123", "displayPhoto": {"source": URL}}
        soup = BeautifulSoup(f"<script>{json.dumps(payload)}</script>", "html.parser")
        self.assertEqual(_get_event_image(soup, "https://www.meetup.com/example/events/123/"), URL)


class ManagedImageTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        media = override_settings(MEDIA_ROOT=self.directory.name)
        media.enable()
        self.addCleanup(media.disable)
        self.event = baker.make("web.Event", image_source_url=URL)

    @patch("web.image_tasks.download_event_image", return_value=b"converted-image")
    def test_saves_image_and_skips_repeat_download(self, download):
        self.assertEqual(ingest_event_image(self.event.pk, URL), "Event image saved.")
        self.event.refresh_from_db()
        self.assertEqual(self.event.image.name, self.event.image_managed_name)
        self.assertEqual(self.event.image_synced_url, URL)
        self.assertTrue(self.event.image.storage.exists(self.event.image.name))
        ingest_event_image(self.event.pk, URL)
        download.assert_called_once()

    @patch("web.image_tasks.download_event_image", return_value=b"converted-image")
    def test_changed_source_replaces_only_managed_file_after_commit(self, download):
        ingest_event_image(self.event.pk, URL)
        self.event.refresh_from_db()
        old_name = self.event.image.name
        new_url = URL + "?version=2"
        self.event.image_source_url = new_url
        self.event.save()
        with self.captureOnCommitCallbacks(execute=True):
            ingest_event_image(self.event.pk, new_url)
        self.event.refresh_from_db()
        self.assertFalse(self.event.image.storage.exists(old_name))
        self.assertTrue(self.event.image.storage.exists(self.event.image.name))

    @patch("web.image_tasks.download_event_image")
    def test_manual_images_and_stale_jobs_are_preserved(self, download):
        self.event.image.save("manual.jpg", ContentFile(b"manual"))
        name = self.event.image.name
        ingest_event_image(self.event.pk, URL)
        ingest_event_image(self.event.pk, URL + "?stale=1")
        self.event.refresh_from_db()
        self.assertEqual(self.event.image.name, name)
        download.assert_not_called()

    @patch("web.image_tasks.download_event_image", side_effect=ImageDownloadError("bad image"))
    def test_invalid_download_retains_previous_image(self, download):
        self.event.image.save("old.jpg", ContentFile(b"old"))
        self.event.image_managed_name = self.event.image.name
        self.event.save()
        old_name = self.event.image.name
        ingest_event_image(self.event.pk, URL)
        self.event.refresh_from_db()
        self.assertEqual(self.event.image.name, old_name)
        self.assertTrue(self.event.image.storage.exists(old_name))

    @patch("web.image_tasks.ingest_event_image.delay")
    def test_download_is_queued_after_commit(self, delay):
        with self.captureOnCommitCallbacks(execute=True):
            queue_event_image(self.event, URL)
            delay.assert_not_called()
        delay.assert_called_once_with(self.event.pk, URL)

    @patch("web.image_tasks.ingest_event_image.delay")
    @patch("web.image_tasks.download_event_image", return_value=b"converted-image")
    def test_synchronous_mode_saves_image_without_worker(self, download, delay):
        with self.captureOnCommitCallbacks(execute=True):
            queue_event_image(self.event, URL, synchronous=True)
            download.assert_not_called()
        self.event.refresh_from_db()
        self.assertTrue(self.event.image.storage.exists(self.event.image.name))
        self.assertEqual(self.event.image_synced_url, URL)
        self.assertEqual(self.event.image_managed_name, self.event.image.name)
        download.assert_called_once_with(URL)
        delay.assert_not_called()

    @patch("web.image_tasks.ingest_event_image.delay")
    @patch("web.image_tasks.download_event_image", side_effect=requests.Timeout("unavailable"))
    def test_synchronous_failure_retries_locally_and_reports_failure(self, download, delay):
        with self.assertLogs("web.image_tasks", level="ERROR"), self.captureOnCommitCallbacks(execute=True):
            queue_event_image(self.event, URL, synchronous=True)
        self.event.refresh_from_db()
        self.assertFalse(self.event.image)
        self.assertFalse(self.event.image_synced_url)
        self.assertEqual(download.call_count, 4)
        delay.assert_not_called()

    @patch("web.tasks.queue_event_image")
    def test_both_ingestion_paths_queue_provider_image(self, queue):
        for platform_name in ("Meetup", "Eventbrite"):
            platform = baker.make("web.SocialPlatform", name=platform_name)
            group = baker.make("web.TechGroup", platform=platform)
            group.links.add(
                baker.make(
                    "web.Link",
                    name=f"{group.name} {platform.name} page",
                    url="https://www.eventbrite.com/o/example-123",
                )
            )
            if platform_name == "Meetup":
                with (
                    patch("web.tasks.get_event_links", return_value=["https://www.meetup.com/example/events/123/"]),
                    patch(
                        "web.tasks.get_event_information",
                        return_value={
                            "name": "Meetup image",
                            "social_platform_id": "123",
                            "start_datetime": "2026-10-20T18:00:00Z",
                            "image_url": URL,
                        },
                    ),
                ):
                    ingest_future_meetup_events(group.pk, synchronous_images=True)
            else:
                item = {
                    "id": "456",
                    "name": {"text": "Eventbrite image"},
                    "start": {"utc": "2026-10-20T18:00:00Z"},
                    "end": {"utc": "2026-10-20T19:00:00Z"},
                    "logo": {"url": "https://img.evbuc.com/example.jpg"},
                }
                with (
                    patch("web.tasks.get_events_for_organization", return_value=[item]),
                    patch("web.tasks.get_event_details", return_value={"tags": []}),
                ):
                    ingest_future_eventbrite_events(group.pk, synchronous_images=True)
            self.assertEqual(queue.call_args.kwargs, {"synchronous": True})
            self.assertEqual(queue.call_args.args[0].group_id, group.pk)
            self.assertEqual(
                queue.call_args.args[1], URL if platform_name == "Meetup" else "https://img.evbuc.com/example.jpg"
            )


class IngestionScriptTests(TestCase):
    def test_script_requests_synchronous_images_for_both_providers(self):
        from web.scripts import ingest_events

        for platform_name, function, task in (
            ("Meetup", ingest_events.get_meetup_events, "ingest_future_meetup_events"),
            ("Eventbrite", ingest_events.get_eventbright_events, "ingest_future_eventbrite_events"),
        ):
            platform = baker.make("web.SocialPlatform", name=platform_name)
            group = baker.make("web.TechGroup", enabled=True, platform=platform)
            with (
                patch(f"web.scripts.ingest_events.{task}.s") as signature,
                patch("web.scripts.ingest_events.time.sleep"),
            ):
                function()
            signature.assert_called_once_with(group.pk, synchronous_images=True)
            signature.return_value.apply.assert_called_once_with(throw=True)
