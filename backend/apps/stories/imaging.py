"""
Untrusted-image processing. Every upload is fully decoded and re-encoded, which:
  * rejects anything that is not really a JPEG/PNG/WebP (magic bytes, not the filename),
  * guards against decompression bombs (pixel cap),
  * strips EXIF/GPS/XMP metadata (nothing is copied across),
  * neutralises polyglot files (the output bytes are freshly generated),
  * produces display-resolution variants only -- originals are never published,
  * stamps a subtle watermark so lifted images carry attribution.
"""

import io

from django.conf import settings
from PIL import Image, ImageDraw, ImageOps

MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
}
DISPLAY_WIDTH = 1200
THUMB_WIDTH = 480
WATERMARK = "walloffounders"


class RejectedImage(ValueError):
    pass


def sniff(data: bytes) -> str | None:
    for magic, mime in MAGIC.items():
        if data.startswith(magic):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _resize(img: Image.Image, width: int) -> Image.Image:
    if img.width <= width:
        return img.copy()
    height = round(img.height * width / img.width)
    return img.resize((width, height), Image.Resampling.LANCZOS)


def _watermark(img: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(img, "RGBA")
    x, y = img.width - 8 - 6 * len(WATERMARK), img.height - 18
    draw.text((x + 1, y + 1), WATERMARK, fill=(0, 0, 0, 70))
    draw.text((x, y), WATERMARK, fill=(255, 255, 255, 110))
    return img


def _encode(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=82, method=4)  # no exif= argument => no metadata
    return buf.getvalue()


def process(data: bytes) -> dict:
    if len(data) > settings.UPLOAD_MAX_BYTES:
        raise RejectedImage("File too large.")
    if sniff(data) is None:
        raise RejectedImage("Unsupported file type.")

    Image.MAX_IMAGE_PIXELS = settings.UPLOAD_MAX_PIXELS
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()  # structural check
        img = Image.open(io.BytesIO(data))
        if img.width * img.height > settings.UPLOAD_MAX_PIXELS:
            raise RejectedImage("Image dimensions too large.")
        img = ImageOps.exif_transpose(img)  # honour orientation, then drop the EXIF
        img.load()
    except RejectedImage:
        raise
    except (Image.DecompressionBombError, OSError, SyntaxError, ValueError) as exc:
        raise RejectedImage("Corrupt or unsafe image.") from exc

    img = img.convert("RGB")
    display = _watermark(_resize(img, DISPLAY_WIDTH))
    thumb = _resize(img, THUMB_WIDTH)
    r, g, b = thumb.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    return {
        "display": _encode(display),
        "thumb": _encode(thumb),
        "width": display.width,
        "height": display.height,
        "dominant_color": f"#{r:02x}{g:02x}{b:02x}",
    }
