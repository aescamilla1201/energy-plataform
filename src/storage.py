import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def save_json_reading(
    data: dict[str, Any],
    *,
    output_folder: str = "data/normalized",
) -> Path:
    folder = Path(output_folder)
    folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    output_file = folder / f"reading_{timestamp}.json"

    output_file.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output_file

def append_csv_reading(
    reading: dict[str, Any],
    *,
    output_file: str = "data/normalized/readings.csv",
) -> Path:
    """
    Agrega una lectura normalizada al CSV histórico.

    Si el archivo no existe, también crea el encabezado.
    """
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = path.exists()

    with path.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(reading.keys()),
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(reading)

    return path

def flatten_sensor_reading(
    *,
    timestamp: str,
    device_id: str,
    measurements: dict[str, Any],
) -> dict[str, Any]:
    phase_a = measurements.get("phase_a", {})
    phase_b = measurements.get("phase_b", {})
    totals = measurements.get("totals", {})

    return {
        "timestamp": timestamp,
        "device_id": device_id,

        "phase_a_voltage_v": phase_a.get("voltage_v"),
        "phase_a_current_a": phase_a.get("current_a"),
        "phase_a_power_w": phase_a.get("power_w"),
        "phase_a_power_factor": phase_a.get("power_factor"),
        "phase_a_frequency_hz": phase_a.get("frequency_hz"),
        "phase_a_direction": phase_a.get("direction"),
        "phase_a_energy_forward_kwh": phase_a.get(
            "energy_forward_kwh"
        ),
        "phase_a_energy_reverse_kwh": phase_a.get(
            "energy_reverse_kwh"
        ),

        "phase_b_voltage_v": phase_b.get("voltage_v"),
        "phase_b_current_a": phase_b.get("current_a"),
        "phase_b_power_w": phase_b.get("power_w"),
        "phase_b_power_factor": phase_b.get("power_factor"),
        "phase_b_frequency_hz": phase_b.get("frequency_hz"),
        "phase_b_direction": phase_b.get("direction"),
        "phase_b_energy_forward_kwh": phase_b.get(
            "energy_forward_kwh"
        ),
        "phase_b_energy_reverse_kwh": phase_b.get(
            "energy_reverse_kwh"
        ),

        "power_sum_w": totals.get("power_sum_w"),
        "forward_energy_total_kwh": totals.get(
            "energy_forward_kwh"
        ),
        "reverse_energy_total_kwh": totals.get(
            "energy_reverse_kwh"
        ),
    }