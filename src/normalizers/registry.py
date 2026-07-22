from collections.abc import Callable
from typing import Any

from src.normalizers.dual_meter import normalize_dual_meter


Normalizer = Callable[
    [dict[str, Any]],
    dict[str, Any],
]


NORMALIZERS: dict[str, Normalizer] = {
    "dual_meter": normalize_dual_meter,
}


def normalize_by_type(
    sensor_type: str,
    properties: dict[str, Any],
) -> dict[str, Any]:
    normalizer = NORMALIZERS.get(sensor_type)

    if normalizer is None:
        supported = ", ".join(sorted(NORMALIZERS))

        raise ValueError(
            f"Tipo de sensor no soportado: {sensor_type}. "
            f"Tipos disponibles: {supported}"
        )

    return normalizer(properties)