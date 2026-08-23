"""
MoneyPrinterTurbo Python Client SDK.

Provides a clean Python API to interact with MoneyPrinterTurbo REST server.
"""

from __future__ import annotations

import time
from typing import Any, Dict
import requests


class MoneyPrinterTurboClient:
    """Client for MoneyPrinterTurbo API server."""

    def __init__(self, base_url: str = "http://localhost:8080", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def ping(self) -> str:
        """Check server availability."""
        response = self.session.get(f"{self.base_url}/ping", timeout=10)
        response.raise_for_status()
        return response.text.strip()

    def get_health(self) -> Dict[str, Any]:
        """Fetch deep system health diagnostics."""
        response = self.session.get(f"{self.base_url}/health/deep", timeout=10)
        response.raise_for_status()
        return response.json()

    def generate_video(
        self,
        video_subject: str,
        video_aspect: str = "9:16",
        voice_name: str = "en-US-AvaNeural",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Trigger video generation task.
        Returns response JSON containing task_id.
        """
        payload = {
            "video_subject": video_subject,
            "video_aspect": video_aspect,
            "voice_name": voice_name,
            **kwargs,
        }
        response = self.session.post(
            f"{self.base_url}/v1/video/generate",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Fetch task status and details."""
        response = self.session.get(f"{self.base_url}/v1/tasks/{task_id}", timeout=10)
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self, task_id: str, poll_interval: float = 2.0, timeout: float = 600.0
    ) -> Dict[str, Any]:
        """Poll task until completion or failure."""
        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout:
            res = self.get_task(task_id)
            task_data = res.get("data", {}) if isinstance(res, dict) else {}
            state = task_data.get("state")
            status = task_data.get("status")

            if state == 1 or status in {"completed", "finished"}:
                return res
            if state == 2 or status in {"failed", "error"}:
                raise RuntimeError(f"Task {task_id} failed: {task_data.get('error')}")

            time.sleep(poll_interval)
        raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
