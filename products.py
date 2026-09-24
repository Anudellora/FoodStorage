"""Продукты: объектная модель и операции с каталогом."""

from decimal import Decimal

from utils import validate_identifier, validate_quantity


class Product:
    """Продукт с единицей измерения и желаемым минимальным запасом."""

    def __init__(
        self, product_id: int, name: str, unit: str, minimum_quantity: float
    ) -> None:
        validate_identifier(product_id)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Название продукта обязательно.")
        if not isinstance(unit, str) or not unit.strip():
            raise ValueError("Единица измерения обязательна.")
        self._id = product_id
        self._name = name.strip()
        self._unit = unit.strip()
        self.minimum_quantity = minimum_quantity

    @property
    def id(self) -> int:
        """Идентификатор, неизменяемый после создания."""
        return self._id

    @property
    def name(self) -> str:
        """Название продукта."""
        return self._name

    @property
    def unit(self) -> str:
        """Единица измерения всех партий продукта."""
        return self._unit

    @property
    def minimum_quantity(self) -> float:
        """Минимальный желаемый запас."""
        return self._minimum_quantity

    @minimum_quantity.setter
    def minimum_quantity(self, value: float) -> None:
        validate_quantity(value)
        self._minimum_quantity = value

    def get_stock_status(self, quantity: float) -> str:
        """Сравнить доступное количество с минимумом этого продукта."""
        validate_quantity(quantity)
        if quantity == 0:
            return "Запас отсутствует"
        if quantity < self.minimum_quantity:
            return "Запас нужно пополнить"
        return "Запаса достаточно"

    def calculate_purchase_quantity(self, quantity: float) -> float:
        """Рассчитать, сколько нужно купить именно этого продукта."""
        validate_quantity(quantity)
        if quantity < self.minimum_quantity:
            return float(
                Decimal(str(self.minimum_quantity)) - Decimal(str(quantity))
            )
        return 0.0

    def to_dict(self) -> dict:
        """Представить продукт в совместимом с ПР2 формате JSON."""
        return {
            "id": self.id, "name": self.name, "unit": self.unit,
            "minimum_quantity": self.minimum_quantity,
        }

    def __str__(self) -> str:
        return f"ID {self.id}: {self.name}"


def find_product(products: list[Product], product_id: int) -> Product:
    """Найти продукт по идентификатору или сообщить об отсутствии."""
    for product in products:
        if product.id == product_id:
            return product
    raise ValueError(f"Продукт с ID {product_id} не найден.")


def add_product(
    products: list[Product], name: str, unit: str, minimum_quantity: float
) -> Product:
    """Добавить продукт с уникальным названием и единицей измерения."""
    product = Product(
        max((item.id for item in products), default=0) + 1,
        name, unit, minimum_quantity,
    )
    for existing in products:
        if existing.name.casefold() == product.name.casefold():
            raise ValueError("Продукт с таким названием уже существует.")
    products.append(product)
    return product


def search_products(products: list[Product], query: str = "") -> list[Product]:
    """Найти по подстроке без учёта регистра и сортировать по названию."""
    matches = (
        product for product in products
        if query.strip().casefold() in product.name.casefold()
    )
    return sorted(matches, key=lambda product: product.name.casefold())
