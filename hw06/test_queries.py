"""Check all query semantics against a small known dataset."""

import os
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base, Grade, Group, Student, Subject, Teacher
import my_select as queries


def test_queries():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all(
            [
                Group(id=1, name="A"),
                Group(id=2, name="B"),
                Teacher(id=1, name="Teacher"),
                Student(id=1, name="Alice", group_id=1),
                Student(id=2, name="Bob", group_id=2),
                Subject(id=1, name="Python", teacher_id=1),
            ]
        )
        db.flush()
        db.add_all(
            [
                Grade(
                    student_id=1, subject_id=1, value=80, received_at=date(2026, 1, 1)
                ),
                Grade(
                    student_id=1, subject_id=1, value=100, received_at=date(2026, 1, 2)
                ),
                Grade(
                    student_id=2, subject_id=1, value=60, received_at=date(2026, 1, 3)
                ),
            ]
        )
        db.commit()
        assert queries.select_1(db)[0][0] == 1
        assert queries.select_2(db, 1)[0][2] == 90
        assert dict(queries.select_3(db, 1)) == {"A": 90, "B": 60}
        assert queries.select_4(db) == 80
        assert queries.select_5(db, 1) == [(1, "Python")]
        assert queries.select_6(db, 1) == [(1, "Alice")]
        assert len(queries.select_7(db, 1, 1)) == 2
        assert queries.select_8(db, 1) == 80
        assert queries.select_9(db, 1) == [(1, "Python")]
        assert queries.select_10(db, 1, 1) == [(1, "Python")]
        assert queries.select_11(db, 1, 1) == 90
        assert queries.select_12(db, 1, 1) == [("Alice", 100, date(2026, 1, 2))]
    engine.dispose()
