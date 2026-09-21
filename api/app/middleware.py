from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

MAX_MEDIA_UPLOAD_BODY = 52 * 1024 * 1024
MAX_PORTFOLIO_UPLOAD_BODY = 13 * 1024 * 1024


class QuoteRequestBodyLimitMiddleware:
    """Reject an oversized individual media upload before multipart parsing begins."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        is_quote_upload = (
            scope["type"] == "http"
            and scope["method"] == "POST"
            and scope.get("path", "").rstrip("/").endswith("/uploads")
            and scope.get("path", "").startswith("/api/v1/quote-requests/")
        )
        if is_quote_upload:
            content_length = Headers(scope=scope).get("content-length")
            try:
                too_large = bool(content_length and int(content_length) > MAX_MEDIA_UPLOAD_BODY)
            except ValueError:
                too_large = True
            if too_large:
                response = JSONResponse(
                    {"detail": "Each uploaded file must be 50 MB or smaller."},
                    status_code=413,
                )
                await response(scope, receive, send)
                return
        is_portfolio_upload = (
            scope["type"] == "http"
            and scope["method"] == "POST"
            and scope.get("path", "").rstrip("/") == "/api/v1/admin/portfolio-images"
        )
        if is_portfolio_upload:
            content_length = Headers(scope=scope).get("content-length")
            try:
                too_large = bool(content_length and int(content_length) > MAX_PORTFOLIO_UPLOAD_BODY)
            except ValueError:
                too_large = True
            if too_large:
                response = JSONResponse(
                    {"detail": "Portfolio photos must be 12 MB or smaller."},
                    status_code=413,
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
