"""Ten required and two optional queries using SQLAlchemy sessions."""

import argparse

from sqlalchemy import func, select

from db import SessionLocal
from models import Grade, Group, Student, Subject


def select_1(session):
    """Five students with the highest overall average."""
    return session.execute(
        select(Student.id, Student.name, func.avg(Grade.value).label("average"))
        .join(Grade)
        .group_by(Student.id, Student.name)
        .order_by(func.avg(Grade.value).desc(), Student.id)
        .limit(5)
    ).all()


def select_2(session, subject_id):
    """Top student for one subject."""
    return session.execute(
        select(Student.id, Student.name, func.avg(Grade.value).label("average"))
        .join(Grade)
        .where(Grade.subject_id == subject_id)
        .group_by(Student.id, Student.name)
        .order_by(func.avg(Grade.value).desc(), Student.id)
        .limit(1)
    ).all()


def select_3(session, subject_id):
    """Group averages for one subject."""
    return session.execute(
        select(Group.name, func.avg(Grade.value))
        .select_from(Group)
        .join(Student)
        .join(Grade)
        .where(Grade.subject_id == subject_id)
        .group_by(Group.id, Group.name)
        .order_by(Group.id)
    ).all()


def select_4(session):
    """Average across all grades."""
    return session.scalar(select(func.avg(Grade.value)))


def select_5(session, teacher_id):
    """Subjects taught by a teacher."""
    return session.execute(
        select(Subject.id, Subject.name).where(Subject.teacher_id == teacher_id)
    ).all()


def select_6(session, group_id):
    """Students belonging to a group."""
    return session.execute(
        select(Student.id, Student.name).where(Student.group_id == group_id)
    ).all()


def select_7(session, group_id, subject_id):
    """Dated grades for a group and subject."""
    return session.execute(
        select(Student.name, Grade.value, Grade.received_at)
        .join(Grade)
        .where(Student.group_id == group_id, Grade.subject_id == subject_id)
        .order_by(Grade.received_at, Student.id)
    ).all()


def select_8(session, teacher_id):
    """Average awarded by a teacher across their subjects."""
    return session.scalar(
        select(func.avg(Grade.value))
        .join(Subject)
        .where(Subject.teacher_id == teacher_id)
    )


def select_9(session, student_id):
    """Subjects with recorded attendance (grades) for a student."""
    return session.execute(
        select(Subject.id, Subject.name)
        .join(Grade)
        .where(Grade.student_id == student_id)
        .distinct()
    ).all()


def select_10(session, student_id, teacher_id):
    """Subjects a student takes with a given teacher."""
    return session.execute(
        select(Subject.id, Subject.name)
        .join(Grade)
        .where(Grade.student_id == student_id, Subject.teacher_id == teacher_id)
        .distinct()
    ).all()


def select_11(session, student_id, teacher_id):
    """Average awarded by a teacher to a student."""
    return session.scalar(
        select(func.avg(Grade.value))
        .join(Subject)
        .where(Grade.student_id == student_id, Subject.teacher_id == teacher_id)
    )


def select_12(session, group_id, subject_id):
    """Grades at the latest lesson for this group and subject."""
    last = (
        select(func.max(Grade.received_at))
        .join(Student)
        .where(Student.group_id == group_id, Grade.subject_id == subject_id)
        .scalar_subquery()
    )
    return session.execute(
        select(Student.name, Grade.value, Grade.received_at)
        .join(Grade)
        .where(
            Student.group_id == group_id,
            Grade.subject_id == subject_id,
            Grade.received_at == last,
        )
    ).all()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("number", type=int, choices=range(1, 13))
    parser.add_argument("--subject-id", type=int, default=1)
    parser.add_argument("--group-id", type=int, default=1)
    parser.add_argument("--teacher-id", type=int, default=1)
    parser.add_argument("--student-id", type=int, default=1)
    args = parser.parse_args()
    import inspect

    query = globals()[f"select_{args.number}"]
    parameters = {
        name: getattr(args, name)
        for name in inspect.signature(query).parameters
        if name != "session"
    }
    with SessionLocal() as session:
        print(query(session, **parameters))
