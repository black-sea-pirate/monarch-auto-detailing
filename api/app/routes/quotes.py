import hashlib
import secrets
import uuid
from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import QuoteRequest, QuoteRequestUpload
from app.schemas import (
    QuoteRequestCreate,
    QuoteRequestDraftRead,
    QuoteRequestRead,
    QuoteRequestUploadRead,
)
from app.services.storage import (
    MAX_PHOTOS,
    MAX_VIDEOS,
    UploadValidationError,
    purge_stored_upload,
    store_quote_upload,
)
from app.services.telegram import deliver_quote

router = APIRouter(prefix="/api/v1/quote-requests", tags=["quote requests"])


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _verify_upload_token(quote: QuoteRequest, token: str) -> None:
    supplied_hash = _token_hash(token)
    if not quote.upload_token_hash or not secrets.compare_digest(
        supplied_hash,
        quote.upload_token_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This upload session is not valid.",
        )
    if quote.status != "uploading":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This request has already been submitted.",
        )


async def _get_locked_quote(
    session: AsyncSession,
    quote_id: uuid.UUID,
    upload_token: str,
) -> QuoteRequest:
    quote = await session.get(QuoteRequest, quote_id, with_for_update=True)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    _verify_upload_token(quote, upload_token)
    return quote


@router.post("", response_model=QuoteRequestDraftRead, status_code=status.HTTP_201_CREATED)
async def create_quote_request(
    payload: Annotated[QuoteRequestCreate, Body()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuoteRequestDraftRead:
    upload_token = secrets.token_urlsafe(32)
    quote_request = QuoteRequest(
        id=uuid.uuid4(),
        **payload.model_dump(),
        status="uploading",
        upload_token_hash=_token_hash(upload_token),
        photo_count=0,
        video_count=0,
        upload_bytes=0,
    )
    session.add(quote_request)
    try:
        await session.commit()
        await session.refresh(quote_request)
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Quote storage is not available.",
        ) from exc

    return QuoteRequestDraftRead(
        id=quote_request.id,
        status=quote_request.status,
        created_at=quote_request.created_at,
        upload_token=upload_token,
    )


@router.post(
    "/{quote_id}/uploads",
    response_model=QuoteRequestUploadRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_quote_media(
    quote_id: uuid.UUID,
    kind: Annotated[Literal["photo", "video"], Form()],
    upload: Annotated[UploadFile, File()],
    upload_token: Annotated[str, Header(alias="X-Upload-Token")],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuoteRequestUploadRead:
    quote = await _get_locked_quote(session, quote_id, upload_token)
    next_photo_count = quote.photo_count + (1 if kind == "photo" else 0)
    next_video_count = quote.video_count + (1 if kind == "video" else 0)
    if next_photo_count > MAX_PHOTOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"You can attach up to {MAX_PHOTOS} photos.",
        )
    if next_video_count > MAX_VIDEOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"You can attach up to {MAX_VIDEOS} videos.",
        )

    try:
        stored = await store_quote_upload(quote.id, upload, kind, quote.upload_bytes)
    except UploadValidationError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc

    upload_row = QuoteRequestUpload(
        quote_id=quote.id,
        kind=stored.kind,
        original_name=stored.original_name,
        stored_name=stored.stored_name,
        content_type=stored.content_type,
        size_bytes=stored.size_bytes,
    )
    session.add(upload_row)
    quote.photo_count = next_photo_count
    quote.video_count = next_video_count
    quote.upload_bytes += stored.size_bytes
    try:
        await session.commit()
        await session.refresh(upload_row)
    except SQLAlchemyError as exc:
        await session.rollback()
        await purge_stored_upload(stored.stored_name)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The uploaded file could not be recorded.",
        ) from exc

    return QuoteRequestUploadRead(
        id=upload_row.id,
        kind=kind,
        original_name=stored.original_name,
        size_bytes=stored.size_bytes,
        photo_count=quote.photo_count,
        video_count=quote.video_count,
        total_bytes=quote.upload_bytes,
    )


@router.post("/{quote_id}/submit", response_model=QuoteRequestRead)
async def submit_quote_request(
    quote_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    upload_token: Annotated[str, Header(alias="X-Upload-Token")],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuoteRequest:
    quote = await _get_locked_quote(session, quote_id, upload_token)
    quote.status = "stored"
    quote.upload_token_hash = ""
    try:
        await session.commit()
        await session.refresh(quote)
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The request could not be submitted.",
        ) from exc

    background_tasks.add_task(deliver_quote, quote.id)
    return quote
