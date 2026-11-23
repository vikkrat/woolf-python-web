"""Seed an empty database with reproducible Ukrainian sample data."""

import random

from faker import Faker
from sqlalchemy import select

from db import SessionLocal
from models import Grade, Group, Student, Subject, Teacher


def seed():
    fake = Faker("uk_UA")
    Faker.seed(42)
    random.seed(42)
    with SessionLocal.begin() as session:
        if session.scalar(select(Group.id).limit(1)) is not None:
            raise SystemExit(
                "Database already contains data; seed refused to duplicate it."
            )
        groups = [Group(name=f"CS-{number}") for number in range(101, 104)]
        teachers = [Teacher(name=fake.name()) for _ in range(4)]
        session.add_all(groups + teachers)
        session.flush()
        subjects = [
            Subject(name=name, teacher_id=teachers[i % 4].id)
            for i, name in enumerate(
                [
                    "Python",
                    "Databases",
                    "Algorithms",
                    "Mathematics",
                    "Networks",
                    "Web",
                    "English",
                ]
            )
        ]
        session.add_all(subjects)
        session.flush()
        for i in range(40):
            student = Student(name=fake.name(), group_id=groups[i % 3].id)
            session.add(student)
            session.flush()
            for _ in range(random.randint(10, 20)):
                session.add(
                    Grade(
                        student_id=student.id,
                        subject_id=random.choice(subjects).id,
                        value=random.randint(50, 100),
                        received_at=fake.date_between("-1y", "today"),
                    )
                )


if __name__ == "__main__":
    seed()
