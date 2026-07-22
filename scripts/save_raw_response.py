import json
from datetime import datetime, timezone
from pathlib import Path

from src.config import get_settings
from src.tuya_client import TuyaApiError, TuyaClient


def main() -> None:
    settings = get_settings()

    client = TuyaClient(
        client_id=settings.tuya_client_id,
        client_secret=settings.tuya_client_secret,
        base_url=settings.tuya_base_url,
    )

    try:
        response = client.get_device_details(
            settings.tuya_device_id
        )
    except TuyaApiError as error:
        print(f"Error de Tuya: {error}")
        raise SystemExit(1) from error

    output_directory = Path("data/raw")
    output_directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    output_file = output_directory / f"tuya_{timestamp}.json"

    output_file.write_text(
        json.dumps(
            response,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("Conexión con Tuya validada")
    print(f"Respuesta guardada en: {output_file}")


if __name__ == "__main__":
    main()