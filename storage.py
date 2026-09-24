"""Чтение, проверка и атомарное сохранение JSON-файла проекта."""

import json
import os
import tempfile
from datetime import date
from pathlib import Path

from products import Product
from stocks import Stock
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


def deserialize_data(data: dict) -> dict[str, list]:
    """Построить объекты из JSON ПР2 и восстановить общие ссылки."""
    validate_data(data)
    products = [
        Product(item["id"], item["name"], item["unit"],
                item["minimum_quantity"])
        for item in data["products"]
    ]
    by_id = {product.id: product for product in products}
    stocks = [
        Stock(item["id"], by_id[item["product_id"]], item["quantity"],
              date.fromisoformat(item["expiry_date"]))
        for item in data["stocks"]
    ]
    return {"products": products, "stocks": stocks}


def serialize_data(data: dict[str, list]) -> dict:
    """Преобразовать объекты в JSON, проверив целостность связей."""
    products, stocks = data["products"], data["stocks"]
    if not all(isinstance(product, Product) for product in products):
        raise ValueError("Каталог должен содержать объекты Product.")
    if not all(isinstance(stock, Stock) for stock in stocks):
        raise ValueError("Запасы должны содержать объекты Stock.")
    by_id = {product.id: product for product in products}
    for stock in stocks:
        if by_id.get(stock.product.id) is not stock.product:
            raise ValueError("Партия связана с продуктом вне каталога.")
    serialized = {
        "products": [product.to_dict() for product in products],
        "stocks": [stock.to_dict() for stock in stocks],
    }
    validate_data(serialized)
    return serialized


def load_data(path: Path) -> dict[str, list]:
    """Загрузить JSON; отсутствие файла означает начало нового учёта."""
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return {"products": [], "stocks": []}
    return deserialize_data(data)


def save_data(path: Path, data: dict[str, list]) -> None:
    """Заменить файл только после успешной записи полного снимка данных."""
    serialized = serialize_data(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(serialized, stream, ensure_ascii=False, indent=2,
                      allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
