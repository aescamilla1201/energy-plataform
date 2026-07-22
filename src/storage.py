import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def save_json_reading(
    data: dict[str, Any],
    *,
    output_folder: str = "data/normalized",
) -> Path:
    folder = Path(output_folder)
    folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    output_file = folder / f"reading_{timestamp}.json"

    output_file.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output_file