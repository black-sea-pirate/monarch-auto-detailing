import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware import QuoteRequestBodyLimitMiddleware
from app.routes import admin, health, quotes
from app.services.housekeeping import housekeeping_loop
from app.services.storage import upload_root
from app.services.telegram import disable_telegram_webhook


@asynccontextmanager
async def lifespan(_: FastAPI):
    upload_root().mkdir(parents=True, exist_ok=True)
    await disable_telegram_webhook()
    housekeeping_task = asyncio.create_task(housekeeping_loop())
    try:
        yield
    finally:
        housekeeping_task.cancel()
        with suppress(asyncio.CancelledError):
            await housekeeping_task


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(QuoteRequestBodyLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Upload-Token"],
)

app.include_router(health.router)
app.include_router(quotes.router)
app.include_router(admin.router)
