from unittest.mock import MagicMock, patch
from sdk.money_printer_turbo import MoneyPrinterTurboClient


def test_sdk_client_ping():
    with patch("requests.Session.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "pong"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = MoneyPrinterTurboClient(base_url="http://localhost:8080")
        res = client.ping()
        assert res == "pong"


def test_sdk_client_generate_video():
    with patch("requests.Session.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 200, "data": {"task_id": "test-123"}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = MoneyPrinterTurboClient(base_url="http://localhost:8080")
        res = client.generate_video(video_subject="AI Future")
        assert res["data"]["task_id"] == "test-123"
