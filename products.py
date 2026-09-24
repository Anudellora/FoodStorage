"""Операции с каталогом продуктов, представленным списком словарей."""

from utils import validate_quantity


def find_product(products: list[dict], product_id: int) -> dict:
    """Найти продукт по идентификатору или сообщить об отсутствии."""
    for product in products:
        if product["id"] == product_id:
            return product
    raise ValueError(f"Продукт с ID {product_id} не найден.")


def add_product(
    products: list[dict], name: str, unit: str, minimum_quantity: float
) -> dict:
    """Добавить продукт с уникальным названием и единицей измерения."""
    name, unit = name.strip(), unit.strip()
    if not name or not unit:
        raise ValueError("Название и единица измерения обязательны.")
    validate_quantity(minimum_quantity)
    for product in products:
        if product["name"].casefold() == name.casefold():
            raise ValueError("Продукт с таким названием уже существует.")
    product = {
        "id": max((item["id"] for item in products), default=0) + 1,
        "name": name,
        "unit": unit,
        "minimum_quantity": minimum_quantity,
    }
    products.append(product)
    return product


def search_products(products: list[dict], query: str = "") -> list[dict]:
    """Найти по подстроке без учёта регистра и сортировать по названию."""
    matches = (
        product for product in products
        if query.strip().casefold() in product["name"].casefold()
    )
    return sorted(matches, key=lambda product: product["name"].casefold())
