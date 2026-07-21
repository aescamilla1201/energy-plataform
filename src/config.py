import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    tuya_client_id: str
    tuya_client_secret: str
    tuya_device_id: str
    tuya_base_url: str


def get_settings() -> Settings:
    required_variables = [
        "TUYA_CLIENT_ID",
        "TUYA_CLIENT_SECRET",
        "TUYA_DEVICE_ID",
    ]

    missing_variables = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing_variables:
        raise RuntimeError(
            "Faltan variables de entorno: "
            + ", ".join(missing_variables)
        )

    return Settings(
        tuya_client_id=os.environ["TUYA_CLIENT_ID"],
        tuya_client_secret=os.environ["TUYA_CLIENT_SECRET"],
        tuya_device_id=os.environ["TUYA_DEVICE_ID"],
        tuya_base_url=os.getenv(
            "TUYA_BASE_URL",
            "https://openapi.tuyaus.com",
        ).rstrip("/"),
    )