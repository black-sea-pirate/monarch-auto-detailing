import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.db import get_session
from app.main import app
from app.models import QuoteRequest, QuoteRequestUpload


class FakeSession:
    def __init__(self) -> None:
        self.quote: QuoteRequest | None = None
        self.uploads: list[QuoteRequestUpload] = []

    def add(self, obj: object) -> None:
        if isinstance(obj, QuoteRequest):
            self.quote = obj
        elif isinstance(obj, QuoteRequestUpload):
            self.uploads.append(obj)

    async def get(self, model: type, _: object, **__: object) -> object | None:
        if model is QuoteRequest:
            return self.quote
        return None

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def refresh(self, obj: object) -> None:
        if isinstance(obj, QuoteRequest):
            obj.created_at = datetime.now(UTC)
        elif isinstance(obj, QuoteRequestUpload) and obj.id is None:
            obj.id = uuid.uuid4()


def test_quote_stages_original_photo_then_submits(tmp_path: Path) -> None:
    fake_session = FakeSession()

    async def override_session() -> AsyncIterator[FakeSession]:
        yield fake_session

    original_upload_dir = settings.upload_dir
    settings.upload_dir = tmp_path
    app.dependency_overrides[get_session] = override_session
    try:
        payload = {
            "name": "Alex Driver",
            "contact": "Telegram: @alex",
            "vehicle": "SUV / Crossover",
            "community": "Royal Oak",
            "concern": "Requested services: Maintenance Interior Clean",
            "source": "website",
        }
        with TestClient(app) as client:
            draft_response = client.post("/api/v1/quote-requests", json=payload)
            assert draft_response.status_code == 201
            draft = draft_response.json()
            assert draft["status"] == "uploading"

            upload_response = client.post(
                f"/api/v1/quote-requests/{draft['id']}/uploads",
                data={"kind": "photo"},
                files={"upload": ("interior.jpg", b"\xff\xd8\xff" + bytes(128), "image/jpeg")},
                headers={"X-Upload-Token": draft["upload_token"]},
            )
            assert upload_response.status_code == 201
            assert upload_response.json()["photo_count"] == 1

            submit_response = client.post(
                f"/api/v1/quote-requests/{draft['id']}/submit",
                headers={"X-Upload-Token": draft["upload_token"]},
            )

        assert submit_response.status_code == 200
        assert submit_response.json()["status"] == "stored"
        assert len(fake_session.uploads) == 1
        stored_path = tmp_path / fake_session.uploads[0].stored_name
        assert stored_path.is_file()
        assert stored_path.read_bytes() == b"\xff\xd8\xff" + bytes(128)
    finally:
        app.dependency_overrides.clear()
        settings.upload_dir = original_upload_dir
