# Smart Academic Management System (Flask + MySQL)

Production-style Academic ERP with RBAC (Admin, Teacher, Student), MVC architecture, secure auth, marks, attendance, assignment sharing, notifications, and analytics.

## 1) Folder Structure

```text
smart acedemic management system/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   ├── utils.py
│   ├── blueprints/
│   │   ├── auth/routes.py
│   │   ├── main/routes.py
│   │   ├── admin/routes.py
│   │   ├── teacher/routes.py
│   │   └── student/routes.py
│   ├── templates/
│   └── static/css/style.css
├── scripts/seed_data.py
├── schema.sql
├── requirements.txt
├── config.py
└── run.py
```

## 2) Architecture (MVC)

- **Model:** `app/models.py` with SQLAlchemy entities and relationships.
- **View:** Jinja templates in `app/templates/`.
- **Controller:** Flask blueprints in `app/blueprints/*/routes.py`.

## 3) Features by Module

### Authentication
- Flask-Login session management
- Bcrypt password hashing
- OTP-based login verification (email OTP)
- CSRF via Flask-WTF
- Dashboard routing by role
- Separate registration pages for admin, teacher, and student

### Admin
- Create/delete students and teachers
- Manage classes and subjects
- Assign teachers to class-subject pairs
- Analytics: top students, pass/fail, attendance ratio

### Teacher
- Access only assigned class-subject combinations
- Record marks (internal/external), auto-grade
- Record attendance
- Upload notes/assignments (file storage)
- Email result updates with Flask-Mail

### Student
- View profile
- View marks and grade
- View attendance %
- Download assignments
- Chart.js performance graph + simple predicted score

## 4) Database (MySQL)

- Core tables: `users`, `students`, `teachers`, `classes`, `subjects`, `teacher_subject_assignments`, `marks`, `attendance`, `assignments`, `notifications`
- SQL script: `schema.sql`

## 5) Setup Instructions (Step by Step)

1. **Create virtual environment**
   - Windows PowerShell:
     - `python -m venv .venv`
     - `.venv\Scripts\Activate.ps1`
2. **Install dependencies**
   - `pip install -r requirements.txt`
3. **Create environment file**
   - Copy `.env.example` to `.env`
   - Update MySQL credentials and mail credentials
4. **Create database tables**
   - Option A: Run `schema.sql` directly in MySQL
   - Option B: Use SQLAlchemy create-all from seed script
5. **Insert sample test data**
   - `python scripts/seed_data.py`
6. **Run app**
   - `python run.py`
7. **Login with test users**
   - Admin: `admin@sams.com / Admin@123`
   - Teacher: `teacher@sams.com / Teacher@123`
   - Student: `student@sams.com / Student@123`

## 6) Exam and Marks Logic

- Teacher inputs internal (40) + external (60)
- Total and percentage calculated automatically
- Grade mapping:
  - A+ (>=90), A (>=80), B (>=70), C (>=60), D (>=50), F (<50)

## 7) Security Controls

- Password hashing (`Flask-Bcrypt`)
- CSRF protection (`Flask-WTF`)
- ORM-based prepared queries (`SQLAlchemy`)
- Role-based route guard (`role_required`)
- Session timeout (`PERMANENT_SESSION_LIFETIME`)

## 8) Scalability Suggestions

- Add Redis cache + Celery for async email/notifications
- Store files in S3/Blob instead of local upload folder
- Add pagination and API layer for mobile clients
- Add unit and integration tests (pytest)

## 9) Viva Questions and Answers

See `VIVA_QA.md`.
"# smart-academic-management" 
