import uuid

import pytest

from app.models import QuoteRequest
from app.services.storage import (
    MAX_PHOTOS,
    UploadValidationError,
    detect_upload_type,
    validate_upload_counts,
)
from app.services.telegram import build_quote_summary


def test_upload_count_limits() -> None:
    validate_upload_counts(MAX_PHOTOS, 2)
    with pytest.raises(UploadValidationError, match=f"up to {MAX_PHOTOS} photos"):
        validate_upload_counts(MAX_PHOTOS + 1, 0)
    with pytest.raises(UploadValidationError, match="up to 2 videos"):
        validate_upload_counts(0, 3)


def test_upload_signatures_are_detected_from_content() -> None:
    assert detect_upload_type("photo", b"\xff\xd8\xff" + bytes(29), "image/jpeg") == (
        "image/jpeg",
        ".jpg",
    )
    assert detect_upload_type(
        "video",
        bytes(4) + b"ftyp" + bytes(24),
        "video/mp4",
    ) == ("video/mp4", ".mp4")


def test_telegram_summary_excludes_direct_customer_identifiers() -> None:
    quote = QuoteRequest(
        id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        name="Alex <Admin>",
        contact="Telegram: @alex&co",
        vehicle="SUV <script>",
        community="Royal Oak & Tuscany",
        concern="Leather & carpet",
        requested_services=["Leather & Care"],
        source="website",
    )

    summary = build_quote_summary(quote)

    assert "#12345678" in summary
    assert "SUV &lt;script&gt;" in summary
    assert "Royal Oak &amp; Tuscany" in summary
    assert "Leather &amp; Care" in summary
    assert "Alex" not in summary
    assert "@alex" not in summary
    assert "Leather &amp; carpet" not in summary
