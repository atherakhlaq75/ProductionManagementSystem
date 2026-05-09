from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date
from ..database import get_db
from ..dependencies import require_admin_html
from ..models.user import User
from ..models.group import Group, UserGroup
from ..models.customer import Customer
from ..models.brand import Brand
from ..models.garment_style import GarmentStyle
from ..models.production_line import ProductionLine
from ..services.auth_service import hash_password
from ..templates_config import templates
from ..config import settings

router = APIRouter(prefix="/admin")

CTX = {"app_name": settings.APP_NAME}


def _ctx(request, current_user, **extra):
    return {"request": request, "current_user": current_user, **CTX, **extra}


# ── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user

    user_count = (await db.execute(select(func.count()).select_from(User))).scalar()
    group_count = (await db.execute(select(func.count()).select_from(Group))).scalar()
    customer_count = (await db.execute(select(func.count()).select_from(Customer))).scalar()
    brand_count = (await db.execute(select(func.count()).select_from(Brand))).scalar()
    style_count = (await db.execute(select(func.count()).select_from(GarmentStyle))).scalar()
    line_count = (await db.execute(select(func.count()).select_from(ProductionLine))).scalar()

    return templates.TemplateResponse(request=request, name="admin/dashboard.html", context=_ctx(
        request, current_user,
        user_count=user_count, group_count=group_count,
        customer_count=customer_count, brand_count=brand_count,
        style_count=style_count, line_count=line_count,
    ))


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    users = (await db.execute(
        select(User)
        .options(selectinload(User.user_groups).selectinload(UserGroup.group))
        .order_by(User.username)
    )).scalars().all()
    return templates.TemplateResponse(request=request, name="admin/users/list.html",
                                      context=_ctx(request, current_user, users=users))


@router.get("/users/new", response_class=HTMLResponse)
async def admin_user_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    groups = (await db.execute(select(Group).where(Group.is_active == True).order_by(Group.group_name))).scalars().all()
    return templates.TemplateResponse(request=request, name="admin/users/form.html",
                                      context=_ctx(request, current_user, user=None, groups=groups, errors={}))


