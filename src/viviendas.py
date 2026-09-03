import json
from dataclasses import dataclass
from pathlib import Path


class ViviendaConfigurationError(RuntimeError):
    """Error en el archivo de configuración de viviendas."""


@dataclass(frozen=True)
class ViviendaConfig:
    name: str
    codigo: str
    enabled: bool
    sensores: tuple[str, ...]
    latitude: float
    longitude: float


def load_viviendas(
    config_path: str = "config/viviendas.json",
) -> dict[str, ViviendaConfig]:

    path = Path(config_path)

    if not path.exists():
        raise ViviendaConfigurationError(
            f"No existe el archivo de viviendas: {path}"
        )

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise ViviendaConfigurationError(
            f"El archivo {path} no contiene JSON válido: {error}"
        ) from error

    raw_viviendas = payload.get("viviendas")

    if not isinstance(raw_viviendas, dict):
        raise ViviendaConfigurationError(
            "La configuración debe contener un objeto 'viviendas'."
        )

    viviendas: dict[str, ViviendaConfig] = {}

    for vivienda_name, item in raw_viviendas.items():

        if not isinstance(item, dict):
            raise ViviendaConfigurationError(
                f"La vivienda '{vivienda_name}' no es válida."
            )

        required_fields = [
            "codigo",
            "enabled",
            "ubicacion",
            "sensores",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in item
        ]

        if missing_fields:
            raise ViviendaConfigurationError(
                f"Vivienda '{vivienda_name}': faltan campos "
                + ", ".join(missing_fields)
            )

        codigo = item["codigo"]

        if not isinstance(codigo, str) or not codigo.strip():
            raise ViviendaConfigurationError(
                f"Vivienda '{vivienda_name}': "
                "'codigo' debe ser un texto no vacío."
            )

        enabled = item["enabled"]

        if not isinstance(enabled, bool):
            raise ViviendaConfigurationError(
                f"Vivienda '{vivienda_name}': "
                "'enabled' debe ser true o false."
            )

        ubicacion = item["ubicacion"]

        if not isinstance(ubicacion, dict):
            raise ViviendaConfigurationError(
                f"Vivienda '{vivienda_name}': "
                "'ubicacion' debe ser un objeto."
            )

        if "latitud" not in ubicacion:
            raise ViviendaConfigurationError(
                f"Vivienda '{vivienda_name}': "
                "falta 'ubicacion.latitud'."
            )

        if "longitud" not in ubicacion:
            raise ViviendaConfigurationError(
                f"Vivienda '{vivienda_name}': "
                "falta 'ubicacion.longitud'."
            )

        try:
            latitude = float(ubicacion["latitud"])
            longitude = float(ubicacion["longitud"])
        except (TypeError, ValueError) as error:
            raise ViviendaConfigurationError(
                f"Vivienda '{vivienda_name}': "
                "latitud y longitud deben ser números."
            ) from error

        if not -90 <= latitude <= 90:
            raise ViviendaConfigurationError(
                f"Vivienda '{vivienda_name}': "
                f"latitud fuera de rango: {latitude}"
            )

        if not -180 <= longitude <= 180:
            raise ViviendaConfigurationError(
                f"Vivienda '{vivienda_name}': "
                f"longitud fuera de rango: {longitude}"
            )

        raw_sensores = item["sensores"]

        if not isinstance(raw_sensores, list) or not raw_sensores:
            raise ViviendaConfigurationError(
                f"Vivienda '{vivienda_name}': "
                "'sensores' debe ser una lista no vacía."
            )

        sensores: list[str] = []

        for index, sensor in enumerate(raw_sensores):

            if not isinstance(sensor, dict):
                raise ViviendaConfigurationError(
                    f"Vivienda '{vivienda_name}': "
                    f"sensor {index} no es válido."
                )

            sensor_codigo = sensor.get("codigo")

            if not isinstance(sensor_codigo, str):
                raise ViviendaConfigurationError(
                    f"Vivienda '{vivienda_name}': "
                    f"sensor {index} no tiene un 'codigo' válido."
                )

            sensor_codigo = sensor_codigo.strip()

            if not sensor_codigo:
                raise ViviendaConfigurationError(
                    f"Vivienda '{vivienda_name}': "
                    f"sensor {index} tiene un código vacío."
                )

            sensores.append(sensor_codigo)

        if codigo in viviendas:
            raise ViviendaConfigurationError(
                f"El código de vivienda '{codigo}' está repetido."
            )

        viviendas[codigo] = ViviendaConfig(
            name=vivienda_name,
            codigo=codigo,
            enabled=enabled,
            sensores=tuple(sensores),
            latitude=latitude,
            longitude=longitude,
        )

    return viviendas
