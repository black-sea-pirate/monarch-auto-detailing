import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.models import (
    AdminAuditEvent,
    PortfolioImage,
    QuoteRequest,
    QuoteRequestDelivery,
    QuoteRequestUpload,
    SiteSettings,
)
from app.schemas import (
    AdminDeliveryRead,
    AdminIdentityRead,
    AdminQuoteDetailRead,
    AdminQuoteListItem,
    AdminQuoteListRead,
    AdminQuoteUploadRead,
    PortfolioImageRead,
    PortfolioImageUpdate,
    SiteSettingsRead,
    SiteSettingsUpdate,
)
from app.services.admin_auth import AdminIdentity, require_admin
from app.services.housekeeping import purge_quote_data
from app.services.storage import (
    UploadValidationError,
    purge_portfolio_image,
    resolve_site_media_path,
    resolve_upload_path,
    store_portfolio_image,
)
from app.site_defaults import DEFAULT_PRICING, DEFAULT_SECTIONS

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


def _audit(
    identity: AdminIdentity,
    action: str,
    quote_id: uuid.UUID | None = None,
    details: dict[str, object] | None = None,
) -> AdminAuditEvent:
    return AdminAuditEvent(
        admin_email=identity.email,
        action=action,
        quote_id=quote_id,
        details=details or {},
    )


def _site_settings_read(row: SiteSettings | None) -> SiteSettingsRead:
    return SiteSettingsRead(
        pricing=row.pricing if row else DEFAULT_PRICING,
        sections=row.sections if row else DEFAULT_SECTIONS,
        version=row.version if row else 1,
        updated_at=row.updated_at if row else None,
        updated_by=row.updated_by if row else None,
    )


def _portfolio_image_read(image: PortfolioImage) -> PortfolioImageRead:
    return PortfolioImageRead(
        id=image.id,
        original_name=image.original_name,
        after_original_name=image.after_original_name,
        caption=image.caption,
        sort_order=image.sort_order,
        is_enabled=image.is_enabled,
        size_bytes=image.size_bytes,
        after_size_bytes=image.after_size_bytes,
        url=f"/api/v1/admin/portfolio-images/{image.id}/file",
        after_url=(
            f"/api/v1/admin/portfolio-images/{image.id}/after-file"
            if image.after_stored_name
            else None
        ),
        created_at=image.created_at,
    )


@router.get("/me", response_model=AdminIdentityRead)
async def admin_me(
    identity: Annotated[AdminIdentity, Depends(require_admin)],
    response: Response,
) -> AdminIdentityRead:
    response.headers["Cache-Control"] = "private, no-store"
    return AdminIdentityRead(email=identity.email)


