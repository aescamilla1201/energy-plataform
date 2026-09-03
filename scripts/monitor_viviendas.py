import argparse
import csv
import json
import time
import unicodedata
from datetime import datetime
from pathlib import Path
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
from src.storage import flatten_sensor_reading
from src.tuya_client import TuyaApiError, TuyaClient


LOCAL_TIMEZONE = ZoneInfo("America/Monterrey")

VIVIENDAS_FILE = Path("config/viviendas.json")
OUTPUT_DIRECTORY = Path("data/viviendas")


def load_viviendas() -> dict:
    """Carga y valida la configuración de viviendas."""

    if not VIVIENDAS_FILE.exists():
        raise SystemExit(
            f"No se encontró el archivo {VIVIENDAS_FILE}"
        )

    try:
        with VIVIENDAS_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise SystemExit(
            f"Error de JSON en {VIVIENDAS_FILE}: {error}"
        ) from error

    viviendas = data.get("viviendas")

    if not isinstance(viviendas, dict):
        raise SystemExit(
            'El archivo viviendas.json debe contener '
            'una propiedad "viviendas".'
        )

    return viviendas


def safe_filename(name: str) -> str:
    """
    Convierte un nombre en un nombre de archivo seguro.

    Ejemplo:
        Vivienda José Ignacio
        ->
        Vivienda_Jose_Ignacio
    """

    normalized = unicodedata.normalize(
        "NFKD",
        name,
    )

    without_accents = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    result = []

    for character in without_accents:
        if character.isalnum():
            result.append(character)
        elif character in ("-", "_"):
            result.append(character)
        else:
            result.append("_")

    filename = "".join(result)

    while "__" in filename:
        filename = filename.replace(
            "__",
            "_",
        )

    return filename.strip("_")


def collect_device_reading(
    *,
    client: TuyaClient,
    device: DeviceConfig,
    timestamp: str,
) -> dict:
    """Obtiene y normaliza una lectura de un dispositivo."""

    raw_response = client.get_shadow_properties(
        device.device_id
    )

    properties = extract_properties(
        raw_response
    )

    measurements = normalize_by_type(
        device.sensor_type,
        properties,
    )

    reading = flatten_sensor_reading(
        timestamp=timestamp,
        device_id=device.device_id,
        measurements=measurements,
    )

    reading["device_name"] = device.name
    reading["sensor_type"] = device.sensor_type

    return reading


def add_device_reading_to_vivienda(
    *,
    vivienda_reading: dict,
    device_reading: dict,
    device_code: str,
) -> None:
    """
    Agrega una lectura de dispositivo a la fila de la vivienda.

    Las columnas propias del dispositivo se prefijan con su código.

    Ejemplo:
        EM-001_phase_a_power_w
        EM-001_phase_b_power_w
    """

    ignored_fields = {
        "timestamp",
        "device_id",
        "device_name",
        "sensor_type",
    }

    for key, value in device_reading.items():

        if key in ignored_fields:
            continue

        column_name = f"{device_code}_{key}"

        vivienda_reading[column_name] = value


def calculate_vivienda_totals(
    vivienda_reading: dict,
) -> None:
    """
    Calcula la potencia total de la vivienda.

    Suma únicamente campos que terminan en _power_w.

    Los campos faltantes por un dispositivo que falló
    simplemente no participan en la suma.
    """

    total_power_w = 0.0
    found_power = False

    for key, value in vivienda_reading.items():

        if not key.endswith("_power_w"):
            continue

        if not isinstance(
            value,
            (int, float),
        ):
            continue

        total_power_w += value
        found_power = True

    if found_power:
        vivienda_reading[
            "total_power_w"
        ] = total_power_w


def save_vivienda_reading(
    reading: dict,
    *,
    output_file: Path,
) -> None:
    """Agrega una fila al CSV de la vivienda."""

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_exists = output_file.exists()

    fieldnames = list(
        reading.keys()
    )

    with output_file.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(reading)


