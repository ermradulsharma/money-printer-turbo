import os
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import PlainTextResponse

from app.services import state as sm
from app.utils import utils

router = APIRouter()


@router.get(
    "/ping",
    tags=["Health Check"],
    description="检查服务可用性",
    response_description="pong",
)
def ping(request: Request) -> str:
    return "pong"


@router.get(
    "/health/deep",
    tags=["Health Check"],
    description="Deep diagnostic health check for system dependencies, storage, and status",
)
def deep_health_check(request: Request, response: Response) -> dict[str, Any]:
    storage_path = utils.storage_dir()
    is_storage_writable = os.access(storage_path, os.W_OK)

    ffmpeg_available = True
    try:
        utils.check_ffmpeg()
    except Exception:
        ffmpeg_available = False

    disk_info = {}
    try:
        total, used, free = shutil.disk_usage(storage_path)
        disk_info = {
            "total_gb": round(total / (1024 ** 3), 2),
            "free_gb": round(free / (1024 ** 3), 2),
            "used_percent": round((used / total) * 100, 1),
        }
    except Exception:
        pass

    status = "healthy" if (is_storage_writable and ffmpeg_available) else "degraded"
    if status == "degraded":
        response.status_code = 503

    return {
        "status": status,
        "storage_writable": is_storage_writable,
        "ffmpeg_available": ffmpeg_available,
        "disk": disk_info,
    }


@router.get(
    "/metrics",
    tags=["Metrics"],
    description="Prometheus text metrics export",
    response_class=PlainTextResponse,
)
def prometheus_metrics(request: Request) -> str:
    ffmpeg_val = 1
    try:
        utils.check_ffmpeg()
    except Exception:
        ffmpeg_val = 0

    storage_bytes = 0
    try:
        storage_path = Path(utils.storage_dir())
        if storage_path.exists():
            storage_bytes = sum(
                f.stat().st_size for f in storage_path.rglob("*") if f.is_file()
            )
    except Exception:
        pass

    tasks, total_tasks = sm.state.get_all_tasks(1, 1000)
    completed_tasks = sum(
        1 for t in tasks if t.get("state") == 1 or t.get("status") == "completed"
    )
    failed_tasks = sum(
        1 for t in tasks if t.get("state") == 2 or t.get("status") == "failed"
    )
    running_tasks = sum(
        1 for t in tasks if t.get("state") == 0 or t.get("status") in {"processing", "running"}
    )

    metrics = [
        "# HELP mpt_ffmpeg_available Indicates if FFmpeg binary is accessible (1) or missing (0).",
        "# TYPE mpt_ffmpeg_available gauge",
        f"mpt_ffmpeg_available {ffmpeg_val}",
        "# HELP mpt_storage_bytes_used Total storage directory usage in bytes.",
        "# TYPE mpt_storage_bytes_used gauge",
        f"mpt_storage_bytes_used {storage_bytes}",
        "# HELP mpt_tasks_total Total count of tracked video generation tasks.",
        "# TYPE mpt_tasks_total counter",
        f"mpt_tasks_total {total_tasks}",
        "# HELP mpt_tasks_by_status Breakdown of video generation tasks by status.",
        "# TYPE mpt_tasks_by_status gauge",
        f'mpt_tasks_by_status{{status="completed"}} {completed_tasks}',
        f'mpt_tasks_by_status{{status="failed"}} {failed_tasks}',
        f'mpt_tasks_by_status{{status="running"}} {running_tasks}',
    ]
    return "\n".join(metrics) + "\n"


