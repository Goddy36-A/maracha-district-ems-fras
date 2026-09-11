# MIU Employee Management System

> **Final-Year Project — Bachelor of Computer Science**
> Metropolitan International University (MIU), Kampala, Uganda
>
> *Evaluating the Effectiveness of an Employee Management System on
> Workforce Administration and Organisational Performance at MIU.*

---

## 🚀 One-Command Local Setup

No manual configuration required. Run a single file and the system does everything:

```bash
git clone https://github.com/Goddy36-A/miu-ems.git
cd miu-ems
pip install -r requirements.txt
python start.py
```

The browser opens automatically at **http://127.0.0.1:8000**

### What `start.py` does automatically

| Step | What happens |
|------|-------------|
| `.env` setup | Creates `.env` and enables SQLite (no PostgreSQL needed) |
| Migrations | Runs all database migrations |
| Admin account | Creates `admin / Admin@12345` superuser |
| Demo data | Seeds departments, positions, leave types, 10 employees, today's attendance |
| Browser | Opens the app automatically |

> On Windows you can also double-click **`start.bat`** instead.

---

## 🔑 Demo Accounts

All accounts are created automatically by `start.py`.

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `admin` | `Admin@12345` | Administrator | Full system access + Admin Panel |
| `nabirye` | `Pass@2025` | HR Manager | Employee management, leave approval, reports |
| `nakato` | `Pass@2025` | Department Head | Department view, leave approvals, evaluations |
| `mugisha` | `Pass@2025` | Employee | Own attendance, leave, performance, documents |
| `tumwine` | `Pass@2025` | Management | Workforce analytics and reports |

---

## ✅ Features Implemented

### Core HR Modules
- **Employee Management** — Full employee profiles, employment types, status lifecycle
- **Department & Position Management** — Organisational structure with department heads
- **Attendance Tracking** — Daily records, check-in/out times, status types (Present, Absent, Late, On Leave, Excused, Remote)
- **Leave Management** — Full two-stage approval workflow (Employee → Dept Head → HR), leave balances per type
- **Performance Evaluations** — Configurable cycles, weighted criteria, five-stage workflow (Open → Self-Assessed → Supervisor-Assessed → Finalized → Acknowledged)
- **Document Management** — Secure, authorization-gated employee document storage
- **Reports** — Role-restricted HR and workforce reports with CSV export
- **Notifications** — In-app notifications for key events (leave decisions, evaluation updates)
- **Audit Trail** — Immutable log of every significant system action

### System & Security
- **Role-Based Access Control** — 5 roles: Admin, HR, Department Head, Management, Employee
- **Account Security** — Lockout after 5 failed logins, forced password change on first login
- **Server-side Authorization** — Every view enforces permissions; UI hiding alone is never relied on
- **Custom Branding** — MIU green `hsl(145,65%,28%)` and gold `hsl(38,70%,50%)` applied system-wide via CSS variables
- **System Effectiveness Module** — Baseline vs. post-implementation indicators and satisfaction survey

---

## 🏗 Project Structure

```
miu-ems/
├── start.py                        # ← Run this to launch everything
├── start.bat                       # ← Double-click launcher (Windows)
├── manage.py
├── requirements.txt
├── pyproject.toml
├── config/
│   ├── settings/
│   │   ├── base.py                 # Shared settings, MIU branding config
│   │   ├── development.py          # SQLite, debug toolbar
│   │   ├── production.py           # PostgreSQL, HTTPS, HSTS
│   │   └── testing.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/                   # Custom User model, auth, lockout
│   ├── core/                       # Shared models, RBAC helpers, error pages
│   ├── departments/                # Department, Position
│   ├── employees/                  # Employee profiles
│   ├── attendance/                 # Attendance records + rate calculation
│   ├── leave_management/           # LeaveType, LeaveRequest, LeaveBalance
│   ├── performance/                # Cycles, criteria, evaluations, scoring
│   ├── documents/                  # Secure document storage
│   ├── notifications/              # In-app notifications
│   ├── audit/                      # Immutable AuditLog + middleware
│   ├── reports/                    # HR/workforce reports + CSV export
│   └── dashboard/                  # Role dashboards + effectiveness module
├── templates/
│   ├── base.html                   # MIU-branded base with green/gold header
│   └── ...                         # Per-app templates
└── static/
    ├── css/miu-theme.css           # MIU CSS variables and component styles
    └── miu/logo-placeholder.svg    # MIU crest (green shield, gold accents)
```

---

## 🎨 Brand Colors

Defined as CSS variables in `static/css/miu-theme.css` and mirrored in `config/settings/base.py → MIU_BRANDING`:

```css
--miu-primary:      hsl(145, 65%, 28%);   /* MIU green  */
--miu-secondary:    hsl(150, 50%, 20%);   /* Dark green */
--miu-accent:       hsl(38,  70%, 50%);   /* MIU gold   */
--miu-hero-gradient: linear-gradient(135deg, hsl(145,65%,28%), hsl(150,50%,20%));
--miu-gold-gradient: linear-gradient(135deg, hsl(38,70%,50%),  hsl(45,80%,55%));
```

---

## 🧪 Running Tests

```bash
python manage.py test apps --settings=config.settings.testing
```

Covers: leave workflow, attendance calculations, performance weighted scoring,
authorization boundaries (IDOR and privilege-escalation checks).

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6.1 (Python 3.12+) |
| Database | SQLite (local) / PostgreSQL (production) |
| ORM | Django ORM with custom abstract models |
| Auth | Custom `AbstractUser` + `SecureAuthBackend` |
| Static files | WhiteNoise |
| Styling | Vanilla CSS with CSS custom properties |
| Testing | Django `TestCase` + `Client` |

---

## 🔒 Security Notes

- Authorization enforced server-side in every view (`apps/core/permissions.py`)
- Employee documents stored outside public media — only accessible via `documents:download` which checks auth and writes to audit log
- Account lockout after 5 failed login attempts
- All significant actions recorded in an immutable `AuditLog` (no update/delete path exists)
- Production settings refuse SQLite and enforce HTTPS/HSTS/secure cookies

---

## 📋 Outstanding / Next Steps

- REST API endpoints (Django REST Framework)
- PDF/Excel export beyond CSV
- Async notifications (Celery + Redis)
- Full accessibility audit (WCAG 2.1)
- Nginx + Gunicorn production deployment manifests

---

## 👤 Author

**Godfrey** — Final-Year BCS Student, Metropolitan International University
Kampala, Uganda · 2026

---

*Demo data only — no real MIU employee records are included in this repository.*
