"""Copy files concurrently into extension directories without overwriting."""

import argparse
import asyncio
import logging
from pathlib import Path

import aiofiles
from anyio import Path as AsyncPath

LOG = logging.getLogger(__name__)


async def copy_file(source, output):
    """Stream one file; reserve a unique target using exclusive creation."""
    target = None
    try:
        folder = output / (source.suffix.lower().lstrip(".") or "no_extension")
        await folder.mkdir(parents=True, exist_ok=True)
        number = 0
        while True:
            name = (
                source.name if number == 0 else f"{source.stem}_{number}{source.suffix}"
            )
            candidate = folder / name
            try:
                destination = await aiofiles.open(candidate, "xb")
                target = candidate
                break
            except FileExistsError:
                number += 1
        try:
            async with aiofiles.open(source, "rb") as incoming:
                while chunk := await incoming.read(1024 * 1024):
                    await destination.write(chunk)
        finally:
            await destination.close()
        return True
    except OSError:
        LOG.exception("Cannot copy %s", source)
        if target is not None:
            try:
                await target.unlink(missing_ok=True)
            except OSError:
                LOG.exception("Cannot remove incomplete copy %s", target)
        return False


async def read_folder(source, output, workers=8):
    """Traverse asynchronously with a bounded queue and fixed worker pool."""
    queue = asyncio.Queue(maxsize=workers * 2)
    failures = 0

    async def worker():
        nonlocal failures
        while True:
            item = await queue.get()
            try:
                if item is None:
                    return
                if not await copy_file(item, output):
                    failures += 1
            finally:
                queue.task_done()

    async def walk(folder):
        nonlocal failures
        try:
            async for path in folder.iterdir():
                if await path.is_symlink():
                    LOG.warning("Skipping symbolic link: %s", path)
                elif await path.is_dir():
                    await walk(path)
                elif await path.is_file():
                    await queue.put(path)
        except OSError:
            failures += 1
            LOG.exception("Cannot read directory %s", folder)

    tasks = [asyncio.create_task(worker()) for _ in range(workers)]
    try:
        await walk(source)
        await queue.join()
    finally:
        for _ in tasks:
            await queue.put(None)
        await asyncio.gather(*tasks)
    return failures


def main():
    """Validate command-line paths and run the asynchronous sorter."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    source, output = args.source.resolve(), args.output.resolve()
    if not source.is_dir():
        parser.error("Source must be an existing directory")
    if source == output or source in output.parents or output in source.parents:
        parser.error("Source and output directories must not overlap")
    if not 1 <= args.workers <= 128:
        parser.error("Workers must be between 1 and 128")
    return bool(
        asyncio.run(read_folder(AsyncPath(source), AsyncPath(output), args.workers))
    )


if __name__ == "__main__":
    raise SystemExit(main())
