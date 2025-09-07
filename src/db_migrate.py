"""Utility to run Alembic migrations inside the running container.

Usage (inside pod):
    python -m src.db_migrate upgrade head
    python -m src.db_migrate downgrade -1
If no args are supplied it defaults to: upgrade head
"""

from __future__ import annotations
import sys
import logging
from pathlib import Path
from alembic import command
from alembic.config import Config

log = logging.getLogger("db_migrate")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

DEFAULT_CMD = ("upgrade", "head")


def get_alembic_config() -> Config:
    # Expect alembic.ini to be at /app/alembic.ini (WORKDIR /app)
    ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    if not ini_path.exists():  # fallback if layout differs
        ini_path = Path("alembic.ini")
    cfg = Config(str(ini_path))
    return cfg


def main(argv: list[str]) -> int:
    if len(argv) == 0:
        action, rev = DEFAULT_CMD
    elif len(argv) == 1:
        action, rev = argv[0], "head"
    else:
        action, rev = argv[0], argv[1]

    cfg = get_alembic_config()

    log.info("Running Alembic command: %s %s", action, rev)
    try:
        if action == "upgrade":
            command.upgrade(cfg, rev)
        elif action == "downgrade":
            command.downgrade(cfg, rev)
        elif action == "stamp":
            command.stamp(cfg, rev)
        elif action == "history":
            command.history(cfg)
        elif action == "current":
            command.current(cfg)
        else:
            log.error("Unsupported action: %s", action)
            return 2
    except Exception as exc:  # noqa: BLE001
        log.exception("Migration failed: %s", exc)
        return 1
    log.info("Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
