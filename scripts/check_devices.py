from src.devices import (
    DeviceConfigurationError,
    load_devices,
)


def mask_device_id(device_id: str) -> str:
    """Oculta parte del ID del dispositivo para mostrarlo de forma segura."""
    if len(device_id) <= 8:
        return device_id

    return f"{device_id[:4]}...{device_id[-4:]}"


def main() -> None:
    try:
        devices = load_devices()
    except DeviceConfigurationError as error:
        print(f"Error de configuración: {error}")
        raise SystemExit(1) from error

    enabled_devices = [
        device
        for device in devices
        if device.enabled
    ]

    print(f"Dispositivos configurados: {len(devices)}")
    print(f"Dispositivos habilitados: {len(enabled_devices)}")
    print()

    for device in devices:
        status = "habilitado" if device.enabled else "deshabilitado"

        print(
            f"{device.name} | "
            f"{mask_device_id(device.device_id)} | "
            f"{device.sensor_type} | "
            f"{status}"
        )


if __name__ == "__main__":
    main()
