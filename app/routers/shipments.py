from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date
from ..database import get_db
from ..dependencies import login_required
from ..models.shipment import Shipment
from ..models.order import Order
from ..models.customer import Customer
from ..models.garment_style import GarmentStyle
from ..models.user import User
from ..templates_config import templates
from ..config import settings

router = APIRouter(prefix="/shipments")


def _next_invoice_no(count: int) -> str:
    today = date.today()
    return f"INV-{today.strftime('%Y%m')}{count + 1:04d}"


@router.get("", response_class=HTMLResponse)
async def shipment_list(
    request: Request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    query = select(Shipment).options(
        selectinload(Shipment.order).selectinload(Order.customer),
        selectinload(Shipment.order).selectinload(Order.style),
    )
    if search:
        query = query.where(
            Shipment.invoice_no.ilike(f"%{search}%") |
            Shipment.bl_number.ilike(f"%{search}%")
        )
    if status:
        query = query.where(Shipment.status == status)
    shipments = (await db.execute(query.order_by(Shipment.created_at.desc()))).scalars().all()
    total = (await db.execute(select(func.count()).select_from(Shipment))).scalar()
    return templates.TemplateResponse(request=request, name="shipments/list.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "shipments": shipments, "total": total,
        "search": search, "selected_status": status,
    })


@router.get("/new", response_class=HTMLResponse)
async def shipment_new(
    request: Request,
    order_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Shipment))).scalar()
    orders = (await db.execute(
        select(Order).options(selectinload(Order.customer), selectinload(Order.style))
        .where(Order.status.in_(["ready_to_ship", "in_production", "confirmed"]))
        .order_by(Order.order_no)
    )).scalars().all()
    preselected_order = None
    if order_id:
        preselected_order = (await db.execute(
            select(Order).options(selectinload(Order.customer), selectinload(Order.style))
            .where(Order.id == order_id)
        )).scalar_one_or_none()
    return templates.TemplateResponse(request=request, name="shipments/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "next_invoice_no": _next_invoice_no(count),
        "orders": orders, "shipment": None,
        "preselected_order": preselected_order, "errors": {},
    })


@router.post("/new")
async def shipment_create(
    request: Request,
    order_id: int = Form(...),
    shipment_date: Optional[str] = Form(None),
    shipped_qty: int = Form(...),
    carton_count: Optional[int] = Form(None),
    net_weight_kg: Optional[str] = Form(None),
    gross_weight_kg: Optional[str] = Form(None),
    unit_price: Optional[str] = Form(None),
    currency: str = Form("USD"),
    port_of_loading: Optional[str] = Form(None),
    port_of_discharge: Optional[str] = Form(None),
    vessel_name: Optional[str] = Form(None),
    bl_number: Optional[str] = Form(None),
    etd: Optional[str] = Form(None),
    eta: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Shipment))).scalar()
    shipment = Shipment(
        invoice_no=_next_invoice_no(count),
        order_id=order_id,
        shipment_date=date.fromisoformat(shipment_date) if shipment_date else date.today(),
        shipped_qty=shipped_qty,
        carton_count=carton_count or None,
        net_weight_kg=float(net_weight_kg) if net_weight_kg else None,
        gross_weight_kg=float(gross_weight_kg) if gross_weight_kg else None,
        unit_price=float(unit_price) if unit_price else None,
        currency=currency,
        port_of_loading=port_of_loading or None,
        port_of_discharge=port_of_discharge or None,
        vessel_name=vessel_name or None,
        bl_number=bl_number or None,
        etd=date.fromisoformat(etd) if etd else None,
        eta=date.fromisoformat(eta) if eta else None,
        remarks=remarks or None,
        status="confirmed",
    )
    db.add(shipment)
    # Update order status
    order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if order:
        order.status = "shipped"
    await db.commit()
    return RedirectResponse("/shipments", status_code=302)


@router.get("/{shipment_id}", response_class=HTMLResponse)
async def shipment_detail(
    request: Request, shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    result = await db.execute(
        select(Shipment)
        .options(
            selectinload(Shipment.order).selectinload(Order.customer),
            selectinload(Shipment.order).selectinload(Order.style),
        )
        .where(Shipment.id == shipment_id)
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        return RedirectResponse("/shipments", status_code=302)
    return templates.TemplateResponse(request=request, name="shipments/detail.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME, "shipment": shipment,
    })


@router.get("/{shipment_id}/edit", response_class=HTMLResponse)
async def shipment_edit(
    request: Request, shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    shipment = (await db.execute(
        select(Shipment).options(selectinload(Shipment.order)).where(Shipment.id == shipment_id)
    )).scalar_one_or_none()
    if not shipment:
        return RedirectResponse("/shipments", status_code=302)
    orders = (await db.execute(
        select(Order).options(selectinload(Order.customer), selectinload(Order.style))
        .where(Order.status.in_(["ready_to_ship", "shipped", "in_production", "confirmed"]))
        .order_by(Order.order_no)
    )).scalars().all()
    return templates.TemplateResponse(request=request, name="shipments/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "shipment": shipment, "orders": orders, "errors": {},
    })


@router.post("/{shipment_id}/edit")
async def shipment_update(
    request: Request, shipment_id: int,
    order_id: int = Form(...),
    shipment_date: Optional[str] = Form(None),
    shipped_qty: int = Form(...),
    carton_count: Optional[int] = Form(None),
    net_weight_kg: Optional[str] = Form(None),
    gross_weight_kg: Optional[str] = Form(None),
    unit_price: Optional[str] = Form(None),
    currency: str = Form("USD"),
    port_of_loading: Optional[str] = Form(None),
    port_of_discharge: Optional[str] = Form(None),
    vessel_name: Optional[str] = Form(None),
    bl_number: Optional[str] = Form(None),
    etd: Optional[str] = Form(None),
    eta: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    status: str = Form("confirmed"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    shipment = (await db.execute(select(Shipment).where(Shipment.id == shipment_id))).scalar_one_or_none()
    if not shipment:
        return RedirectResponse("/shipments", status_code=302)
    shipment.order_id = order_id
    shipment.shipment_date = date.fromisoformat(shipment_date) if shipment_date else shipment.shipment_date
    shipment.shipped_qty = shipped_qty
    shipment.carton_count = carton_count or None
    shipment.net_weight_kg = float(net_weight_kg) if net_weight_kg else None
    shipment.gross_weight_kg = float(gross_weight_kg) if gross_weight_kg else None
    shipment.unit_price = float(unit_price) if unit_price else None
    shipment.currency = currency
    shipment.port_of_loading = port_of_loading or None
    shipment.port_of_discharge = port_of_discharge or None
    shipment.vessel_name = vessel_name or None
    shipment.bl_number = bl_number or None
    shipment.etd = date.fromisoformat(etd) if etd else None
    shipment.eta = date.fromisoformat(eta) if eta else None
    shipment.remarks = remarks or None
    shipment.status = status
    await db.commit()
    return RedirectResponse(f"/shipments/{shipment_id}", status_code=302)


@router.post("/{shipment_id}/delete")
async def shipment_delete(
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    shipment = (await db.execute(select(Shipment).where(Shipment.id == shipment_id))).scalar_one_or_none()
    if shipment:
        await db.delete(shipment)
        await db.commit()
    return RedirectResponse("/shipments", status_code=302)
