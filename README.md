# GarmentFlow — Production Order Management System

A web-based Production Order Management System built for **Croydon Kowloon Designs Ltd. (CKDL)** using **FastAPI**, **PostgreSQL**, and **Jinja2** templates. Designed to digitise and centralise the full garment manufacturing workflow — from customer order receipt through production scheduling to shipment and invoicing.

---

## Features

### Admin Panel *(Administrators only)*

| Module | Capabilities |
|---|---|
| **Admin Dashboard** | Real-time counts for users, groups, customers, brands, styles, and lines. Quick-action shortcuts. |
| **Customers** | Create and manage buyer profiles — contact details, country, payment terms, active/inactive status |
| **Brands** | Register buyer brands linked to customers via many-to-many relationship |
| **Garment Styles** | Full style specs — category, fabric, SAM, standard cost, season, gender, buyer style reference |
| **Production Lines** | Register factory lines with capacity, supervisor, and operational status |
| **Users** | Create, edit, deactivate accounts; classify as Admin or General User; assign to groups |
| **Groups & Permissions** | Define permission groups with module-level flags (Orders / Productions / Shipments) |

### User Panel *(General Users)*

| Module | Capabilities |
|---|---|
| **Dashboard** | Overview of accessible transaction modules |
| **Order Receipt** | Create and manage customer orders; full lifecycle status tracking |
| **Production** | Schedule production runs against orders; track output, efficiency, and dates |
| **Shipment / Invoice** | Create shipment invoices; capture shipping details, B/L number, ETD, ETA |

---

## Access Control

The system enforces a strict two-portal authentication model:

- **Admin login** → `/admin/login` — Administrators only. Grants access to master data and user administration.
- **General login** → `/login` — General users only. Grants access to transaction modules based on group permissions.

Admin credentials are rejected at the general login portal and vice versa. Module access for general users is controlled by **Permission Groups** assigned by the administrator.

---

## Auto-Generated Reference Numbers

| Entity | Format | Example |
|---|---|---|
| Order | `ORD-YYYYMM####` | `ORD-2026050001` |
| Production Run | `PRD-YYYYMM####` | `PRD-2026050001` |
| Shipment Invoice | `INV-YYYYMM####` | `INV-2026050001` |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI 0.115.5 |
| **Database** | PostgreSQL 14+ |
| **ORM** | SQLAlchemy 2.0 (async) + asyncpg 0.30 driver |
| **Auth** | JWT (python-jose) — HS256, HttpOnly cookies, 8-hour session |
| **Password Hashing** | bcrypt 4.2 |
| **Templating** | Jinja2 3.1 (server-side rendering) |
| **Web Server** | Uvicorn (ASGI) with hot reload |
| **Config** | Pydantic Settings + python-dotenv |
| **Middleware** | Starlette BaseHTTPMiddleware (request-level access control) |

---

## Project Structure

