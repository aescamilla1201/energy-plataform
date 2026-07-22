from typing import Any


def extract_properties(
    response: dict[str, Any],
) -> dict[str, Any]:
    result = response.get("result", {})
    properties = result.get("properties", [])

    return {
        item["code"]: item.get("value")
        for item in properties
        if "code" in item
    }