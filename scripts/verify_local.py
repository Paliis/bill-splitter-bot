#!/usr/bin/env python3
"""
Локальна перевірка репозиторію без запуску сервера.
З кореня: python scripts/verify_local.py

Перевіряє: compileall ключових шляхів, імпорт FastAPI-додатку (потрібен PYTHONPATH=.).
Опційно: DATABASE_URL у .env; інакше тимчасовий SQLite у корені (файл *.db у .gitignore).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    os.chdir(ROOT)
    if "PYTHONPATH" not in os.environ:
        os.environ["PYTHONPATH"] = str(ROOT)
    if "DATABASE_URL" not in os.environ:
        # load_dotenv не підключаємо — user може експортувати з .env вручну
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./verify_local.db"

    dirs = ["backend", "handlers", "keyboards", "services"]
    files = ["main.py", "database.py", "models.py", "formatting.py", "middlewares.py", "states.py"]
    for d in dirs:
        p = ROOT / d
        if p.is_dir():
            subprocess.check_call([sys.executable, "-m", "compileall", "-q", str(p)])
    for f in files:
        p = ROOT / f
        if p.is_file():
            subprocess.check_call([sys.executable, "-m", "compileall", "-q", str(p)])

    # Імпорт додатку (не стартує uvicorn)
    from backend.main import app  # noqa: PLC0415

    print("OK:", app.title)
    db = os.environ.get("DATABASE_URL", "")
    print("DATABASE_URL:", db if len(db) <= 72 else db[:72] + "…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
