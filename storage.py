"""Чтение, проверка и атомарное сохранение JSON-файла проекта."""

import json
import os
import tempfile
from datetime import date
from pathlib import Path

from utils import validate_quantity


def validate_data(data: dict) -> None:
    """Проверить схему, идентификаторы и связи до использования данных."""
    if not isinstance(data, dict) or set(data) != {"products", "stocks"}:
        raise ValueError("JSON должен содержать products и stocks.")
    product_ids = set()
    for collection, fields in (
        ("products", {"id", "name", "unit", "minimum_quantity"}),
        ("stocks", {"id", "product_id", "quantity", "expiry_date"}),
    ):
        if not isinstance(data[collection], list):
            raise ValueError(f"{collection} должен быть списком.")
        ids, names = set(), set()
        for item in data[collection]:
            if not isinstance(item, dict) or set(item) != fields:
                raise ValueError(f"Неверные поля записи в {collection}.")
            identifier = item["id"]
            if type(identifier) is not int or identifier <= 0:
                raise ValueError("ID должен быть целым числом больше нуля.")
            if identifier in ids:
                raise ValueError("Обнаружены повторяющиеся ID.")
            ids.add(identifier)
            if collection == "products":
                for field in ("name", "unit"):
                    value = item[field]
                    if not isinstance(value, str) or not value.strip():
                        raise ValueError("Название и единица обязательны.")
                name = item["name"].strip().casefold()
                if name in names:
                    raise ValueError("Названия продуктов повторяются.")
                names.add(name)
                validate_quantity(item["minimum_quantity"])
            else:
                if (type(item["product_id"]) is not int
                        or item["product_id"] not in product_ids):
                    raise ValueError("У партии указан неизвестный продукт.")
                validate_quantity(item["quantity"], positive=True)
                expiry = item["expiry_date"]
                if not isinstance(expiry, str):
                    raise ValueError("Срок годности должен быть строкой.")
                if date.fromisoformat(expiry).isoformat() != expiry:
                    raise ValueError("Формат срока годности: ГГГГ-ММ-ДД.")
        if collection == "products":
            product_ids = ids


def load_data(path: Path) -> dict:
    """Загрузить JSON; отсутствие файла означает начало нового учёта."""
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return {"products": [], "stocks": []}
    validate_data(data)
    return data


def save_data(path: Path, data: dict) -> None:
    """Заменить файл только после успешной записи полного снимка данных."""
    validate_data(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2,
                      allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
