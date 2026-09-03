import argparse
import json

from src.config import get_settings
from src.devices import (
    DeviceConfigurationError,
    load_devices,
)
from src.tuya_client import TuyaApiError, TuyaClient


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta los detalles de un dispositivo Tuya."
    )
    parser.add_argument(
        "device_code",
        help="Código del dispositivo, por ejemplo EM-002.",
    )
    args = parser.parse_args()

    print(
        f"Consultando detalles de {args.device_code}..."
    )

    try:
        devices = load_devices()
    except DeviceConfigurationError as error:
        print(f"Error de configuración: {error}")
        raise SystemExit(1) from error

    device = next(
        (
            item
            for item in devices
            if item.name == args.device_code
        ),
        None,
    )

    if device is None:
        print(
            f"Error: no existe '{args.device_code}' "
            "en devices.json."
        )
        raise SystemExit(1)

    settings = get_settings()

    client = TuyaClient(
        client_id=settings.tuya_client_id,
        client_secret=settings.tuya_client_secret,
        base_url=settings.tuya_base_url,
    )

    try:
        response = client.get_device_details(
            device.device_id
        )
    except TuyaApiError as error:
        print(f"Error de Tuya: {error}")
        raise SystemExit(1) from error
    except Exception as error:
        print(f"Error inesperado: {error}")
        raise SystemExit(1) from error

    print(
        json.dumps(
            response,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()