def collect_vivienda_reading(
    *,
    client: TuyaClient,
    vivienda_name: str,
    vivienda_config: dict,
    devices_by_name: dict[str, DeviceConfig],
) -> dict:
    """Obtiene las lecturas de todos los dispositivos de una vivienda."""

    timestamp = datetime.now(
        LOCAL_TIMEZONE
    ).isoformat()

    ubicacion = vivienda_config.get(
        "ubicacion",
        {},
    )

    vivienda_code = vivienda_config.get(
        "codigo",
        vivienda_name,
    )

    vivienda_reading = {
        "timestamp": timestamp,
        "vivienda": vivienda_name,
        "codigo_vivienda": vivienda_code,
        "latitud": ubicacion.get(
            "latitud"
        ),
        "longitud": ubicacion.get(
            "longitud"
        ),
    }

    sensores = vivienda_config.get(
        "sensores",
        [],
    )

    if not isinstance(
        sensores,
        list,
    ):
        print(
            f"ADVERTENCIA {vivienda_name}: "
            '"sensores" debe ser una lista.'
        )

        return vivienda_reading

    successful_devices = 0

    for sensor in sensores:

        if not isinstance(
            sensor,
            dict,
        ):
            print(
                f"ADVERTENCIA {vivienda_name}: "
                "entrada de sensor inválida."
            )
            continue

        device_code = sensor.get(
            "codigo"
        )

        if not device_code:
            print(
                f"ADVERTENCIA {vivienda_name}: "
                "sensor sin código."
            )
            continue

        device = devices_by_name.get(
            device_code
        )

        if device is None:
            print(
                f"ADVERTENCIA {vivienda_name}: "
                f"{device_code} no existe "
                "en devices.json."
            )
            continue

        if not device.enabled:
            print(
                f"ADVERTENCIA {vivienda_name}: "
                f"{device_code} está deshabilitado."
            )
            continue

        try:
            device_reading = collect_device_reading(
                client=client,
                device=device,
                timestamp=timestamp,
            )

        except TuyaApiError as error:
            print(
                f"ERROR Tuya | "
                f"{vivienda_name} | "
                f"{device_code} | "
                f"{error}"
            )
            continue

        except requests.RequestException as error:
            print(
                f"ERROR RED | "
                f"{vivienda_name} | "
                f"{device_code} | "
                f"{error}"
            )
            continue

        except Exception as error:
            print(
                f"ERROR INESPERADO | "
                f"{vivienda_name} | "
                f"{device_code} | "
                f"{error}"
            )
            continue

        add_device_reading_to_vivienda(
            vivienda_reading=vivienda_reading,
            device_reading=device_reading,
            device_code=device_code,
        )

        successful_devices += 1

    vivienda_reading[
        "dispositivos_ok"
    ] = successful_devices

    vivienda_reading[
        "dispositivos_configurados"
    ] = len(sensores)

    calculate_vivienda_totals(
        vivienda_reading
    )

    return vivienda_reading


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Monitorea viviendas y agrupa "
            "las lecturas de sus dispositivos Tuya."
        )
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help=(
            "Intervalo entre rondas en segundos. "
            "Por defecto: 600."
        ),
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
        print(
            f"Error de configuración: {error}"
        )
        raise SystemExit(1) from error

    viviendas = load_viviendas()

    devices_by_name = {
        device.name: device
        for device in configured_devices
    }

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    client = TuyaClient(
        client_id=settings.tuya_client_id,
        client_secret=settings.tuya_client_secret,
        base_url=settings.tuya_base_url,
    )

    enabled_viviendas = {
        name: config
        for name, config in viviendas.items()
        if config.get(
            "enabled",
            True,
        )
    }

    if not enabled_viviendas:
        raise SystemExit(
            "No hay viviendas habilitadas."
        )

    print(
        f"Viviendas habilitadas: "
        f"{len(enabled_viviendas)}"
    )

    print(
        f"Dispositivos configurados: "
        f"{len(configured_devices)}"
    )

    print(
        f"Intervalo entre rondas: "
        f"{args.interval} segundos"
    )

    print(
        "Presiona Ctrl+C para "
        "detener el monitor.\n"
    )

    try:
        while True:

            round_started_at = (
                time.monotonic()
            )

            for (
                vivienda_name,
                vivienda_config,
            ) in enabled_viviendas.items():

                reading = collect_vivienda_reading(
                    client=client,
                    vivienda_name=vivienda_name,
                    vivienda_config=vivienda_config,
                    devices_by_name=devices_by_name,
                )

                vivienda_code = vivienda_config.get(
                    "codigo",
                    vivienda_name,
                )

                filename = (
                    safe_filename(
                        vivienda_code
                    )
                    + ".csv"
                )

                output_file = (
                    OUTPUT_DIRECTORY
                    / filename
                )

                save_vivienda_reading(
                    reading,
                    output_file=output_file,
                )

                total_power = reading.get(
                    "total_power_w"
                )

                print(
                    f"OK {vivienda_code} | "
                    f"{vivienda_name} | "
                    f"{reading['timestamp']} | "
                    f"dispositivos "
                    f"{reading['dispositivos_ok']}/"
                    f"{reading['dispositivos_configurados']} | "
                    f"potencia total="
                    f"{total_power} W | "
                    f"{output_file}"
                )

            if args.once:
                break

            elapsed = (
                time.monotonic()
                - round_started_at
            )

            sleep_seconds = max(
                0,
                args.interval - elapsed,
            )

            time.sleep(
                sleep_seconds
            )

    except KeyboardInterrupt:
        print(
            "\nMonitor detenido "
            "por el usuario."
        )


if __name__ == "__main__":
    main()
