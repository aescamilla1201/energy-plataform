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
        response = client.get_shadow_properties(
            settings.tuya_device_id
        )
    except TuyaApiError as error:
        print(f"Error de Tuya: {error}")
        raise SystemExit(1) from error
    except Exception as error:
        print(f"Error inesperado: {error}")
        raise SystemExit(1) from error

    print(
        json.dumps(
            response,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()