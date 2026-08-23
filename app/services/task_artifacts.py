"""Safe read and write operations for task directory artifacts."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from loguru import logger

from app.utils import utils


def _script_file(task_id: str) -> Path:
    """Return task script path using unified task directory logic."""
    return Path(utils.task_dir(task_id)) / "script.json"


def _write_json_atomic(target: Path, payload: Mapping[str, Any]) -> None:
    """
    Atomically write JSON payload within the target directory to avoid partial writes.
    """
    temp_path: Path | None = None
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(
                payload,
                temp_file,
                ensure_ascii=False,
                indent=4,
                default=lambda value: value.__dict__,
            )
            temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temp_path, target)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def write_script_data(task_id: str, payload: Mapping[str, Any]) -> None:
    """Create or overwrite task script.json manifest."""
    _write_json_atomic(_script_file(task_id), payload)


def patch_script_data(task_id: str, **updates: Any) -> bool:
    """
    Update task script data while preserving existing fields, returning False on failure.
    """
    try:
        target = _script_file(task_id)
        with target.open("r", encoding="utf-8") as script_file:
            payload = json.load(script_file)
        if not isinstance(payload, dict):
            raise ValueError("task script data must be a JSON object")

        payload.update(updates)
        _write_json_atomic(target, payload)
        return True
    except FileNotFoundError:
        logger.debug(
            f"skip task script update because script.json does not exist: "
            f"task_id={task_id}"
        )
        return False
    except Exception as exc:
        logger.warning(
            "failed to update task script data: "
            f"task_id={task_id}, fields={sorted(updates)}, "
            f"error={type(exc).__name__}, detail={exc}"
        )
        return False


def clean_expired_task_artifacts(max_age_hours: int = 24) -> int:
    """Clean task artifacts and temporary rendering files older than ``max_age_hours``.

    Returns the count of deleted expired task directories.
    """
    import time
    import shutil

    task_root = Path(utils.task_dir())
    if not task_root.exists():
        return 0

    cutoff_time = time.time() - (max_age_hours * 3600)
    deleted_count = 0

    for task_dir in task_root.iterdir():
        if task_dir.is_dir():
            try:
                if task_dir.stat().st_mtime < cutoff_time:
                    shutil.rmtree(task_dir, ignore_errors=True)
                    deleted_count += 1
            except Exception as exc:
                logger.warning(f"failed to clean expired task dir {task_dir}: {exc}")

    if deleted_count > 0:
        logger.info(
            f"cleaned {deleted_count} expired task artifact directories older than {max_age_hours}h"
        )

    return deleted_count
