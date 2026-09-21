import uuid
from copy import deepcopy
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import PortfolioImage, SiteSettings
from app.schemas import PublicPortfolioImageRead, PublicSiteRead
from app.services.storage import resolve_site_media_path
from app.site_defaults import DEFAULT_PRICING, DEFAULT_SECTIONS

router = APIRouter(prefix="/api/v1/site", tags=["site"])


@router.get("", response_model=PublicSiteRead)
async def get_public_site(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PublicSiteRead:
    settings_row = await session.get(SiteSettings, 1)
    portfolio: list[PortfolioImage] = []
    sections = settings_row.sections if settings_row else deepcopy(DEFAULT_SECTIONS)
    if sections.get("portfolio_enabled", False):
        portfolio = list(
            await session.scalars(
                select(PortfolioImage)
                .where(PortfolioImage.is_enabled.is_(True))
                .order_by(PortfolioImage.sort_order, PortfolioImage.created_at)
            )
        )
    response.headers["Cache-Control"] = "no-store"
    return PublicSiteRead(
        pricing=settings_row.pricing if settings_row else deepcopy(DEFAULT_PRICING),
        sections=sections,
        portfolio=[
            PublicPortfolioImageRead(
                id=image.id,
                caption=image.caption,
                url=f"/api/v1/site/media/{image.id}",
                after_url=(
                    f"/api/v1/site/media/{image.id}/after"
                    if image.after_stored_name
                    else None
                ),
            )
            for image in portfolio
        ],
        version=settings_row.version if settings_row else 1,
    )


@router.get("/media/{image_id}/after")
async def get_public_portfolio_after_image(
    image_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FileResponse:
    settings_row = await session.get(SiteSettings, 1)
    image = await session.get(PortfolioImage, image_id)
    if (
        settings_row is None
        or not settings_row.sections.get("portfolio_enabled", False)
        or image is None
        or not image.is_enabled
        or not image.after_stored_name
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    path = resolve_site_media_path(image.after_stored_name)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    return FileResponse(
        path,
        media_type=image.after_content_type or "image/jpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/media/{image_id}")
async def get_public_portfolio_image(
    image_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FileResponse:
    settings_row = await session.get(SiteSettings, 1)
    image = await session.get(PortfolioImage, image_id)
    if (
        settings_row is None
        or not settings_row.sections.get("portfolio_enabled", False)
        or image is None
        or not image.is_enabled
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    path = resolve_site_media_path(image.stored_name)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    return FileResponse(
        path,
        media_type=image.content_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            "X-Content-Type-Options": "nosniff",
        },
    )
