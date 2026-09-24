"""Учёт партий, сроков годности и потребности в покупках."""

from datetime import date
from decimal import Decimal

from products import find_product
from utils import validate_quantity


def get_stock_status(quantity: float, minimum_quantity: float) -> str:
    """Определить, достаточно ли запаса относительно желаемого минимума."""
    if quantity <= 0:
        return "Запас отсутствует"
    if quantity < minimum_quantity:
        return "Запас нужно пополнить"
    return "Запаса достаточно"


def calculate_purchase_quantity(
    quantity: float, minimum_quantity: float
) -> float:
    """Рассчитать недостающее количество до желаемого минимума."""
    if quantity < minimum_quantity:
        return float(Decimal(str(minimum_quantity)) - Decimal(str(quantity)))
    return 0.0


def get_expiry_status(expiry_date: date, current_date: date) -> str:
    """Определить состояние срока годности относительно указанной даты."""
    days_left = (expiry_date - current_date).days
    if days_left < 0:
        return "Срок годности истёк"
    if days_left == 0:
        return "Срок годности истекает сегодня"
    if days_left <= 3:
        return f"Срок годности скоро истекает: осталось дней — {days_left}"
    return f"Срок годности не истекает в ближайшие 3 дня: осталось {days_left}"


def add_stock(
    products: list[dict], stocks: list[dict], product_id: int,
    quantity: float, expiry_date: date,
) -> dict:
    """Добавить партию существующего продукта с положительным количеством."""
    find_product(products, product_id)
    validate_quantity(quantity, positive=True)
    stock = {
        "id": max((item["id"] for item in stocks), default=0) + 1,
        "product_id": product_id,
        "quantity": quantity,
        "expiry_date": expiry_date.isoformat(),
    }
    stocks.append(stock)
    return stock


def find_stock(stocks: list[dict], stock_id: int) -> dict:
    """Найти партию по ID."""
    for stock in stocks:
        if stock["id"] == stock_id:
            return stock
    raise ValueError(f"Партия с ID {stock_id} не найдена.")


def consume_stock(stocks: list[dict], stock_id: int, quantity: float) -> None:
    """Списать количество; полностью израсходованную партию удалить."""
    stock = find_stock(stocks, stock_id)
    validate_quantity(quantity, positive=True)
    if quantity > stock["quantity"]:
        raise ValueError("Нельзя списать больше, чем имеется в партии.")
    remaining = float(Decimal(str(stock["quantity"])) - Decimal(str(quantity)))
    if remaining == 0:
        stocks.remove(stock)
    else:
        stock["quantity"] = remaining


def remove_stock(stocks: list[dict], stock_id: int) -> None:
    """Удалить партию целиком, например при утилизации."""
    stocks.remove(find_stock(stocks, stock_id))


def available_quantity(
    stocks: list[dict], product_id: int, current_date: date
) -> float:
    """Суммировать непросроченные партии одного продукта."""
    return float(sum(
        Decimal(str(stock["quantity"])) for stock in stocks
        if stock["product_id"] == product_id
        and date.fromisoformat(stock["expiry_date"]) >= current_date
    ))


def sort_stocks(stocks: list[dict]) -> list[dict]:
    """Сортировать партии от ближайшего срока годности к дальнему."""
    return sorted(
        stocks, key=lambda stock: (stock["expiry_date"], stock["id"])
    )


def expiring_stocks(
    stocks: list[dict], current_date: date, days: int = 3
) -> list[dict]:
    """Отобрать просроченные партии и истекающие в ближайшие days дней."""
    return sort_stocks([
        stock for stock in stocks
        if (date.fromisoformat(stock["expiry_date"]) - current_date).days
        <= days
    ])


def shopping_list(
    products: list[dict], stocks: list[dict], current_date: date
) -> list[dict]:
    """Составить список недостающих продуктов с единицами измерения."""
    result = []
    for product in products:
        quantity = available_quantity(stocks, product["id"], current_date)
        needed = calculate_purchase_quantity(
            quantity, product["minimum_quantity"]
        )
        if needed > 0:
            result.append({
                "name": product["name"], "unit": product["unit"],
                "quantity": needed,
            })
    return sorted(result, key=lambda item: item["name"].casefold())


def inventory_statistics(
    products: list[dict], stocks: list[dict], current_date: date
) -> dict:
    """Посчитать продукты и партии, не складывая разные единицы измерения."""
    return {
        "products": len(products),
        "stocks": len(stocks),
        "expired": sum(
            date.fromisoformat(stock["expiry_date"]) < current_date
            for stock in stocks
        ),
        "need_purchase": len(shopping_list(products, stocks, current_date)),
    }
