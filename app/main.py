from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .database import engine, AsyncSessionLocal, Base
from .models import User, Customer, Brand, CustomerBrand, GarmentStyle, ProductionLine, Order, Production, Shipment  # noqa
from .models.group import Group, UserGroup  # noqa — ensures tables are created
from .routers import auth, dashboard, customers, brands, styles, lines, orders, productions, shipments
from .routers import admin as admin_router
from .services.auth_service import create_admin_if_not_exists
from .config import settings


# ── Access control middleware ─────────────────────────────────────────────────

class AccessControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Always allow static files and login pages through
        if (path.startswith("/static")
                or path in ("/login", "/logout", "/admin/login", "/admin/logout")
                or path.startswith("/admin/login")
                or path.startswith("/admin/logout")):
            return await call_next(request)

        user = await self._get_user(request)

        # ── Admin-protected paths (masters + admin panel) ──
        admin_paths = ("/admin", "/customers", "/brands", "/styles", "/lines")
        if any(path.startswith(p) for p in admin_paths):
            if not user or not user.is_admin:
                return RedirectResponse("/admin/login", status_code=302)
            return await call_next(request)

        # ── Transaction paths — any logged-in general user ──
        if path.startswith("/orders") or path.startswith("/productions") or path.startswith("/shipments"):
            if not user:
                return RedirectResponse("/login", status_code=302)
            if user.is_admin:
                return RedirectResponse("/admin/", status_code=302)

        # ── Dashboard — general users only; admins go to admin panel ──
        elif path.startswith("/dashboard"):
            if not user:
                return RedirectResponse("/login", status_code=302)
            if user.is_admin:
                return RedirectResponse("/admin/", status_code=302)

        return await call_next(request)

    async def _get_user(self, request: Request):
        token = request.cookies.get("access_token")
        if not token:
            return None
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username = payload.get("sub")
            if not username:
                return None
        except JWTError:
            return None
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User)
                .where(User.username == username)
                .options(selectinload(User.user_groups).selectinload(UserGroup.group))
            )
            return result.scalar_one_or_none()


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await create_admin_if_not_exists(db)
    yield
    await engine.dispose()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description="GarmentFlow — Production Management System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(AccessControlMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router,          tags=["Auth"])
app.include_router(admin_router.router,  tags=["Admin"])
app.include_router(dashboard.router,     tags=["Dashboard"])
app.include_router(customers.router,     tags=["Customers"])
app.include_router(brands.router,        tags=["Brands"])
app.include_router(styles.router,        tags=["Garment Styles"])
app.include_router(lines.router,         tags=["Production Lines"])
app.include_router(orders.router,        tags=["Orders"])
app.include_router(productions.router,   tags=["Productions"])
app.include_router(shipments.router,     tags=["Shipments"])


@app.get("/")
async def root():
    return RedirectResponse("/dashboard", status_code=302)