```
Order-Management/
├── app/
│   ├── main.py                  # FastAPI app, middleware, lifespan, router registration
│   ├── config.py                # Settings loaded from .env via pydantic-settings
│   ├── database.py              # Async SQLAlchemy engine + session factory
│   ├── dependencies.py          # Auth guards — login_required, require_admin_html
│   ├── templates_config.py      # Shared Jinja2Templates instance with global helpers
│   ├── models/
│   │   ├── user.py              # User accounts (admin / general); has_permission()
│   │   ├── group.py             # Permission groups + UserGroup junction
│   │   ├── customer.py          # Buyer profiles
│   │   ├── brand.py             # Buyer brands + CustomerBrand junction
│   │   ├── garment_style.py     # Style specifications (fabric, SAM, season, etc.)
│   │   ├── production_line.py   # Factory production lines
│   │   ├── order.py             # Customer orders (ORD-*)
│   │   ├── production.py        # Production runs (PRD-*)
│   │   └── shipment.py          # Shipment invoices (INV-*)
│   ├── routers/
│   │   ├── auth.py              # /login, /logout, /admin/login, /admin/logout
│   │   ├── admin.py             # /admin — dashboard, users, groups CRUD
│   │   ├── dashboard.py         # /dashboard — general user home
│   │   ├── customers.py         # /customers CRUD
│   │   ├── brands.py            # /brands CRUD
│   │   ├── styles.py            # /styles CRUD
│   │   ├── lines.py             # /lines CRUD
│   │   ├── orders.py            # /orders CRUD
│   │   ├── productions.py       # /productions CRUD
│   │   └── shipments.py         # /shipments CRUD
│   ├── services/
│   │   └── auth_service.py      # JWT creation, bcrypt, admin seed on first run
│   ├── templates/
│   │   ├── base.html            # General user sidebar layout
│   │   ├── login.html           # General user login (split-panel)
│   │   ├── dashboard.html       # General user dashboard
│   │   ├── admin/
│   │   │   ├── base.html        # Admin panel dark sidebar layout
│   │   │   ├── login.html       # Admin login portal
│   │   │   ├── dashboard.html   # Admin dashboard with stats
│   │   │   ├── users/           # list, form
│   │   │   └── groups/          # list, form
│   │   ├── orders/              # list, form, detail
│   │   ├── productions/         # list, form, detail
│   │   ├── shipments/           # list, form, detail
│   │   ├── customers/           # list, form, detail
│   │   ├── brands/              # list, form
│   │   └── styles/              # list, form, detail
│   └── static/
│       ├── css/main.css         # Apple-inspired design system (responsive)
│       ├── js/main.js           # Toast notifications, confirm-delete, animations
│       └── img/ckdl-logo.svg    # CKDL brand logo
├── migrations/
│   ├── 001_init.sql             # Initial schema (optional — app auto-creates tables)
│   └── 002_access_control.sql   # Groups + UserGroup tables
├── run.py                       # Entry point  →  python run.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher running locally

### 2. Create the database

```sql
-- In psql or pgAdmin:
CREATE DATABASE order_mgmt;
```

### 3. Set up the project

```bash
cd "C:\Python Development\Order-Management"

# Create virtual environment
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure environment

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/order_mgmt

# JWT Secret — use a long random string in production
SECRET_KEY=change-this-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Default admin account (created automatically on first run)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@ckdlbd.com

# App settings
APP_NAME=GarmentFlow
APP_ENV=development
DEBUG=True
```

### 5. Run the application

```bash
python run.py
```

On first run the application will automatically:
1. Create all database tables
2. Seed the default admin account
3. Start at **http://127.0.0.1:8083**

---

## Logging In

### Admin Panel

| URL | `http://127.0.0.1:8083/admin/login` |
|---|---|
| Username | `admin` *(or value from `.env`)* |
| Password | `admin123` *(or value from `.env`)* |

From the Admin Panel, create Permission Groups and assign General Users to them.

### General Users

| URL | `http://127.0.0.1:8083/login` |
|---|---|
| Username | *(created by admin)* |
| Password | *(set by admin)* |

> **Important:** Admin accounts cannot log in at the general login portal, and general user accounts cannot log in at the admin portal.

---

## URL Reference

### Public

| URL | Method | Description |
|---|---|---|
| `/` | GET | Redirect to dashboard |
| `/login` | GET / POST | General user sign-in |
| `/logout` | GET | General user sign-out |
| `/admin/login` | GET / POST | Admin sign-in |
| `/admin/logout` | GET | Admin sign-out |

### Admin Panel

| URL | Method | Description |
|---|---|---|
| `/admin/` | GET | Admin dashboard |
| `/admin/users` | GET | User list |
| `/admin/users/new` | GET / POST | Create user |
| `/admin/users/{id}/edit` | GET / POST | Edit user |
| `/admin/users/{id}/delete` | POST | Delete user |
| `/admin/groups` | GET | Group list |
| `/admin/groups/new` | GET / POST | Create group |
| `/admin/groups/{id}/edit` | GET / POST | Edit group |
| `/admin/groups/{id}/delete` | POST | Delete group |
| `/customers` | GET | Customer list |
| `/customers/new` | GET / POST | Add customer |
| `/customers/{id}` | GET | Customer detail |
| `/customers/{id}/edit` | GET / POST | Edit customer |
| `/brands` | GET | Brand list |
| `/brands/new` | GET / POST | Add brand |
| `/brands/{id}/edit` | GET / POST | Edit brand |
| `/styles` | GET | Garment style list |
| `/styles/new` | GET / POST | Add style |
| `/styles/{id}` | GET | Style detail |
| `/styles/{id}/edit` | GET / POST | Edit style |
| `/lines` | GET | Production line list |
| `/lines/new` | GET / POST | Add line |
| `/lines/{id}/edit` | GET / POST | Edit line |

### Transaction Modules *(General Users)*

