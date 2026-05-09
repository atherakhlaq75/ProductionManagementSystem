from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date, datetime
from ..database import get_db
from ..dependencies import login_required
from ..models.order import Order
from ..models.customer import Customer
from ..models.garment_style import GarmentStyle
from ..models.production import Production
from ..models.user import User
from ..templates_config import templates
from ..config import settings

router = APIRouter(prefix="/orders")


def _next_order_no(count: int) -> str:
    today = date.today()
    return f"ORD-{today.strftime('%Y%m')}{count + 1:04d}"


@router.get("", response_class=HTMLResponse)
async def order_list(
    request: Request,
    search: Optional[str] = None,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    query = select(Order).options(selectinload(Order.customer), selectinload(Order.style))
    if search:
        query = query.where(
            Order.order_no.ilike(f"%{search}%") |
            Order.po_number.ilike(f"%{search}%")
        )
    if customer_id:
        query = query.where(Order.customer_id == customer_id)
    if status:
        query = query.where(Order.status == status)
    orders = (await db.execute(query.order_by(Order.created_at.desc()))).scalars().all()
    customers = (await db.execute(select(Customer).where(Customer.status == "active").order_by(Customer.company_name))).scalars().all()
    total = (await db.execute(select(func.count()).select_from(Order))).scalar()
    return templates.TemplateResponse(request=request, name="orders/list.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "orders": orders, "customers": customers, "total": total,
        "search": search, "selected_customer": customer_id, "selected_status": status,
        "now": datetime.today().strftime("%Y-%m-%d"),
    })


@router.get("/new", response_class=HTMLResponse)
async def order_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Order))).scalar()
    customers = (await db.execute(select(Customer).where(Customer.status == "active").order_by(Customer.company_name))).scalars().all()
    styles = (await db.execute(select(GarmentStyle).where(GarmentStyle.status == "active").order_by(GarmentStyle.style_no))).scalars().all()
    return templates.TemplateResponse(request=request, name="orders/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "next_order_no": _next_order_no(count),
        "customers": customers, "styles": styles,
        "order": None, "errors": {},
    })


@router.post("/new")
async def order_create(
    request: Request,
    customer_id: int = Form(...),
    style_id: int = Form(...),
    po_number: Optional[str] = Form(None),
    order_qty: int = Form(...),
    unit_price: float = Form(...),
    currency: str = Form("USD"),
    order_date: Optional[str] = Form(None),
    delivery_date: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Order))).scalar()
    order = Order(
        order_no=_next_order_no(count),
        customer_id=customer_id,
        style_id=style_id,
        po_number=po_number or None,
        order_qty=order_qty,
        unit_price=unit_price,
        currency=currency,
        order_date=date.fromisoformat(order_date) if order_date else date.today(),
        delivery_date=date.fromisoformat(delivery_date) if delivery_date else None,
        remarks=remarks or None,
        status="confirmed",
    )
    db.add(order)
    await db.commit()
    return RedirectResponse("/orders", status_code=302)


@router.get("/{order_id}", response_class=HTMLResponse)
async def order_detail(
    request: Request, order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.style),
            selectinload(Order.productions).selectinload(Production.line),
            selectinload(Order.shipments),
        )
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        return RedirectResponse("/orders", status_code=302)
    return templates.TemplateResponse(request=request, name="orders/detail.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME, "order": order,
    })


@router.get("/{order_id}/edit", response_class=HTMLResponse)
async def order_edit(
    request: Request, order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if not order:
        return RedirectResponse("/orders", status_code=302)
    customers = (await db.execute(select(Customer).where(Customer.status == "active").order_by(Customer.company_name))).scalars().all()
    styles = (await db.execute(select(GarmentStyle).where(GarmentStyle.status == "active").order_by(GarmentStyle.style_no))).scalars().all()
    return templates.TemplateResponse(request=request, name="orders/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "order": order, "customers": customers, "styles": styles, "errors": {},
    })


@router.post("/{order_id}/edit")
async def order_update(
    request: Request, order_id: int,
    customer_id: int = Form(...),
    style_id: int = Form(...),
    po_number: Optional[str] = Form(None),
    order_qty: int = Form(...),
    unit_price: float = Form(...),
    currency: str = Form("USD"),
    order_date: Optional[str] = Form(None),
    delivery_date: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    status: str = Form("confirmed"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if not order:
        return RedirectResponse("/orders", status_code=302)
    order.customer_id = customer_id
    order.style_id = style_id
    order.po_number = po_number or None
    order.order_qty = order_qty
    order.unit_price = unit_price
    order.currency = currency
    order.order_date = date.fromisoformat(order_date) if order_date else order.order_date
    order.delivery_date = date.fromisoformat(delivery_date) if delivery_date else None
    order.remarks = remarks or None
    order.status = status
    await db.commit()
    return RedirectResponse(f"/orders/{order_id}", status_code=302)


@router.post("/{order_id}/delete")
async def order_delete(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if order:
        await db.delete(order)
        await db.commit()
    return RedirectResponse("/orders", status_code=302)
