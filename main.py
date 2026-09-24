"""Начальный сценарий сервиса контроля запасов продуктов (ПР1)."""

from datetime import date, timedelta


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
        return minimum_quantity - quantity
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


def main() -> None:
    """Проверить один запас и вывести результат для пользователя."""
    product_name = "Молоко"
    unit = "л"
    quantity = float("2")
    minimum_quantity = float("5")
    current_date = date.today()
    expiry_date = current_date + timedelta(days=2)

    available_quantity = quantity
    if expiry_date < current_date:
        available_quantity = 0.0

    purchase_quantity = calculate_purchase_quantity(
        available_quantity, minimum_quantity
    )

    print("FoodStorage — контроль запасов продуктов")
    print(f"Продукт: {product_name}")
    print(f"Количество: {quantity:g} {unit}")
    print(f"Желаемый запас: {minimum_quantity:g} {unit}")
    print(f"Дата проверки: {current_date:%d.%m.%Y}")
    print(f"Срок годности: {expiry_date:%d.%m.%Y}")
    print(get_expiry_status(expiry_date, current_date))
    print(f"Пригодный запас: {available_quantity:g} {unit}")
    print(get_stock_status(available_quantity, minimum_quantity))
    print(f"Нужно купить: {purchase_quantity:g} {unit}")


if __name__ == "__main__":
    main()
