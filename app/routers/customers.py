from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from ..database import get_db
from ..dependencies import login_required
from ..models.customer import Customer
from ..models.user import User
from ..templates_config import templates
from ..config import settings

router = APIRouter(prefix="/customers")


def _next_customer_code(count: int) -> str:
    return f"CUST-{count + 1:04d}"


@router.get("", response_class=HTMLResponse)
async def customer_list(
    request: Request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    query = select(Customer)
    if search:
        query = query.where(
            Customer.company_name.ilike(f"%{search}%") |
            Customer.customer_code.ilike(f"%{search}%") |
            Customer.contact_person.ilike(f"%{search}%")
        )
    if status:
        query = query.where(Customer.status == status)
    customers = (await db.execute(query.order_by(Customer.created_at.desc()))).scalars().all()
    total = (await db.execute(select(func.count()).select_from(Customer))).scalar()
    return templates.TemplateResponse(request=request, name="customers/list.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "customers": customers, "total": total,
        "search": search, "selected_status": status,
    })


@router.get("/new", response_class=HTMLResponse)
async def customer_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Customer))).scalar()
    return templates.TemplateResponse(request=request, name="customers/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "next_code": _next_customer_code(count), "customer": None, "errors": {},
    })


@router.post("/new")
async def customer_create(
    request: Request,
    company_name: str = Form(...),
    contact_person: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    payment_terms: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    count = (await db.execute(select(func.count()).select_from(Customer))).scalar()
    customer = Customer(
        customer_code=_next_customer_code(count),
        company_name=company_name,
        contact_person=contact_person or None,
        email=email or None,
        phone=phone or None,
        country=country or None,
        city=city or None,
        address=address or None,
        payment_terms=payment_terms or None,
    )
    db.add(customer)
    await db.commit()
    return RedirectResponse("/customers", status_code=302)


@router.get("/{customer_id}", response_class=HTMLResponse)
async def customer_detail(
    request: Request, customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    customer = (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none()
    if not customer:
        return RedirectResponse("/customers", status_code=302)
    return templates.TemplateResponse(request=request, name="customers/detail.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME, "customer": customer,
    })


@router.get("/{customer_id}/edit", response_class=HTMLResponse)
async def customer_edit(
    request: Request, customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    customer = (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none()
    if not customer:
        return RedirectResponse("/customers", status_code=302)
    return templates.TemplateResponse(request=request, name="customers/form.html", context={
        "current_user": current_user, "app_name": settings.APP_NAME,
        "customer": customer, "errors": {},
    })


@router.post("/{customer_id}/edit")
async def customer_update(
    request: Request, customer_id: int,
    company_name: str = Form(...),
    contact_person: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    payment_terms: Optional[str] = Form(None),
    status: str = Form("active"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    customer = (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none()
    if not customer:
        return RedirectResponse("/customers", status_code=302)
    customer.company_name = company_name
    customer.contact_person = contact_person or None
    customer.email = email or None
    customer.phone = phone or None
    customer.country = country or None
    customer.city = city or None
    customer.address = address or None
    customer.payment_terms = payment_terms or None
    customer.status = status
    await db.commit()
    return RedirectResponse(f"/customers/{customer_id}", status_code=302)


@router.post("/{customer_id}/delete")
async def customer_delete(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(login_required),
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    customer = (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none()
    if customer:
        await db.delete(customer)
        await db.commit()
    return RedirectResponse("/customers", status_code=302)