| URL | Method | Description |
|---|---|---|
| `/dashboard` | GET | User dashboard |
| `/orders` | GET | Order list (search, filter) |
| `/orders/new` | GET / POST | Place new order |
| `/orders/{id}` | GET | Order detail with productions & shipments |
| `/orders/{id}/edit` | GET / POST | Edit order |
| `/orders/{id}/delete` | POST | Delete order |
| `/productions` | GET | Production list |
| `/productions/new` | GET / POST | Schedule production run |
| `/productions/{id}` | GET | Production detail |
| `/productions/{id}/edit` | GET / POST | Edit production run |
| `/productions/{id}/delete` | POST | Delete production run |
| `/shipments` | GET | Shipment list |
| `/shipments/new` | GET / POST | Create shipment invoice |
| `/shipments/{id}` | GET | Shipment detail |
| `/shipments/{id}/edit` | GET / POST | Edit shipment |
| `/shipments/{id}/delete` | POST | Delete shipment |

---

## Database Schema

```
users
  id, username, email, full_name, hashed_password,
  is_admin, is_active, created_at, updated_at

groups
  id, group_code, group_name, description,
  can_access_orders, can_access_productions, can_access_shipments,
  is_active, created_at, updated_at

user_groups  (junction)
  user_id → users.id
  group_id → groups.id

customers
  id, customer_code, company_name, contact_person,
  email, phone, country, city, address, payment_terms,
  status, created_at, updated_at

brands
  id, brand_code, brand_name, description, country_of_origin,
  status, created_at, updated_at

customer_brands  (junction)
  customer_id → customers.id
  brand_id → brands.id

garment_styles
  id, style_no, style_name, description, category,
  fabric_type, fabric_composition, season, gender,
  brand_id → brands.id, customer_id → customers.id,
  buyer_style_ref, unit_of_measure, standard_cost,
  standard_minutes (SAM), status, created_at, updated_at

production_lines
  id, line_code, line_name, capacity_per_day,
  supervisor, status, created_at, updated_at

orders
  id, order_no, po_number,
  customer_id → customers.id,
  style_id → garment_styles.id,
  order_qty, unit_price, currency,
  order_date, delivery_date, remarks,
  status, created_at, updated_at

productions
  id, production_no,
  order_id → orders.id,
  line_id → production_lines.id,
  planned_qty, planned_start, planned_end,
  actual_start, actual_end,
  output_qty, rejected_qty, remarks,
  status, created_at, updated_at

shipments
  id, invoice_no,
  order_id → orders.id,
  shipment_date, shipped_qty, carton_count,
  net_weight_kg, gross_weight_kg,
  unit_price, currency,
  port_of_loading, port_of_discharge,
  vessel_name, bl_number, etd, eta,
  remarks, status, created_at, updated_at
```

---

## Order Lifecycle (Automatic Status Transitions)

```
Order created     →  pending
Order confirmed   →  confirmed
Production run scheduled and completed  →  in_production  →  ready_to_ship
Shipment invoice created  →  shipped
```

---

## Development Tips

**Hot reload** — `run.py` uses `reload=True` so the server restarts automatically on every file save.

**Change port** — Edit `run.py`:
```python
uvicorn.run("app.main:app", host="127.0.0.1", port=8083, reload=True)
```

**Reset admin password** — Update `ADMIN_PASSWORD` in `.env`, delete the admin row from the `users` table, then restart. The admin will be re-seeded on startup.

**Generate a secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Production checklist:**
- Set `DEBUG=False` in `.env`
- Use a long random `SECRET_KEY`
- Set `APP_ENV=production`
- Run behind a reverse proxy (nginx)
- Enable HTTPS / TLS
- Use a managed PostgreSQL instance

---

## Beginner Reference

| Topic | Where to look |
|---|---|
| App startup & table creation | `app/main.py` → `lifespan()` |
| Access control middleware | `app/main.py` → `AccessControlMiddleware` |
| Route definitions | `app/routers/*.py` |
| Database models & relationships | `app/models/*.py` |
| Auth — JWT & bcrypt | `app/services/auth_service.py` |
| Auth guards (dependencies) | `app/dependencies.py` |
| Shared Jinja2 templates instance | `app/templates_config.py` |
| Page templates | `app/templates/` |
| CSS design system | `app/static/css/main.css` |
| App configuration | `app/config.py` + `.env` |

---

## License

Proprietary — developed for internal use by Croydon Kowloon Designs Ltd. (CKDL).  
All rights reserved.
