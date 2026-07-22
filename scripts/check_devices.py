from src.devices import (
    DeviceConfigurationError,
    load_devices,
)


def mask_device_id(
    device_id: str,
    visible: int = 4,
) -> str:
    if len(device_id) <= visible:
        return "*" * len(device_id)

    return f"{device_id[:visible]}********"


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
            f"- {device.name} | "
            f"{mask_device_id(device.device_id)} | "
            f"{device.sensor_type} | "
            f"{device.site} | "
            f"{status}"
        )


if __name__ == "__main__":
    main()