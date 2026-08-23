import os
import shutil
from typing import Any
from fastapi import APIRouter, Request, Response
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
        "ffmpeg": ffmpeg_available,
        "storage_writable": is_storage_writable,
        "disk": disk_info,
    }

