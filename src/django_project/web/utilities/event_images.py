"""Provider image metadata and bounded downloads for Django media storage."""

from io import BytesIO
from urllib.parse import urlparse

import requests
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000


class ImageDownloadError(ValueError):
    """The provider image cannot be safely decoded or downloaded."""


def eventbrite_image_url(data: dict) -> str:
    for key in ("image", "logo"):
        image = data.get(key)
        if isinstance(image, dict):
            original = image.get("original")
            url = original.get("url") if isinstance(original, dict) else None
            url = url or image.get("url")
            if isinstance(url, str):
                return url
    return ""


def validate_image_url(url: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    allowed = any(host == domain or host.endswith("." + domain) for domain in ("meetupstatic.com", "evbuc.com"))
    if parsed.scheme != "https" or not allowed or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ImageDownloadError("Image URL must use an approved provider HTTPS host")


def download_event_image(url: str) -> bytes:
    """Validate redirects and size, then decode and resize to a metadata-free WebP."""
    for _ in range(4):
        validate_image_url(url)
        with requests.get(url, stream=True, timeout=(5, 20), allow_redirects=False) as response:
            if response.status_code in (301, 302, 303, 307, 308):
                from urllib.parse import urljoin

                url = urljoin(url, response.headers.get("Location", ""))
                continue
            response.raise_for_status()
            try:
                if int(response.headers.get("Content-Length", 0)) > MAX_DOWNLOAD_BYTES:
                    raise ImageDownloadError("Image exceeds download limit")
            except ValueError as exc:
                raise ImageDownloadError("Invalid or oversized image content length") from exc
            content = bytearray()
            for chunk in response.iter_content(chunk_size=65536):
                content.extend(chunk)
                if len(content) > MAX_DOWNLOAD_BYTES:
                    raise ImageDownloadError("Image exceeds download limit")
            break
    else:
        raise ImageDownloadError("Too many image redirects")
    try:
        with Image.open(BytesIO(content)) as original:
            if original.format not in ("JPEG", "PNG", "WEBP") or original.width * original.height > MAX_IMAGE_PIXELS:
                raise ImageDownloadError("Unsupported image format or excessive dimensions")
            image = ImageOps.exif_transpose(original).convert("RGBA")
            image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            output = BytesIO()
            background.save(output, format="WEBP", quality=85)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ImageDownloadError("Invalid image content") from exc
