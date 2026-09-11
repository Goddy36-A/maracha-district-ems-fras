#!/usr/bin/env python
"""
Maracha District EMS Local Startup — Run: python start.py
Does everything automatically. No manual config needed.
"""
import os, sys, subprocess, time, webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE  = BASE_DIR / ".env"
SETTINGS  = "config.settings.development"
ADMIN     = {"username": "admin", "password": "Admin@12345", "email": "admin@maracha.go.ug"}

# ── Set env var immediately at module level so django.setup() always works ──
os.environ["DJANGO_SETTINGS_MODULE"] = SETTINGS

GREEN  = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"
RESET  = "\033[0m";  BOLD = "\033[1m"

def ok(msg):   print(f"{GREEN}✅ {msg}{RESET}")
def err(msg):  print(f"{RED}❌ {msg}{RESET}")
def info(msg): print(f"{YELLOW}➜  {msg}{RESET}")
def hdr(msg):  print(f"\n{BOLD}{msg}{RESET}")

def banner():
    print(f"""
{BOLD}╔══════════════════════════════════════════╗
║   Maracha District Local Government     ║
║   Employee Management System — Local    ║
╚══════════════════════════════════════════╝{RESET}
""")

def install_deps():
    """Install packages one by one — skips any that fail (e.g. psycopg2 without PostgreSQL)."""
    info("Installing dependencies...")
    req_file = BASE_DIR / "requirements.txt"
    if not req_file.exists():
        print(f"{YELLOW}⚠️  requirements.txt not found — skipping{RESET}")
        return

    lines = req_file.read_text(encoding="utf-8").splitlines()
    pkgs  = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]

    failed = []
    for pkg in pkgs:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "-q",
             "--only-binary=:all:", "--no-build-isolation"],
            capture_output=True
        )
        if r.returncode != 0:
            # Retry without binary restriction (some packages are fine)
            r2 = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "-q"],
                capture_output=True
            )
            if r2.returncode != 0:
                failed.append(pkg)
                print(f"{YELLOW}  ⚠ Skipped (not available locally): {pkg}{RESET}")

    if failed:
        print(f"{YELLOW}  Skipped {len(failed)} package(s) that need native tools or servers.{RESET}")
        print(f"{YELLOW}  This is normal for SQLite local setup.{RESET}")
    ok("Dependencies ready")


def fix_env():
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        patched, has_settings = [], False
        for line in lines:
            s = line.strip()
            if s.startswith("DATABASE_URL=postgresql") or s.startswith("DATABASE_URL=postgres"):
                patched.append("# " + line + "  # disabled for local SQLite")
                ok("Disabled PostgreSQL DATABASE_URL → using SQLite")
            elif "DJANGO_SETTINGS_MODULE" in s and not s.startswith("#"):
                patched.append("DJANGO_SETTINGS_MODULE=" + SETTINGS)
                has_settings = True
            else:
                patched.append(line)
        if not has_settings:
            patched.append("DJANGO_SETTINGS_MODULE=" + SETTINGS)
        ENV_FILE.write_text("\n".join(patched), encoding="utf-8")
    else:
        ENV_FILE.write_text(
            f"DJANGO_SETTINGS_MODULE={SETTINGS}\n"
            "SECRET_KEY=django-insecure-maracha-local-dev-only\n"
            "DEBUG=True\n", encoding="utf-8"
        )
        ok(".env created for local development")

def run(cmd, capture=False):
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": SETTINGS}
    return subprocess.run(
        [sys.executable, "manage.py"] + cmd,
        cwd=BASE_DIR, env=env,
        capture_output=capture, text=capture
    )

def migrate():
    info("Running database migrations...")
    run(["makemigrations", "--settings=" + SETTINGS])
    result = run(["migrate"])
    if result.returncode != 0:
        err("Migration failed. Check errors above.")
        sys.exit(1)
    ok("Migrations complete")

def create_admin():
    info("Setting up admin account...")
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": SETTINGS,
        "DJANGO_SUPERUSER_USERNAME": ADMIN["username"],
        "DJANGO_SUPERUSER_PASSWORD": ADMIN["password"],
        "DJANGO_SUPERUSER_EMAIL":    ADMIN["email"],
    }
    r = subprocess.run(
        [sys.executable, "manage.py", "createsuperuser", "--no-input"],
        cwd=BASE_DIR, env=env, capture_output=True, text=True
    )
    if r.returncode == 0:
        ok(f"Admin created  →  username: {ADMIN['username']}  |  password: {ADMIN['password']}")
    elif "already exists" in (r.stderr + r.stdout):
        ok(f"Admin already exists  →  username: {ADMIN['username']}  |  password: {ADMIN['password']}")
    else:
        print(f"{YELLOW}⚠️  Admin note: {r.stderr.strip() or r.stdout.strip()}{RESET}")

    # Always ensure admin password is correct and account is unlocked
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = User.objects.get(username=ADMIN["username"])
        u.set_password(ADMIN["password"])
        u.is_locked = False
        u.failed_login_attempts = 0
        u.save()
        ok("Admin password confirmed and account unlocked")
    except Exception as e:
        print(f"{YELLOW}⚠️  Admin reset: {e}{RESET}")

