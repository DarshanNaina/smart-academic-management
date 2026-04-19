from app import create_app
from app.extensions import db
from app.models import ClassRoom, Student, Subject, Teacher, TeacherSubjectAssignment, User

app = create_app()

with app.app_context():
    db.create_all()

    admin = User(full_name="System Admin", email="admin@sams.com", role="admin")
    admin.set_password("Admin@123")
    db.session.add(admin)

    class_a = ClassRoom(name="10", section="A")
    db.session.add(class_a)
    db.session.flush()

    teacher_user = User(full_name="Rahul Sharma", email="teacher@sams.com", role="teacher")
    teacher_user.set_password("Teacher@123")
    db.session.add(teacher_user)
    db.session.flush()
    teacher = Teacher(user_id=teacher_user.id, employee_code="EMP1001")
    db.session.add(teacher)

    student_user = User(full_name="Priya Singh", email="student@sams.com", role="student")
    student_user.set_password("Student@123")
    db.session.add(student_user)
    db.session.flush()
    student = Student(
        user_id=student_user.id,
        admission_no="ADM1001",
        class_id=class_a.id,
        roll_no="01",
        guardian_name="Mr. Singh",
    )
    db.session.add(student)

    math = Subject(name="Mathematics", code="MATH101")
    db.session.add(math)
    db.session.flush()

    db.session.add(
        TeacherSubjectAssignment(
            teacher_id=teacher.id,
            class_id=class_a.id,
            subject_id=math.id,
        )
    )

    db.session.commit()
    print("Seed data inserted.")
