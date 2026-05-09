from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date
from ..database import get_db
from ..dependencies import login_required
from ..models.production import Production
from ..models.order import Order
from ..models.production_line import ProductionLine
from ..models.customer import Customer
from ..models.garment_style import GarmentStyle
from ..models.user import User
from ..templates_config import templates
from ..config import settings

router = APIRouter(prefix="/productions")


def _next_production_no(count: int) -> str:
    today = date.today()
    return f"PRD-{today.strftime('%Y%m')}{count + 1:04d}"


@router.get("", response_class=HTMLResponse)
async def production_list(
    request: Request,
    search: Optional[str] = None,
    line_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    query = select(Production).options(
        selectinload(Production.order).selectinload(Order.customer),
        selectinload(Production.order).selectinload(Order.style),
        selectinload(Production.line),
    )
    if search:
        query = query.where(Production.production_no.ilike(f"%{search}%"))
    if line_id:
        query = query.where(Production.line_id == line_id)
    if status:
        query = query.where(Production.status == status)
    productions = (await db.execute(query.order_by(Production.created_at.desc()))).scalars().all()
    lines = (await db.execute(select(ProductionLine).where(ProductionLine.status == "active").order_by(ProductionLine.line_code))).scalars().all()
    total = (await db.execute(select(func.count()).select_from(Production))).scalar()
    return templates.TemplateResponse(request=request, name="productions/list.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "productions": productions, "lines": lines, "total": total,
        "search": search, "selected_line": line_id, "selected_status": status,
    })


@router.get("/new", response_class=HTMLResponse)
async def production_new(
    request: Request,
    order_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Production))).scalar()
    orders = (await db.execute(
        select(Order).options(selectinload(Order.customer), selectinload(Order.style))
        .where(Order.status.in_(["confirmed", "in_production"]))
        .order_by(Order.order_no)
    )).scalars().all()
    lines = (await db.execute(select(ProductionLine).where(ProductionLine.status == "active").order_by(ProductionLine.line_code))).scalars().all()
    preselected_order = None
    if order_id:
        preselected_order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    return templates.TemplateResponse(request=request, name="productions/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "next_production_no": _next_production_no(count),
        "orders": orders, "lines": lines,
        "production": None, "preselected_order": preselected_order, "errors": {},
    })


@router.post("/new")
async def production_create(
    request: Request,
    order_id: int = Form(...),
    line_id: int = Form(...),
    planned_qty: int = Form(...),
    planned_start: Optional[str] = Form(None),
    planned_end: Optional[str] = Form(None),
    actual_start: Optional[str] = Form(None),
    actual_end: Optional[str] = Form(None),
    output_qty: int = Form(0),
    rejected_qty: int = Form(0),
    remarks: Optional[str] = Form(None),
    status: str = Form("scheduled"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Production))).scalar()
    production = Production(
        production_no=_next_production_no(count),
        order_id=order_id,
        line_id=line_id,
        planned_qty=planned_qty,
        planned_start=date.fromisoformat(planned_start) if planned_start else None,
        planned_end=date.fromisoformat(planned_end) if planned_end else None,
        actual_start=date.fromisoformat(actual_start) if actual_start else None,
        actual_end=date.fromisoformat(actual_end) if actual_end else None,
        output_qty=output_qty,
        rejected_qty=rejected_qty,
        remarks=remarks or None,
        status=status,
    )
    db.add(production)
    # Update order status to in_production
    order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if order and order.status == "confirmed":
        order.status = "in_production"
    await db.commit()
    return RedirectResponse("/productions", status_code=302)


@router.get("/{prod_id}", response_class=HTMLResponse)
async def production_detail(
    request: Request, prod_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    result = await db.execute(
        select(Production)
        .options(
            selectinload(Production.order).selectinload(Order.customer),
            selectinload(Production.order).selectinload(Order.style),
            selectinload(Production.line),
        )
        .where(Production.id == prod_id)
    )
    production = result.scalar_one_or_none()
    if not production:
        return RedirectResponse("/productions", status_code=302)
    return templates.TemplateResponse(request=request, name="productions/detail.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME, "production": production,
    })


@router.get("/{prod_id}/edit", response_class=HTMLResponse)
async def production_edit(
    request: Request, prod_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    production = (await db.execute(
        select(Production)
        .options(selectinload(Production.order), selectinload(Production.line))
        .where(Production.id == prod_id)
    )).scalar_one_or_none()
    if not production:
        return RedirectResponse("/productions", status_code=302)
    orders = (await db.execute(
        select(Order).options(selectinload(Order.customer), selectinload(Order.style))
        .where(Order.status.in_(["confirmed", "in_production"]))
        .order_by(Order.order_no)
    )).scalars().all()
    lines = (await db.execute(select(ProductionLine).where(ProductionLine.status == "active").order_by(ProductionLine.line_code))).scalars().all()
    return templates.TemplateResponse(request=request, name="productions/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "production": production, "orders": orders, "lines": lines, "errors": {},
    })


@router.post("/{prod_id}/edit")
async def production_update(
    request: Request, prod_id: int,
    order_id: int = Form(...),
    line_id: int = Form(...),
    planned_qty: int = Form(...),
    planned_start: Optional[str] = Form(None),
    planned_end: Optional[str] = Form(None),
    actual_start: Optional[str] = Form(None),
    actual_end: Optional[str] = Form(None),
    output_qty: int = Form(0),
    rejected_qty: int = Form(0),
    remarks: Optional[str] = Form(None),
    status: str = Form("scheduled"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    production = (await db.execute(select(Production).where(Production.id == prod_id))).scalar_one_or_none()
    if not production:
        return RedirectResponse("/productions", status_code=302)
    production.order_id = order_id
    production.line_id = line_id
    production.planned_qty = planned_qty
    production.planned_start = date.fromisoformat(planned_start) if planned_start else None
    production.planned_end = date.fromisoformat(planned_end) if planned_end else None
    production.actual_start = date.fromisoformat(actual_start) if actual_start else None
    production.actual_end = date.fromisoformat(actual_end) if actual_end else None
    production.output_qty = output_qty
    production.rejected_qty = rejected_qty
    production.remarks = remarks or None
    production.status = status
    # If completed, check if order should be updated
    if status == "completed":
        order = (await db.execute(
            select(Order).where(Order.id == order_id)
        )).scalar_one_or_none()
        if order:
            order.status = "ready_to_ship"
    await db.commit()
    return RedirectResponse(f"/productions/{prod_id}", status_code=302)


@router.post("/{prod_id}/delete")
async def production_delete(
    prod_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    production = (await db.execute(select(Production).where(Production.id == prod_id))).scalar_one_or_none()
    if production:
        await db.delete(production)
        await db.commit()
    return RedirectResponse("/productions", status_code=302)
