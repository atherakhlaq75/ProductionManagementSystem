from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from ..database import get_db
from ..dependencies import login_required
from ..models.production_line import ProductionLine
from ..models.user import User
from ..templates_config import templates
from ..config import settings

router = APIRouter(prefix="/lines")


def _next_line_code(count: int) -> str:
    return f"LINE-{count + 1:02d}"


@router.get("", response_class=HTMLResponse)
async def line_list(
    request: Request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    query = select(ProductionLine)
    if search:
        query = query.where(
            ProductionLine.line_name.ilike(f"%{search}%") |
            ProductionLine.line_code.ilike(f"%{search}%") |
            ProductionLine.supervisor.ilike(f"%{search}%")
        )
    if status:
        query = query.where(ProductionLine.status == status)
    lines = (await db.execute(query.order_by(ProductionLine.line_code))).scalars().all()
    total = (await db.execute(select(func.count()).select_from(ProductionLine))).scalar()
    return templates.TemplateResponse(request=request, name="lines/list.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "lines": lines, "total": total,
        "search": search, "selected_status": status,
    })


@router.get("/new", response_class=HTMLResponse)
async def line_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(ProductionLine))).scalar()
    return templates.TemplateResponse(request=request, name="lines/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "next_code": _next_line_code(count), "line": None, "errors": {},
    })


@router.post("/new")
async def line_create(
    request: Request,
    line_name: str = Form(...),
    floor: Optional[str] = Form(None),
    capacity_per_day: Optional[int] = Form(None),
    operator_count: Optional[int] = Form(None),
    supervisor: Optional[str] = Form(None),
    line_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(ProductionLine))).scalar()
    line = ProductionLine(
        line_code=_next_line_code(count),
        line_name=line_name,
        floor=floor or None,
        capacity_per_day=capacity_per_day or None,
        operator_count=operator_count or None,
        supervisor=supervisor or None,
        line_type=line_type or None,
        description=description or None,
    )
    db.add(line)
    await db.commit()
    return RedirectResponse("/lines", status_code=302)


@router.get("/{line_id}", response_class=HTMLResponse)
async def line_detail(
    request: Request, line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    line = (await db.execute(select(ProductionLine).where(ProductionLine.id == line_id))).scalar_one_or_none()
    if not line:
        return RedirectResponse("/lines", status_code=302)
    return templates.TemplateResponse(request=request, name="lines/detail.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME, "line": line,
    })


@router.get("/{line_id}/edit", response_class=HTMLResponse)
async def line_edit(
    request: Request, line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    line = (await db.execute(select(ProductionLine).where(ProductionLine.id == line_id))).scalar_one_or_none()
    if not line:
        return RedirectResponse("/lines", status_code=302)
    return templates.TemplateResponse(request=request, name="lines/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "line": line, "errors": {},
    })


@router.post("/{line_id}/edit")
async def line_update(
    request: Request, line_id: int,
    line_name: str = Form(...),
    floor: Optional[str] = Form(None),
    capacity_per_day: Optional[int] = Form(None),
    operator_count: Optional[int] = Form(None),
    supervisor: Optional[str] = Form(None),
    line_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    status: str = Form("active"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    line = (await db.execute(select(ProductionLine).where(ProductionLine.id == line_id))).scalar_one_or_none()
    if not line:
        return RedirectResponse("/lines", status_code=302)
    line.line_name = line_name
    line.floor = floor or None
    line.capacity_per_day = capacity_per_day or None
    line.operator_count = operator_count or None
    line.supervisor = supervisor or None
    line.line_type = line_type or None
    line.description = description or None
    line.status = status
    await db.commit()
    return RedirectResponse(f"/lines/{line_id}", status_code=302)


@router.post("/{line_id}/delete")
async def line_delete(
    line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    line = (await db.execute(select(ProductionLine).where(ProductionLine.id == line_id))).scalar_one_or_none()
    if line:
        await db.delete(line)
        await db.commit()
    return RedirectResponse("/lines", status_code=302)
