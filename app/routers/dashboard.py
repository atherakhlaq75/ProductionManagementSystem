from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..dependencies import login_required
from ..models.customer import Customer
from ..models.brand import Brand
from ..models.garment_style import GarmentStyle
from ..models.production_line import ProductionLine
from ..models.order import Order
from ..models.production import Production
from ..models.shipment import Shipment
from ..models.user import User
from ..templates_config import templates
from ..config import settings

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user

    customer_count    = (await db.execute(select(func.count()).select_from(Customer))).scalar()
    brand_count       = (await db.execute(select(func.count()).select_from(Brand))).scalar()
    style_count       = (await db.execute(select(func.count()).select_from(GarmentStyle))).scalar()
    line_count        = (await db.execute(select(func.count()).select_from(ProductionLine))).scalar()
    order_count       = (await db.execute(select(func.count()).select_from(Order))).scalar()
    production_count  = (await db.execute(select(func.count()).select_from(Production))).scalar()
    shipment_count    = (await db.execute(select(func.count()).select_from(Shipment))).scalar()

    pending_orders = (await db.execute(
        select(func.count()).select_from(Order).where(Order.status.in_(["confirmed", "in_production"]))
    )).scalar()

    recent_orders = (await db.execute(
        select(Order)
        .options(selectinload(Order.customer), selectinload(Order.style))
        .order_by(Order.created_at.desc()).limit(5)
    )).scalars().all()

    recent_shipments = (await db.execute(
        select(Shipment)
        .options(
            selectinload(Shipment.order).selectinload(Order.customer),
            selectinload(Shipment.order).selectinload(Order.style),
        )
        .order_by(Shipment.created_at.desc()).limit(5)
    )).scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "current_user": current_user,
            "app_name": settings.APP_NAME,
            "customer_count": customer_count,
            "brand_count": brand_count,
            "style_count": style_count,
            "line_count": line_count,
            "order_count": order_count,
            "production_count": production_count,
            "shipment_count": shipment_count,
            "pending_orders": pending_orders,
            "recent_orders": recent_orders,
            "recent_shipments": recent_shipments,
        },
    )
