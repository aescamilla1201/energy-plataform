import json
from dataclasses import dataclass
from pathlib import Path


class DeviceConfigurationError(RuntimeError):
    """Error en el archivo de configuración de dispositivos."""


@dataclass(frozen=True)
class DeviceConfig:
    name: str
    device_id: str
    sensor_type: str
    site: str
    enabled: bool = True


def load_devices(
    config_path: str = "config/devices.json",
) -> list[DeviceConfig]:
    path = Path(config_path)

    if not path.exists():
        raise DeviceConfigurationError(
            f"No existe el archivo de dispositivos: {path}"
        )

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise DeviceConfigurationError(
            f"El archivo {path} no contiene JSON válido: {error}"
        ) from error

    raw_devices = payload.get("devices")

    if not isinstance(raw_devices, list):
        raise DeviceConfigurationError(
            "La configuración debe contener una lista 'devices'."
        )

    devices: list[DeviceConfig] = []

    for index, item in enumerate(raw_devices):
        if not isinstance(item, dict):
            raise DeviceConfigurationError(
                f"El dispositivo en posición {index} no es válido."
            )

        required_fields = [
            "name",
            "device_id",
            "sensor_type",
            "site",
        ]

        missing_fields = [
            field
            for field in required_fields
            if not item.get(field)
        ]

        if missing_fields:
            raise DeviceConfigurationError(
                f"Dispositivo {index}: faltan campos "
                + ", ".join(missing_fields)
            )

        devices.append(
            DeviceConfig(
                name=str(item["name"]),
                device_id=str(item["device_id"]),
                sensor_type=str(item["sensor_type"]),
                site=str(item["site"]),
                enabled=bool(item.get("enabled", True)),
            )
        )

    return devices