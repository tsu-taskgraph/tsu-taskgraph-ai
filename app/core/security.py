from fastapi import Header, HTTPException, status

from app.config import get_settings


async def require_internal_secret(x_internal_secret: str | None = Header(None)) -> None:
    settings = get_settings()
    if not x_internal_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required X-Internal-Secret header",
        )
    if x_internal_secret != settings.internal_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Internal-Secret header",
        )