@router.get("/site-settings", response_model=SiteSettingsRead)
async def get_site_settings(
    _: Annotated[AdminIdentity, Depends(require_admin)],
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SiteSettingsRead:
    response.headers["Cache-Control"] = "private, no-store"
    return _site_settings_read(await session.get(SiteSettings, 1))


@router.put("/site-settings", response_model=SiteSettingsRead)
async def update_site_settings(
    payload: SiteSettingsUpdate,
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SiteSettingsRead:
    row = await session.get(SiteSettings, 1)
    current_version = row.version if row else 1
    if payload.version != current_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="These settings changed in another window. Reload and try again.",
        )
    if row is None:
        row = SiteSettings(id=1, pricing={}, sections={}, version=1)
        session.add(row)
    row.pricing = {key: value.model_dump(mode="json") for key, value in payload.pricing.items()}
    row.sections = payload.sections.model_dump(mode="json")
    row.version = current_version + 1
    row.updated_by = identity.email
    session.add(
        _audit(
            identity,
            "site_settings_updated",
            details={"version": row.version},
        )
    )
    await session.commit()
    await session.refresh(row)
    response.headers["Cache-Control"] = "private, no-store"
    return _site_settings_read(row)


@router.get("/portfolio-images", response_model=list[PortfolioImageRead])
async def list_portfolio_images(
    _: Annotated[AdminIdentity, Depends(require_admin)],
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PortfolioImageRead]:
    images = list(
        await session.scalars(
            select(PortfolioImage).order_by(
                PortfolioImage.sort_order,
                PortfolioImage.created_at,
            )
        )
    )
    response.headers["Cache-Control"] = "private, no-store"
    return [_portfolio_image_read(image) for image in images]


@router.post(
    "/portfolio-images",
    response_model=PortfolioImageRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_portfolio_image(
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    session: Annotated[AsyncSession, Depends(get_session)],
    image: Annotated[UploadFile, File()],
    after_image: Annotated[UploadFile | None, File()] = None,
    caption: Annotated[str, Form(max_length=240)] = "",
    is_enabled: Annotated[bool, Form()] = True,
) -> PortfolioImageRead:
    stored = None
    stored_after = None
    try:
        stored = await store_portfolio_image(image)
        if after_image is not None and after_image.filename:
            stored_after = await store_portfolio_image(after_image)
    except UploadValidationError as exc:
        if stored is not None:
            await purge_portfolio_image(stored.stored_name)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception:
        if stored is not None:
            await purge_portfolio_image(stored.stored_name)
        raise

    next_order = (
        await session.scalar(select(func.coalesce(func.max(PortfolioImage.sort_order), -1)))
    ) + 1
    row = PortfolioImage(
        id=uuid.uuid4(),
        original_name=stored.original_name,
        stored_name=stored.stored_name,
        content_type=stored.content_type,
        size_bytes=stored.size_bytes,
        after_original_name=stored_after.original_name if stored_after else None,
        after_stored_name=stored_after.stored_name if stored_after else None,
        after_content_type=stored_after.content_type if stored_after else None,
        after_size_bytes=stored_after.size_bytes if stored_after else None,
        caption=caption.strip() or None,
        sort_order=next_order,
        is_enabled=is_enabled,
    )
    session.add(row)
    session.add(
        _audit(
            identity,
            "portfolio_image_uploaded",
            details={"image_id": str(row.id), "original_name": stored.original_name},
        )
    )
    try:
        await session.commit()
        await session.refresh(row)
    except Exception:
        await session.rollback()
        await purge_portfolio_image(stored.stored_name)
        if stored_after is not None:
            await purge_portfolio_image(stored_after.stored_name)
        raise
    return _portfolio_image_read(row)


@router.get("/portfolio-images/{image_id}/file")
async def get_admin_portfolio_image(
    image_id: uuid.UUID,
    _: Annotated[AdminIdentity, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FileResponse:
    image = await session.get(PortfolioImage, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    path = resolve_site_media_path(image.stored_name)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    return FileResponse(
        path,
        media_type=image.content_type,
        content_disposition_type="inline",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/portfolio-images/{image_id}/after-file")
async def get_admin_portfolio_after_image(
    image_id: uuid.UUID,
    _: Annotated[AdminIdentity, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FileResponse:
    image = await session.get(PortfolioImage, image_id)
    if image is None or not image.after_stored_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    path = resolve_site_media_path(image.after_stored_name)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    return FileResponse(
        path,
        media_type=image.after_content_type or "image/jpeg",
        content_disposition_type="inline",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/portfolio-images/{image_id}/after", response_model=PortfolioImageRead)
async def upload_portfolio_after_image(
    image_id: uuid.UUID,
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    session: Annotated[AsyncSession, Depends(get_session)],
    image: Annotated[UploadFile, File()],
) -> PortfolioImageRead:
    row = await session.get(PortfolioImage, image_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    try:
        stored = await store_portfolio_image(image)
    except UploadValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    previous_stored_name = row.after_stored_name
    row.after_original_name = stored.original_name
    row.after_stored_name = stored.stored_name
    row.after_content_type = stored.content_type
    row.after_size_bytes = stored.size_bytes
    session.add(
        _audit(
            identity,
            "portfolio_after_image_uploaded",
            details={"image_id": str(row.id), "original_name": stored.original_name},
        )
    )
    try:
        await session.commit()
        await session.refresh(row)
    except Exception:
        await session.rollback()
        await purge_portfolio_image(stored.stored_name)
        raise
    if previous_stored_name:
        await purge_portfolio_image(previous_stored_name)
    return _portfolio_image_read(row)


@router.delete("/portfolio-images/{image_id}/after", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_after_image(
    image_id: uuid.UUID,
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    row = await session.get(PortfolioImage, image_id)
    if row is None or not row.after_stored_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    stored_name = row.after_stored_name
    row.after_original_name = None
    row.after_stored_name = None
    row.after_content_type = None
    row.after_size_bytes = None
    session.add(
        _audit(identity, "portfolio_after_image_deleted", details={"image_id": str(row.id)})
    )
    await session.commit()
    await purge_portfolio_image(stored_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/portfolio-images/{image_id}", response_model=PortfolioImageRead)
async def update_portfolio_image(
    image_id: uuid.UUID,
    payload: PortfolioImageUpdate,
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PortfolioImageRead:
    image = await session.get(PortfolioImage, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    image.caption = payload.caption.strip() if payload.caption and payload.caption.strip() else None
    image.is_enabled = payload.is_enabled
    session.add(
        _audit(
            identity,
            "portfolio_image_updated",
            details={"image_id": str(image.id), "is_enabled": image.is_enabled},
        )
    )
    await session.commit()
    await session.refresh(image)
    return _portfolio_image_read(image)


@router.post("/portfolio-images/{image_id}/move", response_model=list[PortfolioImageRead])
async def move_portfolio_image(
    image_id: uuid.UUID,
    direction: Annotated[Literal["up", "down"], Query()],
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PortfolioImageRead]:
    image = await session.get(PortfolioImage, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    if direction == "up":
        adjacent = await session.scalar(
            select(PortfolioImage)
            .where(PortfolioImage.sort_order < image.sort_order)
            .order_by(PortfolioImage.sort_order.desc())
            .limit(1)
        )
    else:
        adjacent = await session.scalar(
            select(PortfolioImage)
            .where(PortfolioImage.sort_order > image.sort_order)
            .order_by(PortfolioImage.sort_order)
            .limit(1)
        )
    if adjacent is not None:
        image.sort_order, adjacent.sort_order = adjacent.sort_order, image.sort_order
        session.add(
            _audit(
                identity,
                "portfolio_image_moved",
                details={"image_id": str(image.id), "direction": direction},
            )
        )
        await session.commit()
    images = list(
        await session.scalars(
            select(PortfolioImage).order_by(
                PortfolioImage.sort_order,
                PortfolioImage.created_at,
            )
        )
    )
    return [_portfolio_image_read(row) for row in images]


@router.delete("/portfolio-images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_image(
    image_id: uuid.UUID,
    identity: Annotated[AdminIdentity, Depends(require_admin_mutation)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    image = await session.get(PortfolioImage, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    stored_name = image.stored_name
    after_stored_name = image.after_stored_name
    session.add(
        _audit(
            identity,
            "portfolio_image_deleted",
            details={"image_id": str(image.id), "original_name": image.original_name},
        )
    )
    await session.delete(image)
    await session.commit()
    await purge_portfolio_image(stored_name)
    if after_stored_name:
        await purge_portfolio_image(after_stored_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Accepted requests cannot be unread."
        )
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
