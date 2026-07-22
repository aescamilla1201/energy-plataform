from typing import Any


def extract_properties(
    response: dict[str, Any],
) -> dict[str, Any]:
    """
    Convierte la lista de propiedades de Tuya en un diccionario:

    [
        {"code": "voltage_a", "value": 1339},
        {"code": "current_a", "value": 8344},
    ]

    pasa a:

    {
        "voltage_a": 1339,
        "current_a": 8344,
    }
    """
    result = response.get("result", {})
    properties = result.get("properties", [])

    return {
        item["code"]: item.get("value")
        for item in properties
        if "code" in item
    }


def normalize_dual_meter(
    properties: dict[str, Any],
) -> dict[str, Any]:
    """
    Convierte los valores crudos del medidor dual a unidades físicas.
    """

    energy_forward_a_wh = (
        properties.get("energy_forword_a", 0) * 10
    )

    energy_reverse_a_wh = (
        properties.get("energy_reverse_a", 0) * 10
    )

    energy_forward_b_wh = (
        properties.get("energy_forword_b", 0) * 10
    )

    energy_reverse_b_wh = (
        properties.get("energy_reserse_b", 0) * 10
    )

    total_forward_wh = (
        properties.get("forward_energy_total", 0) * 10
    )

    total_reverse_wh = (
        properties.get("reverse_energy_total", 0) * 10
    )

    frequency_hz = properties.get("freq", 0) / 100

    return {
        "phase_a": {
            "voltage_v": properties.get("voltage_a", 0) / 10,
            "current_a": properties.get("current_a", 0) / 1000,
            "power_w": properties.get("power_a", 0) / 10,
            "power_factor": (
                properties.get("power_factor", 0) / 100
            ),
            "frequency_hz": frequency_hz,
            "direction": properties.get("direction_a"),
            "energy_forward_wh": energy_forward_a_wh,
            "energy_forward_kwh": energy_forward_a_wh / 1000,
            "energy_reverse_wh": energy_reverse_a_wh,
            "energy_reverse_kwh": energy_reverse_a_wh / 1000,
        },
        "phase_b": {
            "current_a": properties.get("current_b", 0) / 1000,
            "power_w": properties.get("power_b", 0) / 10,
            "power_factor": (
                properties.get("power_factor_b", 0) / 100
            ),
            "frequency_hz": frequency_hz,
            "direction": properties.get("direction_b"),
            "energy_forward_wh": energy_forward_b_wh,
            "energy_forward_kwh": energy_forward_b_wh / 1000,
            "energy_reverse_wh": energy_reverse_b_wh,
            "energy_reverse_kwh": energy_reverse_b_wh / 1000,
        },
        "totals": {
            "power_w": properties.get("total_power", 0) / 10,
            "energy_forward_wh": total_forward_wh,
            "energy_forward_kwh": total_forward_wh / 1000,
            "energy_reverse_wh": total_reverse_wh,
            "energy_reverse_kwh": total_reverse_wh / 1000,
        },
    }