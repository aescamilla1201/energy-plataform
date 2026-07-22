from datetime import datetime
from zoneinfo import ZoneInfo

from src.config import get_settings
from src.normalizers.common import extract_properties
from src.normalizers.registry import normalize_by_type
from src.storage import append_csv_reading, flatten_sensor_reading
from src.tuya_client import TuyaApiError, TuyaClient


LOCAL_TIMEZONE = ZoneInfo("America/Monterrey")


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
    measurements = normalize_by_type(
        "dual_meter",
        properties,
    )

    timestamp = datetime.now(
        LOCAL_TIMEZONE
    ).isoformat()

    csv_reading = flatten_sensor_reading(
        timestamp=timestamp,
        device_id=settings.tuya_device_id,
        measurements=measurements,
    )

    output_file = append_csv_reading(csv_reading)

    print("Lectura agregada al CSV")
    print(f"Archivo: {output_file}")


if __name__ == "__main__":
    main()