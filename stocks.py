"""Партии продуктов: объектная модель, коллекции и отчёты."""

from datetime import date
from decimal import Decimal

from products import Product, find_product
from utils import validate_identifier, validate_quantity


class Stock:
    """Партия, связанная с объектом продукта, с защищённым количеством."""

    def __init__(
        self, stock_id: int, product: Product, quantity: float,
        expiry_date: date,
    ) -> None:
        validate_identifier(stock_id)
        if not isinstance(product, Product):
            raise ValueError("Партия должна быть связана с объектом Product.")
        validate_quantity(quantity, positive=True)
        if type(expiry_date) is not date:
            raise ValueError("Срок годности должен иметь тип date.")
        self._id = stock_id
        self._product = product
        self._quantity = quantity
        self._expiry_date = expiry_date

    @property
    def id(self) -> int:
        """Идентификатор партии."""
        return self._id

    @property
    def product(self) -> Product:
        """Тот же объект продукта, который находится в каталоге."""
        return self._product

    @property
    def quantity(self) -> float:
        """Остаток; изменяется только проверенной операцией consume."""
        return self._quantity

    @property
    def expiry_date(self) -> date:
        """Дата окончания срока годности партии."""
        return self._expiry_date

    def is_expired(self, current_date: date) -> bool:
        """Считать партию просроченной со следующего дня после срока."""
        return self.expiry_date < current_date

    def get_expiry_status(self, current_date: date) -> str:
        """Описать срок годности этой партии относительно указанной даты."""
        days_left = (self.expiry_date - current_date).days
        if self.is_expired(current_date):
            return "Срок годности истёк"
        if days_left == 0:
            return "Срок годности истекает сегодня"
        if days_left <= 3:
            return f"Срок годности скоро истекает: осталось дней — {days_left}"
        return ("Срок годности не истекает в ближайшие 3 дня: "
                f"осталось {days_left}")

    def consume(self, quantity: float) -> None:
        """Списать количество без отрицательного или ложного остатка."""
        validate_quantity(quantity, positive=True)
        if quantity > self.quantity:
            raise ValueError("Нельзя списать больше, чем имеется в партии.")
        self._quantity = float(
            Decimal(str(self.quantity)) - Decimal(str(quantity))
        )

    def to_dict(self) -> dict:
        """Сохранить ссылку на продукт как ID, дату как ISO-строку."""
        return {
            "id": self.id, "product_id": self.product.id,
            "quantity": self.quantity,
            "expiry_date": self.expiry_date.isoformat(),
        }

    def __str__(self) -> str:
        return (f"Партия {self.id}: {self.product.name} — "
                f"{self.quantity:g} {self.product.unit}; "
                f"годен до {self.expiry_date:%d.%m.%Y}")


def add_stock(
    products: list[Product], stocks: list[Stock], product_id: int,
    quantity: float, expiry_date: date,
) -> Stock:
    """Добавить партию, связанную с объектом из каталога продуктов."""
    product = find_product(products, product_id)
    stock = Stock(
        max((item.id for item in stocks), default=0) + 1,
        product, quantity, expiry_date,
    )
    stocks.append(stock)
    return stock


def find_stock(stocks: list[Stock], stock_id: int) -> Stock:
    """Найти партию по ID."""
    for stock in stocks:
        if stock.id == stock_id:
            return stock
    raise ValueError(f"Партия с ID {stock_id} не найдена.")


def consume_stock(stocks: list[Stock], stock_id: int, quantity: float) -> None:
    """Вызвать метод партии и удалить её при полном списании."""
    stock = find_stock(stocks, stock_id)
    stock.consume(quantity)
    if stock.quantity == 0:
        stocks.remove(stock)


def remove_stock(stocks: list[Stock], stock_id: int) -> None:
    """Удалить партию целиком, например при утилизации."""
    stocks.remove(find_stock(stocks, stock_id))


def available_quantity(
    stocks: list[Stock], product_id: int, current_date: date
) -> float:
    """Суммировать непросроченные партии одного продукта."""
    return float(sum(
        Decimal(str(stock.quantity)) for stock in stocks
        if stock.product.id == product_id
        and not stock.is_expired(current_date)
    ))


def sort_stocks(stocks: list[Stock]) -> list[Stock]:
    """Сортировать партии от ближайшего срока годности к дальнему."""
    return sorted(stocks, key=lambda stock: (stock.expiry_date, stock.id))


def expiring_stocks(
    stocks: list[Stock], current_date: date, days: int = 3
) -> list[Stock]:
    """Отобрать просроченные партии и истекающие в ближайшие days дней."""
    return sort_stocks([
        stock for stock in stocks
        if (stock.expiry_date - current_date).days <= days
    ])


def shopping_list(
    products: list[Product], stocks: list[Stock], current_date: date
) -> list[dict]:
    """Составить отчёт о недостающих продуктах с единицами измерения."""
    result = []
    for product in products:
        quantity = available_quantity(stocks, product.id, current_date)
        needed = product.calculate_purchase_quantity(quantity)
        if needed > 0:
            result.append({
                "name": product.name, "unit": product.unit, "quantity": needed,
            })
    return sorted(result, key=lambda item: item["name"].casefold())


def inventory_statistics(
    products: list[Product], stocks: list[Stock], current_date: date
) -> dict[str, int]:
    """Посчитать продукты и партии, не складывая разные единицы измерения."""
    return {
        "products": len(products),
        "stocks": len(stocks),
        "expired": sum(stock.is_expired(current_date) for stock in stocks),
        "need_purchase": len(shopping_list(products, stocks, current_date)),
    }
