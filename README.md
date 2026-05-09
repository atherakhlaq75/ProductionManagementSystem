# EduSphere — Student Management System

A modern, Apple-inspired Student Management System built with **FastAPI**, **PostgreSQL**, and **Jinja2** templates. Designed for schools and educational institutions to manage students, teachers, classes, subjects, and weekly timetables.

---

## Features

| Module | Capabilities |
|---|---|
| **Dashboard** | Live stats, recent registrations, quick actions |
| **Students** | Registration, profiles, class assignment, guardian info |
| **Teachers** | Staff records, specialization, qualifications |
| **Classes** | Grade/section management, occupancy tracking |
| **Subjects** | Curriculum builder with codes and categories |
| **Routine** | Weekly timetable scheduler with visual grid |
| **Auth** | JWT cookie-based login, admin seeded on first run |

---

## Tech Stack

- **Backend** — Python 3.11+, FastAPI 0.115, SQLAlchemy 2.0 (async)
- **Database** — PostgreSQL 14+ via asyncpg driver
- **Templates** — Jinja2 (server-side rendered HTML)
- **Styling** — Custom CSS (Apple-inspired design system, no framework needed)
- **Auth** — JWT tokens stored in HTTP-only cookies, bcrypt password hashing

---

## Project Structure

```
Student-Management/
├── app/
│   ├── main.py               # FastAPI app, lifespan, router registration
│   ├── config.py             # Settings from .env via pydantic-settings
│   ├── database.py           # Async SQLAlchemy engine + session
│   ├── dependencies.py       # Auth guards (login_required, get_current_user)
│   ├── models/
│   │   ├── user.py           # Admin / staff users
│   │   ├── student.py        # Student records
│   │   ├── teacher.py        # Teacher records
│   │   ├── class_.py         # Classes (Grade 10-A etc.)
│   │   ├── subject.py        # Subjects + ClassSubject junction
│   │   └── routine.py        # Weekly timetable slots
│   ├── schemas/              # Pydantic v2 request/response models
│   ├── routers/
│   │   ├── auth.py           # /login, /logout
│   │   ├── dashboard.py      # /dashboard
│   │   ├── students.py       # /students CRUD
│   │   ├── teachers.py       # /teachers CRUD
│   │   ├── classes.py        # /classes CRUD
│   │   ├── subjects.py       # /subjects CRUD
│   │   └── routines.py       # /routines CRUD
│   ├── services/
│   │   └── auth_service.py   # JWT, bcrypt, admin seed
│   ├── templates/            # Jinja2 HTML templates
│   │   ├── base.html         # Sidebar layout
│   │   ├── login.html        # Sign-in page
│   │   ├── dashboard.html
│   │   ├── students/         # list, form, detail
│   │   ├── teachers/         # list, form, detail
│   │   ├── classes/          # list, form
│   │   ├── subjects/         # list, form
│   │   └── routines/         # list, form
│   └── static/
│       ├── css/main.css      # Full Apple-inspired design system
│       └── js/main.js        # Toast, confirm delete, stat animation
├── migrations/
│   └── 001_init.sql          # Manual SQL (optional — app auto-creates tables)
├── run.py                    # Entry point  →  python run.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher running locally
- `pip` or `uv`

### 2. Create the database

```sql
-- In psql or pgAdmin:
CREATE DATABASE student_mgmt;
```

### 3. Clone / copy the project

```bash
cd "C:\Python Development\Student-Management"
```

### 4. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment

```bash
# Copy the example file
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux

# Edit .env with your database credentials
```

**.env file:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/student_mgmt
SECRET_KEY=change-this-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@school.edu

APP_NAME=EduSphere
DEBUG=True
```

### 7. Run the application

```bash
python run.py
```

The app will:
1. Auto-create all database tables on first run
2. Seed the default admin user
3. Start at **http://127.0.0.1:8000**

### 8. Login

Open **http://127.0.0.1:8000** in your browser.

| Field | Default Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

> Change these in your `.env` file before deploying.

---

## URL Reference

| URL | Method | Description |
|---|---|---|
| `/` | GET | Redirect to dashboard |
| `/login` | GET / POST | Sign in |
| `/logout` | GET | Sign out |
| `/dashboard` | GET | Stats overview |
| `/students` | GET | Student list (search, filter) |
| `/students/new` | GET / POST | Register student |
| `/students/{id}` | GET | Student profile |
| `/students/{id}/edit` | GET / POST | Edit student |
| `/students/{id}/delete` | POST | Delete student |
| `/teachers` | GET | Teacher list |
| `/teachers/new` | GET / POST | Add teacher |
| `/teachers/{id}` | GET | Teacher profile |
| `/teachers/{id}/edit` | GET / POST | Edit teacher |
| `/classes` | GET | Class cards with occupancy |
| `/classes/new` | GET / POST | Create class |
| `/classes/{id}/edit` | GET / POST | Edit class |
| `/subjects` | GET | Subject list |
| `/subjects/new` | GET / POST | Add subject |
| `/subjects/{id}/edit` | GET / POST | Edit subject |
| `/routines` | GET | Timetable grid + list |
| `/routines/new` | GET / POST | Schedule period |
| `/routines/{id}/edit` | GET / POST | Edit period |

---

## Auto-Generated IDs

| Entity | Format | Example |
|---|---|---|
| Student | `SMS-YYYY-NNNN` | `SMS-2024-0001` |
| Teacher | `TCH-YYYY-NNNN` | `TCH-2024-0001` |

---

## Database Schema

```
users ──────────────────────────────────────────────────
  id, username, email, hashed_password, is_admin

teachers ───────────────────────────────────────────────
  id, teacher_id, first_name, last_name, email,
  specialization, qualification, join_date, status

classes ────────────────────────────────────────────────
  id, name, section, grade_level, capacity,
  class_teacher_id → teachers.id

students ───────────────────────────────────────────────
  id, student_id, first_name, last_name, email,
  guardian_name, guardian_phone, class_id → classes.id,
  enrollment_date, status, blood_group

subjects ───────────────────────────────────────────────
  id, code, name, credits, category

class_subjects (junction) ──────────────────────────────
  class_id → classes.id
  subject_id → subjects.id
  teacher_id → teachers.id

routines ───────────────────────────────────────────────
  class_id → classes.id
  subject_id → subjects.id
  teacher_id → teachers.id
  day_of_week, start_time, end_time, room_number
```

---

## Development Tips

**Hot reload** — `run.py` uses `reload=True` so the server restarts on every file save.

**Add a new admin user** — Update `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env` and delete the existing admin row in the `users` table, then restart.

**Change port** — Edit `run.py`:
```python
uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
```

**Production checklist:**
- Set `DEBUG=False` in `.env`
- Use a long random `SECRET_KEY` (e.g. `openssl rand -hex 32`)
- Run behind nginx / gunicorn
- Enable HTTPS

---

## Beginner Notes

| Concept | Where to look |
|---|---|
| How routes work | `app/routers/*.py` |
| How database models work | `app/models/*.py` |
| How forms are processed | `Form(...)` params in routers |
| How authentication works | `app/services/auth_service.py` |
| How pages are rendered | `app/templates/` |
| How the design is built | `app/static/css/main.css` |
| App startup / table creation | `app/main.py` → `lifespan()` |

---

## License

MIT — free to use, modify, and distribute.