@router.post("/users/new")
async def admin_user_create(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(""),
    password: str = Form(...),
    is_admin: Optional[str] = Form(None),
    is_active: Optional[str] = Form(None),
    group_ids: list[int] = Form(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user

    errors = {}
    existing = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if existing:
        errors["username"] = "Username already exists."
    existing_email = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing_email:
        errors["email"] = "Email already registered."
    if len(password) < 6:
        errors["password"] = "Password must be at least 6 characters."

    if errors:
        groups = (await db.execute(select(Group).where(Group.is_active == True).order_by(Group.group_name))).scalars().all()
        return templates.TemplateResponse(request=request, name="admin/users/form.html",
                                          context=_ctx(request, current_user, user=None, groups=groups, errors=errors))

    user = User(
        username=username, email=email,
        full_name=full_name or None,
        hashed_password=hash_password(password),
        is_admin=bool(is_admin),
        is_active=bool(is_active) if is_active is not None else True,
    )
    db.add(user)
    await db.flush()

    for gid in group_ids:
        db.add(UserGroup(user_id=user.id, group_id=gid))

    await db.commit()
    return RedirectResponse("/admin/users", status_code=302)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def admin_user_edit(
    request: Request, user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    user = (await db.execute(
        select(User).where(User.id == user_id)
        .options(selectinload(User.user_groups).selectinload(UserGroup.group))
    )).scalar_one_or_none()
    if not user:
        return RedirectResponse("/admin/users", status_code=302)
    groups = (await db.execute(select(Group).where(Group.is_active == True).order_by(Group.group_name))).scalars().all()
    return templates.TemplateResponse(request=request, name="admin/users/form.html",
                                      context=_ctx(request, current_user, user=user, groups=groups, errors={}))


@router.post("/users/{user_id}/edit")
async def admin_user_update(
    request: Request, user_id: int,
    email: str = Form(...),
    full_name: str = Form(""),
    new_password: str = Form(""),
    is_admin: Optional[str] = Form(None),
    is_active: Optional[str] = Form(None),
    group_ids: list[int] = Form(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    user = (await db.execute(
        select(User).where(User.id == user_id)
        .options(selectinload(User.user_groups))
    )).scalar_one_or_none()
    if not user:
        return RedirectResponse("/admin/users", status_code=302)

    user.email = email
    user.full_name = full_name or None
    user.is_admin = bool(is_admin)
    user.is_active = bool(is_active)
    if new_password and len(new_password) >= 6:
        user.hashed_password = hash_password(new_password)

    # Replace group assignments
    for ug in list(user.user_groups):
        await db.delete(ug)
    await db.flush()
    for gid in group_ids:
        db.add(UserGroup(user_id=user.id, group_id=gid))

    await db.commit()
    return RedirectResponse("/admin/users", status_code=302)


@router.post("/users/{user_id}/delete")
async def admin_user_delete(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user and user.id != current_user.id:  # prevent self-delete
        await db.delete(user)
        await db.commit()
    return RedirectResponse("/admin/users", status_code=302)


# ── Groups ────────────────────────────────────────────────────────────────────

@router.get("/groups", response_class=HTMLResponse)
async def admin_groups(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    groups = (await db.execute(
        select(Group)
        .options(selectinload(Group.user_groups))
        .order_by(Group.group_name)
    )).scalars().all()
    return templates.TemplateResponse(request=request, name="admin/groups/list.html",
                                      context=_ctx(request, current_user, groups=groups))


@router.get("/groups/new", response_class=HTMLResponse)
async def admin_group_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Group))).scalar()
    next_code = f"GRP-{count + 1:03d}"
    return templates.TemplateResponse(request=request, name="admin/groups/form.html",
                                      context=_ctx(request, current_user, group=None, next_code=next_code, errors={}))


@router.post("/groups/new")
async def admin_group_create(
    request: Request,
    group_code: str = Form(...),
    group_name: str = Form(...),
    description: str = Form(""),
    can_access_orders: Optional[str] = Form(None),
    can_access_productions: Optional[str] = Form(None),
    can_access_shipments: Optional[str] = Form(None),
    is_active: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user

    errors = {}
    existing = (await db.execute(select(Group).where(Group.group_code == group_code.upper()))).scalar_one_or_none()
    if existing:
        errors["group_code"] = "Group code already exists."

    if errors:
        count = (await db.execute(select(func.count()).select_from(Group))).scalar()
        return templates.TemplateResponse(request=request, name="admin/groups/form.html",
                                          context=_ctx(request, current_user, group=None,
                                                       next_code=f"GRP-{count + 1:03d}", errors=errors))

    group = Group(
        group_code=group_code.upper(),
        group_name=group_name,
        description=description or None,
        can_access_orders=bool(can_access_orders),
        can_access_productions=bool(can_access_productions),
        can_access_shipments=bool(can_access_shipments),
        is_active=bool(is_active) if is_active is not None else True,
    )
    db.add(group)
    await db.commit()
    return RedirectResponse("/admin/groups", status_code=302)


@router.get("/groups/{group_id}/edit", response_class=HTMLResponse)
async def admin_group_edit(
    request: Request, group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    group = (await db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
    if not group:
        return RedirectResponse("/admin/groups", status_code=302)
    return templates.TemplateResponse(request=request, name="admin/groups/form.html",
                                      context=_ctx(request, current_user, group=group, next_code=group.group_code, errors={}))


@router.post("/groups/{group_id}/edit")
async def admin_group_update(
    request: Request, group_id: int,
    group_name: str = Form(...),
    description: str = Form(""),
    can_access_orders: Optional[str] = Form(None),
    can_access_productions: Optional[str] = Form(None),
    can_access_shipments: Optional[str] = Form(None),
    is_active: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    group = (await db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
    if not group:
        return RedirectResponse("/admin/groups", status_code=302)

    group.group_name = group_name
    group.description = description or None
    group.can_access_orders = bool(can_access_orders)
    group.can_access_productions = bool(can_access_productions)
    group.can_access_shipments = bool(can_access_shipments)
    group.is_active = bool(is_active)
    await db.commit()
    return RedirectResponse("/admin/groups", status_code=302)


@router.post("/groups/{group_id}/delete")
async def admin_group_delete(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_html),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    group = (await db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
    if group:
        await db.delete(group)
        await db.commit()
    return RedirectResponse("/admin/groups", status_code=302)
