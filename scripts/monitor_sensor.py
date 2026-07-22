import argparse
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from src.config import get_settings
from src.normalizers.common import extract_properties
from src.normalizers.registry import normalize_by_type
from src.storage import append_csv_reading, flatten_sensor_reading
from src.tuya_client import TuyaApiError, TuyaClient


LOCAL_TIMEZONE = ZoneInfo("America/Monterrey")


def collect_reading(
    client: TuyaClient,
    device_id: str,
) -> dict:
    raw_response = client.get_shadow_properties(device_id)

    properties = extract_properties(raw_response)
    measurements = normalize_by_type(
        "dual_meter",
        properties,
    )

    timestamp = datetime.now(
        LOCAL_TIMEZONE
    ).isoformat()

    return flatten_sensor_reading(
        timestamp=timestamp,
        device_id=device_id,
        measurements=measurements,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monitorea periódicamente un sensor Tuya."
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help="Intervalo entre lecturas, en segundos. Default: 600.",
    )

    parser.add_argument(
        "--output",
        default="data/normalized/readings.csv",
        help="Ruta del archivo CSV de salida.",
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Realiza una sola lectura y termina.",
    )

    args = parser.parse_args()

    if args.interval < 1:
        raise SystemExit(
            "El intervalo debe ser de al menos 1 segundo."
        )

    settings = get_settings()

    client = TuyaClient(
        client_id=settings.tuya_client_id,
        client_secret=settings.tuya_client_secret,
        base_url=settings.tuya_base_url,
    )

    print("Monitor iniciado")
    print(f"Intervalo: {args.interval} segundos")
    print(f"Archivo: {args.output}")
    print("Presiona Ctrl+C para detenerlo.\n")

    while True:
        started_at = time.monotonic()

        try:
            reading = collect_reading(
                client=client,
                device_id=settings.tuya_device_id,
            )

            output_file = append_csv_reading(
                reading,
                output_file=args.output,
            )

            timestamp = reading["timestamp"]
            power_a = reading.get("phase_a_power_w")
            power_b = reading.get("phase_b_power_w")

            print(
                f"Lectura guardada {timestamp} | "
                f"Fase A: {power_a} W | "
                f"Fase B: {power_b} W | "
                f"{output_file}"
            )

        except TuyaApiError as error:
            print(f"Error de Tuya: {error}")

        except requests.RequestException as error:
            print(f"Error de red: {error}")

        except Exception as error:
            print(f"Error inesperado: {error}")

        if args.once:
            break

        elapsed = time.monotonic() - started_at
        sleep_seconds = max(0, args.interval - elapsed)

        try:
            time.sleep(sleep_seconds)
        except KeyboardInterrupt:
            print("\nMonitor detenido por el usuario.")
            break


if __name__ == "__main__":
    main()