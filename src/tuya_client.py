import hashlib
import hmac
import time
from typing import Any

import requests


class TuyaApiError(RuntimeError):
    """Error devuelto por Tuya o por la comunicación HTTP."""


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
        self.token_expires_at: float = 0

    @staticmethod
    def _timestamp_ms() -> str:
        return str(int(time.time() * 1000))

    @staticmethod
    def _sha256(value: str) -> str:
        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()

    def _sign(
        self,
        *,
        timestamp: str,
        method: str,
        request_path: str,
        access_token: str = "",
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
            + access_token
            + timestamp
            + string_to_sign
        )

        return hmac.new(
            self.client_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest().upper()

    @staticmethod
    def _parse_response(
        response: requests.Response,
    ) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as error:
            raise TuyaApiError(
                "Tuya devolvió una respuesta no válida: "
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

        return payload

    def get_token(self) -> dict[str, Any]:
        timestamp = self._timestamp_ms()
        request_path = "/v1.0/token?grant_type=1"

        signature = self._sign(
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

        payload = self._parse_response(response)

        result = payload.get("result", {})
        access_token = result.get("access_token")
        expire_time = int(result.get("expire_time", 0))

        if not access_token:
            raise TuyaApiError(
                f"Tuya no devolvió access_token: {payload}"
            )

        self.access_token = access_token
        self.token_expires_at = time.time() + expire_time - 30

        return payload

    def _ensure_token(self) -> None:
        token_is_valid = (
            self.access_token is not None
            and time.time() < self.token_expires_at
        )

        if not token_is_valid:
            self.get_token()

    def get(
        self,
        request_path: str,
    ) -> dict[str, Any]:
        self._ensure_token()

        timestamp = self._timestamp_ms()

        signature = self._sign(
            timestamp=timestamp,
            method="GET",
            request_path=request_path,
            access_token=self.access_token or "",
        )

        headers = {
            "client_id": self.client_id,
            "access_token": self.access_token or "",
            "sign": signature,
            "sign_method": "HMAC-SHA256",
            "t": timestamp,
            "lang": "en",
        }

        response = self.session.get(
            f"{self.base_url}{request_path}",
            headers=headers,
            timeout=self.timeout_seconds,
        )

        return self._parse_response(response)

    def get_device_details(
        self,
        device_id: str,
    ) -> dict[str, Any]:
        return self.get(
            f"/v1.0/devices/{device_id}"
        )

    def get_shadow_properties(
        self,
        device_id: str,
    ) -> dict[str, Any]:
        return self.get(
            f"/v2.0/cloud/thing/{device_id}/shadow/properties"
        )