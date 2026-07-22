import argparse
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from src.config import get_settings
from src.devices import (
    DeviceConfig,
    DeviceConfigurationError,
    load_devices,
)
from src.normalizers.common import extract_properties
from src.normalizers.registry import normalize_by_type
from src.storage import append_csv_reading, flatten_sensor_reading
from src.tuya_client import TuyaApiError, TuyaClient


LOCAL_TIMEZONE = ZoneInfo("America/Monterrey")


def collect_device_reading(
    *,
    client: TuyaClient,
    device: DeviceConfig,
) -> dict:
    raw_response = client.get_shadow_properties(
        device.device_id
    )

    properties = extract_properties(raw_response)

    measurements = normalize_by_type(
        device.sensor_type,
        properties,
    )

    timestamp = datetime.now(
        LOCAL_TIMEZONE
    ).isoformat()

    reading = flatten_sensor_reading(
        timestamp=timestamp,
        device_id=device.device_id,
        measurements=measurements,
    )

    reading["device_name"] = device.name
    reading["site"] = device.site
    reading["sensor_type"] = device.sensor_type

    return reading


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monitorea varios sensores Tuya."
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help="Intervalo entre rondas en segundos.",
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Ejecuta una sola ronda.",
    )

    args = parser.parse_args()

    if args.interval < 1:
        raise SystemExit(
            "El intervalo debe ser mayor o igual a 1."
        )

    settings = get_settings()

    try:
        configured_devices = load_devices()
    except DeviceConfigurationError as error:
        print(f"Error de configuración: {error}")
        raise SystemExit(1) from error

    devices = [
        device
        for device in configured_devices
        if device.enabled
    ]

    if not devices:
        raise SystemExit(
            "No hay dispositivos habilitados."
        )

    client = TuyaClient(
        client_id=settings.tuya_client_id,
        client_secret=settings.tuya_client_secret,
        base_url=settings.tuya_base_url,
    )

    print(f"Dispositivos habilitados: {len(devices)}")
    print(f"Intervalo entre rondas: {args.interval} segundos")
    print("Presiona Ctrl+C para detener el monitor.\n")

    try:
        while True:
            round_started_at = time.monotonic()

            for device in devices:
                try:
                    reading = collect_device_reading(
                        client=client,
                        device=device,
                    )

                    output_file = (
                        f"data/normalized/"
                        f"{device.name}_readings.csv"
                    )

                    saved_path = append_csv_reading(
                        reading,
                        output_file=output_file,
                    )

                    print(
                        f"OK {device.name} | "
                        f"{reading['timestamp']} | "
                        f"A={reading.get('phase_a_power_w')} W | "
                        f"B={reading.get('phase_b_power_w')} W | "
                        f"{saved_path}"
                    )

                except TuyaApiError as error:
                    print(
                        f"Error Tuya en {device.name}: {error}"
                    )

                except requests.RequestException as error:
                    print(
                        f"Error de red en {device.name}: {error}"
                    )

                except Exception as error:
                    print(
                        f"Error inesperado en {device.name}: {error}"
                    )

            if args.once:
                break

            elapsed = time.monotonic() - round_started_at
            sleep_seconds = max(
                0,
                args.interval - elapsed,
            )

            time.sleep(sleep_seconds)

    except KeyboardInterrupt:
        print("\nMonitor detenido por el usuario.")


if __name__ == "__main__":
    main()