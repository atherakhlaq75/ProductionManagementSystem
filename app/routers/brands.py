from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from ..database import get_db
from ..dependencies import login_required
from ..models.brand import Brand, CustomerBrand
from ..models.customer import Customer
from ..models.garment_style import GarmentStyle
from ..models.user import User
from ..templates_config import templates
from ..config import settings

router = APIRouter(prefix="/brands")


def _next_brand_code(count: int) -> str:
    return f"BRD-{count + 1:04d}"


# ── API endpoint: brands that belong to a specific customer (used by style form JS) ──
@router.get("/api/by-customer", response_class=JSONResponse)
async def brands_by_customer(
    customer_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    if not customer_id:
        brands = (await db.execute(
            select(Brand).where(Brand.status == "active").order_by(Brand.brand_name)
        )).scalars().all()
    else:
        # Brands linked to this customer via customer_brands
        result = await db.execute(
            select(Brand)
            .join(CustomerBrand, CustomerBrand.brand_id == Brand.id)
            .where(CustomerBrand.customer_id == customer_id)
            .where(Brand.status == "active")
            .order_by(Brand.brand_name)
        )
        brands = result.scalars().all()
    return [{"id": b.id, "brand_name": b.brand_name, "brand_code": b.brand_code} for b in brands]


# ── List ──────────────────────────────────────────────────────────────────────
@router.get("", response_class=HTMLResponse)
async def brand_list(
    request: Request,
    search: Optional[str] = None,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user

    query = select(Brand).options(selectinload(Brand.customer_brands).selectinload(CustomerBrand.customer))
    if search:
        query = query.where(
            Brand.brand_name.ilike(f"%{search}%") | Brand.brand_code.ilike(f"%{search}%")
        )
    if status:
        query = query.where(Brand.status == status)
    if customer_id:
        query = query.join(CustomerBrand, CustomerBrand.brand_id == Brand.id).where(
            CustomerBrand.customer_id == customer_id
        )
    brands = (await db.execute(query.order_by(Brand.brand_name))).scalars().all()
    customers = (await db.execute(
        select(Customer).where(Customer.status == "active").order_by(Customer.company_name)
    )).scalars().all()
    total = (await db.execute(select(func.count()).select_from(Brand))).scalar()
    return templates.TemplateResponse(request=request, name="brands/list.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "brands": brands, "customers": customers, "total": total,
        "search": search, "selected_customer": customer_id, "selected_status": status,
    })


# ── New ───────────────────────────────────────────────────────────────────────
@router.get("/new", response_class=HTMLResponse)
async def brand_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Brand))).scalar()
    customers = (await db.execute(
        select(Customer).where(Customer.status == "active").order_by(Customer.company_name)
    )).scalars().all()
    return templates.TemplateResponse(request=request, name="brands/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "next_code": _next_brand_code(count),
        "customers": customers, "brand": None, "assigned_customer_ids": [], "errors": {},
    })


@router.post("/new")
async def brand_create(
    request: Request,
    brand_name: str = Form(...),
    description: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    customer_ids: List[int] = Form(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Brand))).scalar()
    brand = Brand(
        brand_code=_next_brand_code(count),
        brand_name=brand_name,
        description=description or None,
        website=website or None,
    )
    db.add(brand)
    await db.flush()   # get brand.id before adding junctions
    for cid in customer_ids:
        db.add(CustomerBrand(customer_id=cid, brand_id=brand.id))
    await db.commit()
    return RedirectResponse("/brands", status_code=302)


# ── Detail ────────────────────────────────────────────────────────────────────
@router.get("/{brand_id}", response_class=HTMLResponse)
async def brand_detail(
    request: Request, brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    brand = (await db.execute(
        select(Brand)
        .options(
            selectinload(Brand.customer_brands).selectinload(CustomerBrand.customer),
            selectinload(Brand.styles),
        )
        .where(Brand.id == brand_id)
    )).scalar_one_or_none()
    if not brand:
        return RedirectResponse("/brands", status_code=302)
    return templates.TemplateResponse(request=request, name="brands/detail.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME, "brand": brand,
    })


# ── Edit ──────────────────────────────────────────────────────────────────────
@router.get("/{brand_id}/edit", response_class=HTMLResponse)
async def brand_edit(
    request: Request, brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    brand = (await db.execute(
        select(Brand)
        .options(selectinload(Brand.customer_brands))
        .where(Brand.id == brand_id)
    )).scalar_one_or_none()
    if not brand:
        return RedirectResponse("/brands", status_code=302)
    customers = (await db.execute(
        select(Customer).where(Customer.status == "active").order_by(Customer.company_name)
    )).scalars().all()
    assigned_ids = [cb.customer_id for cb in brand.customer_brands]
    return templates.TemplateResponse(request=request, name="brands/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "brand": brand, "customers": customers,
        "assigned_customer_ids": assigned_ids, "errors": {},
    })


@router.post("/{brand_id}/edit")
async def brand_update(
    request: Request, brand_id: int,
    brand_name: str = Form(...),
    description: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    status: str = Form("active"),
    customer_ids: List[int] = Form(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    brand = (await db.execute(select(Brand).where(Brand.id == brand_id))).scalar_one_or_none()
    if not brand:
        return RedirectResponse("/brands", status_code=302)
    brand.brand_name = brand_name
    brand.description = description or None
    brand.website = website or None
    brand.status = status
    # Replace customer_brands: delete old, insert new
    await db.execute(delete(CustomerBrand).where(CustomerBrand.brand_id == brand_id))
    for cid in customer_ids:
        db.add(CustomerBrand(customer_id=cid, brand_id=brand_id))
    await db.commit()
    return RedirectResponse(f"/brands/{brand_id}", status_code=302)


# ── Delete ────────────────────────────────────────────────────────────────────
@router.post("/{brand_id}/delete")
async def brand_delete(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    brand = (await db.execute(select(Brand).where(Brand.id == brand_id))).scalar_one_or_none()
    if brand:
        await db.delete(brand)
        await db.commit()
    return RedirectResponse("/brands", status_code=302)
