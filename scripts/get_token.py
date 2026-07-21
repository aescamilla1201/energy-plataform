import json

from src.config import get_settings
from src.tuya_client import TuyaApiError, TuyaClient


def main() -> None:
    settings = get_settings()

    client = TuyaClient(
        client_id=settings.tuya_client_id,
        client_secret=settings.tuya_client_secret,
        base_url=settings.tuya_base_url,
    )

    try:
        response = client.get_token()
    except TuyaApiError as error:
        print(f"Error de Tuya: {error}")
        raise SystemExit(1) from error
    except Exception as error:
        print(f"Error inesperado: {error}")
        raise SystemExit(1) from error

    result = response.get("result", {})

    safe_output = {
        "success": response.get("success"),
        "expire_time": result.get("expire_time"),
        "has_access_token": bool(result.get("access_token")),
        "has_refresh_token": bool(result.get("refresh_token")),
    }

    print(
        json.dumps(
            safe_output,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()