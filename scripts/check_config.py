from src.config import get_settings


def mask(value: str, visible: int = 4) -> str:
    if len(value) <= visible:
        return "*" * len(value)

    return f"{value[:visible]}********"


def main() -> None:
    settings = get_settings()

    print("Configuración cargada correctamente")
    print(f"Base URL: {settings.tuya_base_url}")
    print(f"Client ID: {mask(settings.tuya_client_id)}")
    print(f"Device ID: {mask(settings.tuya_device_id)}")
    print("Client Secret: configurado")


if __name__ == "__main__":
    main()