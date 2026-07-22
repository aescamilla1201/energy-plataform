import json

from src.config import get_settings
from src.normalizers.common import extract_properties
from src.normalizers.registry import normalize_by_type
from src.tuya_client import TuyaApiError, TuyaClient


def main() -> None:
    settings = get_settings()

    client = TuyaClient(
        client_id=settings.tuya_client_id,
        client_secret=settings.tuya_client_secret,
        base_url=settings.tuya_base_url,
    )

    try:
        raw_response = client.get_shadow_properties(
            settings.tuya_device_id
        )
    except TuyaApiError as error:
        print(f"Error de Tuya: {error}")
        raise SystemExit(1) from error

    properties = extract_properties(raw_response)
    normalized = normalize_by_type(
        "dual_meter",
        properties,
    )

    print(
        json.dumps(
            normalized,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()