from src.devices import (
    DeviceConfigurationError,
    load_devices,
)
from src.viviendas import (
    ViviendaConfigurationError,
    load_viviendas,
)


def main() -> None:
    try:
        devices = load_devices()
        viviendas = load_viviendas()
    except (
        DeviceConfigurationError,
        ViviendaConfigurationError,
    ) as error:
        print(f"Error de configuración: {error}")
        raise SystemExit(1) from error

    device_names = {
        device.name
        for device in devices
    }

    assigned_devices: dict[str, str] = {}
    errors: list[str] = []

    enabled_viviendas = [
        vivienda
        for vivienda in viviendas.values()
        if vivienda.enabled
    ]

    for vivienda in enabled_viviendas:

        for sensor_codigo in vivienda.sensores:

            if sensor_codigo not in device_names:
                errors.append(
                    f"{vivienda.codigo}: "
                    f"el dispositivo '{sensor_codigo}' "
                    "no existe en devices.json."
                )
                continue

            if sensor_codigo in assigned_devices:
                previous_vivienda = assigned_devices[sensor_codigo]

                errors.append(
                    f"{sensor_codigo} está asignado a "
                    f"'{previous_vivienda}' y también a "
                    f"'{vivienda.codigo}'."
                )
                continue

            assigned_devices[sensor_codigo] = vivienda.codigo

    if errors:
        print("Se encontraron errores:\n")

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    print(f"Viviendas configuradas: {len(viviendas)}")
    print(f"Viviendas habilitadas: {len(enabled_viviendas)}")
    print(f"Dispositivos configurados: {len(devices)}")
    print(f"Dispositivos asignados: {len(assigned_devices)}")
    print()

    for vivienda in viviendas.values():

        status = (
            "habilitada"
            if vivienda.enabled
            else "deshabilitada"
        )

        sensores = ", ".join(vivienda.sensores)

        print(
            f"{vivienda.codigo} | "
            f"{vivienda.name} | "
            f"{sensores} | "
            f"{status}"
        )


if __name__ == "__main__":
    main()