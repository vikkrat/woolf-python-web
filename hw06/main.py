"""Optional CRUD CLI for every university model."""

import argparse
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db import SessionLocal
from models import Grade, Group, Student, Subject, Teacher

MODELS = {model.__name__: model for model in (Teacher, Group, Student, Subject, Grade)}
FIELDS = {
    "Teacher": ["name"],
    "Group": ["name"],
    "Student": ["name", "group_id"],
    "Subject": ["name", "teacher_id"],
    "Grade": ["student_id", "subject_id", "value", "received_at"],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--action",
        "-action",
        "-a",
        choices=["create", "list", "update", "remove"],
        required=True,
    )
    parser.add_argument("--model", "-m", choices=MODELS, required=True)
    parser.add_argument("--id", type=int)
    parser.add_argument("--name", "-n")
    for key in ["group", "teacher", "student", "subject"]:
        parser.add_argument(f"--{key}-id", type=int)
    parser.add_argument("--value", type=int, choices=range(1, 101))
    parser.add_argument("--received-at", type=date.fromisoformat)
    args = parser.parse_args()
    model = MODELS[args.model]
    data = {
        field: getattr(args, field)
        for field in FIELDS[args.model]
        if getattr(args, field) is not None
    }
    if "name" in data and not data["name"].strip():
        parser.error("Name cannot be empty")
    if args.action == "create" and len(data) != len(FIELDS[args.model]):
        parser.error(f"Required fields: {', '.join(FIELDS[args.model])}")
    if args.action in {"update", "remove"} and args.id is None:
        parser.error("--id is required")
    if args.action == "update" and not data:
        parser.error("Provide at least one field to update")
    try:
        with SessionLocal.begin() as session:
            if args.action == "list":
                for item in session.scalars(select(model).order_by(model.id)):
                    print(
                        {
                            column.name: getattr(item, column.name)
                            for column in model.__table__.columns
                        }
                    )
                return
            if args.action == "create":
                item = model(**data)
                session.add(item)
            else:
                item = session.get(model, args.id)
                if item is None:
                    parser.error("Record not found")
                if args.action == "remove":
                    session.delete(item)
                else:
                    for field, value in data.items():
                        setattr(item, field, value)
            session.flush()
            print(f"{args.action}: {args.model} id={item.id}")
    except IntegrityError:
        parser.exit(
            1,
            "Constraint violation: check references, duplicates and dependent records.\n",
        )


if __name__ == "__main__":
    main()
