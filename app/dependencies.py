from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .services.auth_service import get_user_by_username
from .models.user import User
from .config import settings


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_username(db, username)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def login_required(request: Request, db: AsyncSession = Depends(get_db)):
    """For general page routes — redirects to /login instead of raising 401."""
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login", status_code=302)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return RedirectResponse("/login", status_code=302)
    except JWTError:
        return RedirectResponse("/login", status_code=302)

    user = await get_user_by_username(db, username)
    if not user or not user.is_active:
        return RedirectResponse("/login", status_code=302)
    return user


async def require_admin_html(request: Request, db: AsyncSession = Depends(get_db)):
    """For admin page routes — redirects to /admin/login if not admin."""
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/admin/login", status_code=302)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return RedirectResponse("/admin/login", status_code=302)
    except JWTError:
        return RedirectResponse("/admin/login", status_code=302)

    user = await get_user_by_username(db, username)
    if not user or not user.is_active or not user.is_admin:
        return RedirectResponse("/admin/login", status_code=302)
    return user