def seed_demo_data():
    """Seed realistic Maracha District demo data for presentation."""
    import django
    django.setup()

    import datetime
    from django.contrib.auth import get_user_model
    from apps.departments.models      import Department, Position
    from apps.employees.models        import Employee
    from apps.leave_management.models import LeaveType
    from apps.attendance.models       import Attendance

    User  = get_user_model()
    today = datetime.date.today()

    hdr("Seeding demo data for Maracha District...")

    # ── Departments ──────────────────────────────────────────────────
    dept_data = [
        ("Education Department",                           "EDU"),
        ("Health Department",                              "HLT"),
        ("Local Government Administration",                "LGA"),
        ("Finance & Planning Department",                  "FIN"),
        ("Infrastructure & Works Department",              "INF"),
        ("Production & Marketing Department",              "PMK"),
    ]
    depts = {}
    for name, code in dept_data:
        d, _ = Department.objects.get_or_create(code=code, defaults={"name": name})
        depts[code] = d
    ok(f"Departments ready ({len(depts)})")

    # ── Positions ────────────────────────────────────────────────────
    pos_data = [
        ("District Education Officer",  "EDU"), ("School Inspector",            "EDU"),
        ("District Health Officer",     "HLT"), ("Health Facility Supervisor",  "HLT"),
        ("District Commissioner",       "LGA"), ("Administrative Officer",      "LGA"),
        ("Chief Finance Officer",       "FIN"), ("Budget Officer",              "FIN"),
        ("Director of Works",           "INF"), ("Engineer",                    "INF"),
        ("Production Officer",          "PMK"), ("Marketing Officer",           "PMK"),
    ]
    positions = {}
    for title, code in pos_data:
        p, _ = Position.objects.get_or_create(title=title, department=depts[code])
        positions[(title, code)] = p
    ok(f"Positions ready ({len(positions)})")

    # ── Leave Types ──────────────────────────────────────────────────
    leave_types = [
        ("Annual Leave",        21, "Standard annual leave entitlement"),
        ("Sick Leave",          10, "Medical/illness leave"),
        ("Maternity Leave",     60, "Maternity leave for female staff"),
        ("Paternity Leave",      5, "Paternity leave for male staff"),
        ("Study Leave",         14, "Leave for professional development"),
        ("Compassionate Leave",  3, "Bereavement or family emergency"),
        ("Unpaid Leave",         0, "Leave without pay, approved by management"),
    ]
    for name, days, desc in leave_types:
        LeaveType.objects.get_or_create(name=name, defaults={"default_annual_days": days, "description": desc})
    ok(f"Leave types ready ({len(leave_types)})")

    # ── Demo Employees + User Accounts (Maracha District) ──────────────
    employees_data = [
        ("MAR-2023-001","Peter",    "Otim",      "p.otim@maracha.go.ug",    "EDU","District Education Officer","FULL_TIME","otim",      "Pass@2025","DEPARTMENT_HEAD"),
        ("MAR-2023-002","Alice",    "Akello",    "a.akello@maracha.go.ug",  "EDU","School Inspector",         "FULL_TIME","akello",    "Pass@2025","EMPLOYEE"),
        ("MAR-2023-003","Samuel",   "Lokwang",   "s.lokwang@maracha.go.ug", "HLT","District Health Officer",  "FULL_TIME","lokwang",   "Pass@2025","EMPLOYEE"),
        ("MAR-2024-001","Mary",     "Adwok",     "m.adwok@maracha.go.ug",   "HLT","Health Facility Supervisor","FULL_TIME","adwok",     "Pass@2025","EMPLOYEE"),
        ("MAR-2022-001","Joseph",   "Awol",      "j.awol@maracha.go.ug",    "LGA","District Commissioner",    "FULL_TIME","awol",      "Pass@2025","HR"),
        ("MAR-2022-002","Grace",    "Lematec",   "g.lematec@maracha.go.ug", "LGA","Administrative Officer",   "FULL_TIME","lematec",   "Pass@2025","HR"),
        ("MAR-2021-001","John",     "Lomongin",  "j.lomongin@maracha.go.ug","FIN","Chief Finance Officer",    "FULL_TIME","lomongin",  "Pass@2025","EMPLOYEE"),
        ("MAR-2020-001","Catherine","Omoding",   "c.omoding@maracha.go.ug", "INF","Director of Works",        "FULL_TIME","omoding",   "Pass@2025","MANAGEMENT"),
        ("MAR-2024-002","Geoffrey", "Lolem",     "g.lolem@maracha.go.ug",   "INF","Engineer",                 "FULL_TIME","lolem",     "Pass@2025","EMPLOYEE"),
        ("MAR-2024-003","Beatrice", "Lokwang",   "b.lokwang@maracha.go.ug", "PMK","Production Officer",       "CONTRACT", "lokwang2", "Pass@2025","EMPLOYEE"),
    ]
    created = 0
    for (eid, fn, ln, email, dcode, pos, etype, uname, pwd, role) in employees_data:
        user, u_new = User.objects.get_or_create(
            username=uname,
            defaults={"email": email, "first_name": fn, "last_name": ln, "role": role}
        )
        if u_new:
            user.set_password(pwd); user.save()

        emp, e_new = Employee.objects.get_or_create(
            employee_id=eid,
            defaults={
                "user": user, "first_name": fn, "last_name": ln, "email": email,
                "employment_type": etype, "employment_status": "ACTIVE",
                "date_joined_org": today.replace(year=int(eid.split("-")[1])),
                "department": depts[dcode],
                "position": positions.get((pos, dcode)),
            }
        )
        if e_new: created += 1
    ok(f"Demo employees ready ({created} new, {len(employees_data)-created} existing)")

    # ── Admin employee profile ───────────────────────────────────────
    try:
        admin_user = User.objects.get(username=ADMIN["username"])
        if not hasattr(admin_user, "employee_profile") or admin_user.employee_profile is None:
            Employee.objects.get_or_create(
                employee_id="MAR-ADMIN-001",
                defaults={
                    "user": admin_user, "first_name": "System", "last_name": "Administrator",
                    "email": ADMIN["email"], "employment_type": "FULL_TIME",
                    "employment_status": "ACTIVE", "date_joined_org": today,
                }
            )
            ok("Admin employee profile linked")
        else:
            ok("Admin profile already linked")
    except Exception as e:
        print(f"{YELLOW}⚠️  Admin profile: {e}{RESET}")

    # ── Today's Attendance ───────────────────────────────────────────
    statuses = ["PRESENT","PRESENT","PRESENT","PRESENT","PRESENT",
                "PRESENT","LATE","PRESENT","PRESENT","ON_LEAVE"]
    att_count = 0
    try:
        for i, emp in enumerate(Employee.objects.filter(employment_status="ACTIVE")):
            status = statuses[i % len(statuses)]
            _, created_att = Attendance.objects.get_or_create(
                employee=emp, date=today,
                defaults={
                    "status": status,
                    "check_in_time": __import__("datetime").time(8, 0) if status == "PRESENT"
                                     else (__import__("datetime").time(9, 15) if status == "LATE" else None),
                }
            )
            if created_att: att_count += 1
        ok(f"Today's attendance seeded ({att_count} new records)")
    except Exception as e:
        print(f"{YELLOW}⚠️  Attendance: {e}{RESET}")

    hdr("Demo data ready.")
    print(f"""
  {BOLD}Presentation accounts:{RESET}
  ┌──────────────┬──────────────┬──────────────────┐
  │ Username     │ Password     │ Role             │
  ├──────────────┼──────────────┼──────────────────┤
  │ admin        │ Admin@12345  │ Administrator    │
  │ awol         │ Pass@2025    │ HR Manager       │
  │ otim         │ Pass@2025    │ Department Head  │
  │ akello       │ Pass@2025    │ Employee         │
  │ omoding      │ Pass@2025    │ Management       │
  └──────────────┴──────────────┴──────────────────┘
""")

def start_server():
    url = "http://127.0.0.1:8000"
    print(f"""
{BOLD}🚀 Server starting...{RESET}
   App:   {url}
   Admin: {url}/admin
   Stop   →  Ctrl+C
""")
    time.sleep(1)
    webbrowser.open(url)
    run(["runserver"])

if __name__ == "__main__":
    banner()
    install_deps()
    fix_env()
    migrate()
    create_admin()
    seed_demo_data()
    start_server()
