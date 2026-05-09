from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date
from ..database import get_db
from ..dependencies import login_required
from ..models.garment_style import GarmentStyle
from ..models.customer import Customer
from ..models.brand import Brand, CustomerBrand
from ..models.user import User
from ..templates_config import templates
from ..config import settings

router = APIRouter(prefix="/styles")


def _next_style_no(count: int) -> str:
    return f"STY-{date.today().year}-{count + 1:04d}"


async def _get_form_data(db: AsyncSession):
    """Shared helper — fetches brands and customers for the style form."""
    brands = (await db.execute(
        select(Brand).options(selectinload(Brand.customer_brands))
        .where(Brand.status == "active").order_by(Brand.brand_name)
    )).scalars().all()
    customers = (await db.execute(
        select(Customer).where(Customer.status == "active").order_by(Customer.company_name)
    )).scalars().all()
    return brands, customers


@router.get("", response_class=HTMLResponse)
async def style_list(
    request: Request,
    search: Optional[str] = None,
    brand_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    query = select(GarmentStyle).options(
        selectinload(GarmentStyle.brand),
        selectinload(GarmentStyle.customer),
    )
    if search:
        query = query.where(
            GarmentStyle.style_no.ilike(f"%{search}%") |
            GarmentStyle.style_name.ilike(f"%{search}%") |
            GarmentStyle.buyer_style_ref.ilike(f"%{search}%")
        )
    if brand_id:
        query = query.where(GarmentStyle.brand_id == brand_id)
    if customer_id:
        query = query.where(GarmentStyle.customer_id == customer_id)
    if status:
        query = query.where(GarmentStyle.status == status)
    styles = (await db.execute(query.order_by(GarmentStyle.created_at.desc()))).scalars().all()
    brands, customers = await _get_form_data(db)
    total = (await db.execute(select(func.count()).select_from(GarmentStyle))).scalar()
    return templates.TemplateResponse(request=request, name="styles/list.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "styles": styles, "brands": brands, "customers": customers, "total": total,
        "search": search, "selected_brand": brand_id,
        "selected_customer": customer_id, "selected_status": status,
    })


@router.get("/new", response_class=HTMLResponse)
async def style_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(GarmentStyle))).scalar()
    brands, customers = await _get_form_data(db)
    return templates.TemplateResponse(request=request, name="styles/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "next_style_no": _next_style_no(count),
        "brands": brands, "customers": customers,
        "style": None, "errors": {},
    })


@router.post("/new")
async def style_create(
    request: Request,
    style_name: str = Form(...),
    brand_id: Optional[int] = Form(None),
    customer_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    fabric_type: Optional[str] = Form(None),
    fabric_composition: Optional[str] = Form(None),
    season: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    buyer_style_ref: Optional[str] = Form(None),
    unit_of_measure: str = Form("PCS"),
    standard_cost: Optional[str] = Form(None),
    standard_minutes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(GarmentStyle))).scalar()
    style = GarmentStyle(
        style_no=_next_style_no(count),
        style_name=style_name,
        brand_id=brand_id or None,
        customer_id=customer_id or None,
        description=description or None,
        category=category or None,
        fabric_type=fabric_type or None,
        fabric_composition=fabric_composition or None,
        season=season or None,
        gender=gender or None,
        buyer_style_ref=buyer_style_ref or None,
        unit_of_measure=unit_of_measure,
        standard_cost=float(standard_cost) if standard_cost else None,
        standard_minutes=float(standard_minutes) if standard_minutes else None,
    )
    db.add(style)
    await db.commit()
    return RedirectResponse("/styles", status_code=302)


@router.get("/{style_id}", response_class=HTMLResponse)
async def style_detail(
    request: Request, style_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    style = (await db.execute(
        select(GarmentStyle)
        .options(
            selectinload(GarmentStyle.brand).selectinload(Brand.customer_brands).selectinload(CustomerBrand.customer),
            selectinload(GarmentStyle.customer),
        )
        .where(GarmentStyle.id == style_id)
    )).scalar_one_or_none()
    if not style:
        return RedirectResponse("/styles", status_code=302)
    return templates.TemplateResponse(request=request, name="styles/detail.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME, "style": style,
    })


@router.get("/{style_id}/edit", response_class=HTMLResponse)
async def style_edit(
    request: Request, style_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    style = (await db.execute(select(GarmentStyle).where(GarmentStyle.id == style_id))).scalar_one_or_none()
    if not style:
        return RedirectResponse("/styles", status_code=302)
    brands, customers = await _get_form_data(db)
    return templates.TemplateResponse(request=request, name="styles/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "style": style, "brands": brands, "customers": customers, "errors": {},
    })


@router.post("/{style_id}/edit")
async def style_update(
    request: Request, style_id: int,
    style_name: str = Form(...),
    brand_id: Optional[int] = Form(None),
    customer_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    fabric_type: Optional[str] = Form(None),
    fabric_composition: Optional[str] = Form(None),
    season: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    buyer_style_ref: Optional[str] = Form(None),
    unit_of_measure: str = Form("PCS"),
    standard_cost: Optional[str] = Form(None),
    standard_minutes: Optional[str] = Form(None),
    status: str = Form("active"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    style = (await db.execute(select(GarmentStyle).where(GarmentStyle.id == style_id))).scalar_one_or_none()
    if not style:
        return RedirectResponse("/styles", status_code=302)
    style.style_name = style_name
    style.brand_id = brand_id or None
    style.customer_id = customer_id or None
    style.description = description or None
    style.category = category or None
    style.fabric_type = fabric_type or None
    style.fabric_composition = fabric_composition or None
    style.season = season or None
    style.gender = gender or None
    style.buyer_style_ref = buyer_style_ref or None
    style.unit_of_measure = unit_of_measure
    style.standard_cost = float(standard_cost) if standard_cost else None
    style.standard_minutes = float(standard_minutes) if standard_minutes else None
    style.status = status
    await db.commit()
    return RedirectResponse(f"/styles/{style_id}", status_code=302)


@router.post("/{style_id}/delete")
async def style_delete(
    style_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    style = (await db.execute(select(GarmentStyle).where(GarmentStyle.id == style_id))).scalar_one_or_none()
    if style:
        await db.delete(style)
        await db.commit()
    return RedirectResponse("/styles", status_code=302)
