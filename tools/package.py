"""Create independent homework archives without local secrets or runtime data."""

import argparse
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Full name for LMS archive names")
    args = parser.parse_args()
    if (
        any(character in args.name for character in '/\\:*?"<>|')
        or not args.name.strip()
    ):
        parser.error("Name contains invalid filename characters")
    root = Path(__file__).resolve().parents[1]
    output = root / "dist"
    output.mkdir(exist_ok=True)
    excluded = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "htmlcov",
        "_build",
    }
    for folder in sorted(root.glob("hw[0-9][0-9]")):
        archive = output / f"ДЗ{int(folder.name[2:])}_{args.name}.zip"
        with ZipFile(archive, "w", ZIP_DEFLATED) as zipped:
            for path in sorted(folder.rglob("*")):
                relative = path.relative_to(folder)
                if not path.is_file() or excluded.intersection(relative.parts):
                    continue
                if (
                    path.name == ".env"
                    or path.name.startswith(".coverage")
                    or path.suffix in {".db", ".log", ".pyc"}
                ):
                    continue
                if (
                    folder.name == "hw03"
                    and relative.parts[0] == "storage"
                    and path.suffix == ".json"
                ):
                    continue
                zipped.write(path, relative.as_posix())
        print(archive)


if __name__ == "__main__":
    main()
