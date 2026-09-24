import io

import pytest
from PIL import Image

from apps.stories import imaging


def _jpeg_with_exif() -> bytes:
    img = Image.new("RGB", (1600, 900), (200, 50, 50))
    exif = Image.Exif()
    exif[0x010F] = "SecretCam"  # Make
    exif[0x8825] = {2: (51.0, 30.0, 0.0)}  # GPS IFD
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def test_reencodes_resizes_and_strips_metadata(settings):
    out = imaging.process(_jpeg_with_exif())
    assert out["width"] == imaging.DISPLAY_WIDTH
    for key in ("display", "thumb"):
        img = Image.open(io.BytesIO(out[key]))
        assert img.format == "WEBP"
        assert not img.getexif()
        assert b"SecretCam" not in out[key]
    assert out["dominant_color"].startswith("#")


def test_rejects_non_images_and_polyglots(settings):
    with pytest.raises(imaging.RejectedImage):
        imaging.process(b"<?php system($_GET['c']); ?>")
    with pytest.raises(imaging.RejectedImage):
        imaging.process(b"\x89PNG\r\n\x1a\n" + b"garbage" * 100)  # fake magic bytes


def test_rejects_decompression_bomb(settings):
    settings.UPLOAD_MAX_PIXELS = 1000
    buf = io.BytesIO()
    Image.new("RGB", (100, 100)).save(buf, format="PNG")
    with pytest.raises(imaging.RejectedImage):
        imaging.process(buf.getvalue())
