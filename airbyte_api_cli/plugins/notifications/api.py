"""API client for notification endpoints (OSS internal API)."""
from __future__ import annotations
from typing import Any
from airbyte_api_cli.core.client import HttpClient

class NotificationsApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def try_notification(
        self,
        notification_type: str,
        slack_webhook: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"notificationType": notification_type}
        if notification_type == "slack" and slack_webhook:
            body["slackConfiguration"] = {"webhook": slack_webhook}
        return self.client.request("POST", "notifications/try", body=body)
