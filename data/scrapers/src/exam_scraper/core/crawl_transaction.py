from __future__ import annotations

import shutil
from pathlib import Path

import aiosqlite


class CrawlTransaction:
    def __init__(self, db: aiosqlite.Connection, temp_dir: Path):
        self._db = db
        self.temp_dir = temp_dir
        self._moved_files: list[Path] = []

    async def begin(self) -> None:
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        await self._db.execute("BEGIN")

    def build_temp_path(self, filename: str) -> Path:
        return self.temp_dir / f"{filename}.part"

    def register_final_file(self, path: Path) -> None:
        self._moved_files.append(path)

    async def commit(self) -> None:
        await self._db.commit()
        self._cleanup_temp()

    async def rollback(self) -> None:
        await self._db.rollback()
        for path in self._moved_files:
            path.unlink(missing_ok=True)
        self._cleanup_temp()

    def _cleanup_temp(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
