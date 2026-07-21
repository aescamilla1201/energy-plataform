import hashlib
import hmac
import time
from typing import Any

import requests


class TuyaApiError(RuntimeError):
    pass


class TuyaClient:
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        base_url: str,
        timeout_seconds: int = 15,
    ) -> None:
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

        self.session = requests.Session()
        self.access_token: str | None = None

    @staticmethod
    def _timestamp_ms() -> str:
        return str(int(time.time() * 1000))

    @staticmethod
    def _sha256(value: str) -> str:
        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()

    def _create_token_signature(
        self,
        *,
        timestamp: str,
        method: str,
        request_path: str,
        body: str = "",
    ) -> str:
        content_hash = self._sha256(body)

        string_to_sign = "\n".join(
            [
                method.upper(),
                content_hash,
                "",
                request_path,
            ]
        )

        message = (
            self.client_id
            + timestamp
            + string_to_sign
        )

        return hmac.new(
            self.client_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest().upper()

    def get_token(self) -> dict[str, Any]:
        timestamp = self._timestamp_ms()

        request_path = "/v1.0/token?grant_type=1"

        signature = self._create_token_signature(
            timestamp=timestamp,
            method="GET",
            request_path=request_path,
        )

        headers = {
            "client_id": self.client_id,
            "sign": signature,
            "sign_method": "HMAC-SHA256",
            "t": timestamp,
            "lang": "en",
        }

        response = self.session.get(
            f"{self.base_url}/v1.0/token",
            params={"grant_type": 1},
            headers=headers,
            timeout=self.timeout_seconds,
        )

        try:
            payload = response.json()
        except ValueError as error:
            raise TuyaApiError(
                f"Tuya devolvió una respuesta inválida: "
                f"HTTP {response.status_code}"
            ) from error

        if not response.ok:
            raise TuyaApiError(
                f"Error HTTP {response.status_code}: {payload}"
            )

        if not payload.get("success"):
            raise TuyaApiError(
                f"Tuya rechazó la solicitud: {payload}"
            )

        result = payload.get("result", {})
        access_token = result.get("access_token")

        if not access_token:
            raise TuyaApiError(
                f"Tuya no devolvió access_token: {payload}"
            )

        self.access_token = access_token

        return payload