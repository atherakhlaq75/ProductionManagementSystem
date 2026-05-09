from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from ..database import get_db
from ..services.auth_service import authenticate_user, create_access_token
from ..templates_config import templates
from ..config import settings

router = APIRouter()


# ── General login ────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.cookies.get("access_token"):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={"app_name": settings.APP_NAME})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"error": "Invalid username or password", "app_name": settings.APP_NAME},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if user.is_admin:
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"error": "Admin accounts must use the Admin Panel login.", "app_name": settings.APP_NAME},
            status_code=status.HTTP_403_FORBIDDEN,
        )
    if not user.is_active:
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"error": "Your account has been deactivated.", "app_name": settings.APP_NAME},
            status_code=status.HTTP_403_FORBIDDEN,
        )
    token = create_access_token({"sub": user.username}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie("access_token", token, httponly=True,
                        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite="lax")
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# ── Admin login ───────────────────────────────────────────────────────────────

@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse("/admin/", status_code=302)
    return templates.TemplateResponse(request=request, name="admin/login.html", context={"app_name": settings.APP_NAME})


@router.post("/admin/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            request=request, name="admin/login.html",
            context={"error": "Invalid credentials.", "app_name": settings.APP_NAME},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if not user.is_admin:
        return templates.TemplateResponse(
            request=request, name="admin/login.html",
            context={"error": "Admin credentials required. General users must use the main login.", "app_name": settings.APP_NAME},
            status_code=status.HTTP_403_FORBIDDEN,
        )
    if not user.is_active:
        return templates.TemplateResponse(
            request=request, name="admin/login.html",
            context={"error": "This account has been deactivated.", "app_name": settings.APP_NAME},
            status_code=status.HTTP_403_FORBIDDEN,
        )
    token = create_access_token({"sub": user.username}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    response = RedirectResponse("/admin/", status_code=302)
    response.set_cookie("access_token", token, httponly=True,
                        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite="lax")
    return response


@router.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse("/admin/login", status_code=302)
    response.delete_cookie("access_token")
    return response
