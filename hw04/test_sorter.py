"""Test nested traversal, duplicate preservation and extension grouping."""

import asyncio

from anyio import Path as AsyncPath

from main import read_folder


def test_nested_files_and_collisions(tmp_path):
    source, output = tmp_path / "source", tmp_path / "output"
    (source / "nested").mkdir(parents=True)
    (source / "a.TXT").write_text("first", encoding="utf-8")
    (source / "nested" / "a.TXT").write_text("second", encoding="utf-8")
    (source / "README").write_text("no extension", encoding="utf-8")
    (source / "empty.bin").write_bytes(b"")
    assert (
        asyncio.run(read_folder(AsyncPath(source), AsyncPath(output), workers=2)) == 0
    )
    assert {path.read_text() for path in (output / "txt").iterdir()} == {
        "first",
        "second",
    }
    assert (output / "no_extension" / "README").read_text() == "no extension"
    assert (output / "bin" / "empty.bin").read_bytes() == b""
    assert len(list(source.rglob("*"))) == 5
