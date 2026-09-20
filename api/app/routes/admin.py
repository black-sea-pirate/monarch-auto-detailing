import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.models import AdminAuditEvent, QuoteRequest, QuoteRequestDelivery, QuoteRequestUpload
from app.schemas import (
    AdminDeliveryRead,
    AdminIdentityRead,
    AdminQuoteDetailRead,
    AdminQuoteListItem,
    AdminQuoteListRead,
    AdminQuoteUploadRead,
)
from app.services.admin_auth import AdminIdentity, require_admin
from app.services.housekeeping import purge_quote_data
from app.services.storage import resolve_upload_path

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
ACTIVE_STATUSES = {"new", "viewed", "accepted"}


def _request_number(quote_id: uuid.UUID) -> str:
    return str(quote_id).split("-", 1)[0].upper()


def _verify_same_origin(request: Request) -> None:
    if settings.app_env == "development":
        return
    origin = request.headers.get("origin")
    expected = settings.admin_base_url.strip().rstrip("/")
    if not origin or not expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request origin.")
    actual_parts = urlsplit(origin)
    expected_parts = urlsplit(expected)
    if (actual_parts.scheme, actual_parts.netloc) != (expected_parts.scheme, expected_parts.netloc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request origin.")


async def require_admin_mutation(
    request: Request,
    identity: Annotated[AdminIdentity, Depends(require_admin)],
) -> AdminIdentity:
    _verify_same_origin(request)
    return identity


def _list_item(
    quote: QuoteRequest,
    delivery: QuoteRequestDelivery | None,
) -> AdminQuoteListItem:
    return AdminQuoteListItem(
        id=quote.id,
        number=_request_number(quote.id),
        name=quote.name,
        vehicle=quote.vehicle,
        community=quote.community,
        requested_services=quote.requested_services or [],
        status=quote.status,
        photo_count=quote.photo_count,
        video_count=quote.video_count,
        created_at=quote.created_at,
        viewed_at=quote.viewed_at,
        accepted_at=quote.accepted_at,
        notification_delivered=bool(delivery and delivery.delivered_at),
    )


async def _active_quote(session: AsyncSession, quote_id: uuid.UUID) -> QuoteRequest:
    quote = await session.get(QuoteRequest, quote_id)
    if quote is None or quote.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    return quote


def _audit(identity: AdminIdentity, action: str, quote_id: uuid.UUID) -> AdminAuditEvent:
    return AdminAuditEvent(admin_email=identity.email, action=action, quote_id=quote_id, details={})


@router.get("/me", response_model=AdminIdentityRead)
async def admin_me(
    identity: Annotated[AdminIdentity, Depends(require_admin)],
    response: Response,
) -> AdminIdentityRead:
    response.headers["Cache-Control"] = "private, no-store"
    return AdminIdentityRead(email=identity.email)


@router.get("/quote-requests", response_model=AdminQuoteListRead)
async def list_quote_requests(
    _: Annotated[AdminIdentity, Depends(require_admin)],
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    state: Literal["all", "new", "viewed", "accepted"] = "all",
    search: Annotated[str, Query(max_length=100)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminQuoteListRead:
    filters = [QuoteRequest.status.in_(ACTIVE_STATUSES)]
    if state != "all":
        filters.append(QuoteRequest.status == state)
    if search.strip():
        value = f"%{search.strip()}%"
        filters.append(
            or_(
                QuoteRequest.name.ilike(value),
                QuoteRequest.contact.ilike(value),
                QuoteRequest.vehicle.ilike(value),
                QuoteRequest.community.ilike(value),
            )
        )

    priority = case(
        (QuoteRequest.status == "new", 0),
        (QuoteRequest.status == "viewed", 1),
        else_=2,
    )
    rows = (
        await session.execute(
            select(QuoteRequest, QuoteRequestDelivery)
            .outerjoin(QuoteRequestDelivery, QuoteRequestDelivery.quote_id == QuoteRequest.id)
            .where(*filters)
            .order_by(priority, QuoteRequest.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    total = await session.scalar(select(func.count()).select_from(QuoteRequest).where(*filters))
    new_count = await session.scalar(
        select(func.count()).select_from(QuoteRequest).where(QuoteRequest.status == "new")
    )
    response.headers["Cache-Control"] = "private, no-store"
    return AdminQuoteListRead(
        items=[_list_item(quote, delivery) for quote, delivery in rows],
        total=total or 0,
        new_count=new_count or 0,
    )


@router.get("/quote-requests/{quote_id}", response_model=AdminQuoteDetailRead)
async def get_quote_request(
    quote_id: uuid.UUID,
    _: Annotated[AdminIdentity, Depends(require_admin)],
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AdminQuoteDetailRead:
    quote = await _active_quote(session, quote_id)
    delivery = await session.get(QuoteRequestDelivery, quote_id)
    uploads = list(
        await session.scalars(
            select(QuoteRequestUpload)
            .where(QuoteRequestUpload.quote_id == quote_id)
            .order_by(QuoteRequestUpload.created_at, QuoteRequestUpload.id)
        )
    )
    item = _list_item(quote, delivery)
    response.headers["Cache-Control"] = "private, no-store"
    return AdminQuoteDetailRead(
        **item.model_dump(),
        contact_method=quote.contact_method,
        contact=quote.contact,
        concern=quote.concern,
        source=quote.source,
        upload_bytes=quote.upload_bytes,
        purge_after=quote.purge_after,
        uploads=[
            AdminQuoteUploadRead(
                id=upload.id,
                kind=upload.kind,
                original_name=upload.original_name,
                content_type=upload.content_type,
                size_bytes=upload.size_bytes,
                url=f"/api/v1/admin/quote-requests/{quote.id}/uploads/{upload.id}",
            )
            for upload in uploads
        ],
        delivery=AdminDeliveryRead(
            delivered=bool(delivery and delivery.delivered_at),
            attempts=delivery.attempts if delivery else 0,
            last_error=delivery.last_error if delivery else None,
            last_attempt_at=delivery.last_attempt_at if delivery else None,
        ),
    )


@router.get("/quote-requests/{quote_id}/uploads/{upload_id}")
async def get_quote_upload(
    quote_id: uuid.UUID,
    upload_id: uuid.UUID,
    _: Annotated[AdminIdentity, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FileResponse:
    await _active_quote(session, quote_id)
    upload = await session.get(QuoteRequestUpload, upload_id)
    if upload is None or upload.quote_id != quote_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    path = resolve_upload_path(upload.stored_name)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return FileResponse(
        path,
        media_type=upload.content_type,
        filename=upload.original_name,
        content_disposition_type="inline",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/quote-requests/{quote_id}/view", status_code=status.HTTP_204_NO_CONTENT)
async def mark_quote_viewed(
    quote_id: uuid.UUID,
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    quote = await _active_quote(session, quote_id)
    if quote.status == "new":
        quote.status = "viewed"
        quote.viewed_at = datetime.now(UTC)
        session.add(_audit(identity, "quote_viewed", quote_id))
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/quote-requests/{quote_id}/unread", status_code=status.HTTP_204_NO_CONTENT)
async def mark_quote_unread(
    quote_id: uuid.UUID,
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    quote = await _active_quote(session, quote_id)
    if quote.status == "accepted":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Accepted requests cannot be unread.")
    quote.status = "new"
    quote.viewed_at = None
    session.add(_audit(identity, "quote_marked_unread", quote_id))
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/quote-requests/{quote_id}/accept", status_code=status.HTTP_204_NO_CONTENT)
async def accept_quote_request(
    quote_id: uuid.UUID,
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    quote = await _active_quote(session, quote_id)
    if quote.status != "accepted":
        now = datetime.now(UTC)
        quote.status = "accepted"
        quote.viewed_at = quote.viewed_at or now
        quote.accepted_at = now
        quote.purge_after = now + timedelta(days=settings.quote_accepted_retention_days)
        session.add(_audit(identity, "quote_accepted", quote_id))
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/quote-requests/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote_request(
    quote_id: uuid.UUID,
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    quote = await _active_quote(session, quote_id)
    await purge_quote_data(session, quote, final_status="deleted_purged")
    session.add(_audit(identity, "quote_deleted", quote_id))
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
