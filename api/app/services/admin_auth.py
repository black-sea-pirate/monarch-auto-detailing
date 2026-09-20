import secrets
from dataclasses import dataclass
from functools import lru_cache

import anyio
import jwt
from fastapi import Header, HTTPException, status
from jwt import PyJWKClient

from app.config import settings


@dataclass(frozen=True)
class AdminIdentity:
    email: str


@lru_cache
def _jwk_client() -> PyJWKClient:
    return PyJWKClient(f"{settings.cloudflare_access_issuer}/cdn-cgi/access/certs", cache_keys=True)


def _decode_access_token(token: str) -> dict[str, object]:
    signing_key = _jwk_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.cloudflare_access_aud,
        issuer=settings.cloudflare_access_issuer,
        options={"require": ["exp", "iat", "iss", "aud", "email"]},
    )


async def require_admin(
    access_token: str | None = Header(default=None, alias="Cf-Access-Jwt-Assertion"),
    dev_token: str | None = Header(default=None, alias="X-Admin-Dev-Token"),
) -> AdminIdentity:
    if (
        settings.app_env == "development"
        and settings.admin_dev_token
        and dev_token
        and secrets.compare_digest(dev_token, settings.admin_dev_token)
    ):
        email = next(iter(settings.normalized_admin_emails), "developer@localhost")
        return AdminIdentity(email=email)

    if not (
        settings.cloudflare_access_issuer
        and settings.cloudflare_access_aud
        and settings.normalized_admin_emails
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured.",
        )
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    try:
        claims = await anyio.to_thread.run_sync(_decode_access_token, access_token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The admin session is invalid or expired.",
        ) from exc

    email = str(claims.get("email", "")).strip().casefold()
    if email not in settings.normalized_admin_emails:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access is not permitted.")
    return AdminIdentity(email=email)
