"""Консольное приложение FoodStorage: практическая работа № 3."""

import argparse
from copy import deepcopy
from datetime import date
from pathlib import Path

from products import add_product, find_product, search_products
from stocks import (
    add_stock, available_quantity, consume_stock, expiring_stocks,
    inventory_statistics,
    remove_stock, shopping_list, sort_stocks,
)
from storage import load_data, save_data
from utils import input_date, input_int, input_quantity, input_text


DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "inventory.json"


def show_products(data: dict[str, list], query: str = "") -> None:
    """Вывести каталог и достаточность пригодного запаса."""
    products = search_products(data["products"], query)
    if not products:
        print("Продукты не найдены. Добавьте продукт через пункт 2.")
    for product in products:
        quantity = available_quantity(
            data["stocks"], product.id, date.today()
        )
        status = product.get_stock_status(quantity)
        print(f"{product} — {quantity:g} "
              f"{product.unit}; минимум {product.minimum_quantity:g}; "
              f"{status}")


def show_stocks(data: dict[str, list], urgent_only: bool = False) -> None:
    """Показать партии по сроку годности, при необходимости с фильтром."""
    today = date.today()
    stocks = (expiring_stocks(data["stocks"], today) if urgent_only
              else sort_stocks(data["stocks"]))
    if not stocks:
        print("Подходящих партий нет.")
    for stock in stocks:
        print(f"{stock}; {stock.get_expiry_status(today)}")


def change_data(choice: str, data: dict[str, list]) -> None:
    """Собрать пользовательский ввод и изменить рабочую копию данных."""
    if choice == "2":
        add_product(
            data["products"], input_text("Название: "),
            input_text("Единица измерения (кг, л, шт): "),
            input_quantity("Минимальный желаемый запас: "),
        )
    elif choice == "3":
        show_products(data)
        if not data["products"]:
            raise ValueError("Сначала добавьте продукт.")
        product_id = input_int("ID продукта: ")
        product = find_product(data["products"], product_id)
        add_stock(
            data["products"], data["stocks"], product_id,
            input_quantity(f"Количество ({product.unit}): ", True),
            input_date("Срок годности (ГГГГ-ММ-ДД): "),
        )
    else:
        show_stocks(data)
        if not data["stocks"]:
            raise ValueError("Сначала добавьте партию.")
        stock_id = input_int("ID партии: ")
        if choice == "5":
            consume_stock(data["stocks"], stock_id,
                          input_quantity("Списать количество: ", True))
        else:
            remove_stock(data["stocks"], stock_id)


def show_report(choice: str, data: dict[str, list]) -> None:
    """Вывести каталог, поиск, партии, покупки или статистику."""
    if choice == "1":
        show_products(data)
    elif choice == "4":
        show_stocks(data)
    elif choice == "7":
        show_products(data, input_text("Часть названия: "))
    elif choice == "8":
        show_stocks(data, urgent_only=True)
    elif choice == "9":
        items = shopping_list(data["products"], data["stocks"], date.today())
        if not items:
            print("Покупки не требуются.")
        for item in items:
            print(f"{item['name']}: купить "
                  f"{item['quantity']:g} {item['unit']}")
    else:
        stats = inventory_statistics(
            data["products"], data["stocks"], date.today()
        )
        print(f"Продуктов: {stats['products']}; партий: {stats['stocks']}; "
              f"просроченных партий: {stats['expired']}; "
              f"продуктов к покупке: {stats['need_purchase']}")


def run_menu(path: Path, data: dict[str, list]) -> None:
    """Обрабатывать команды; сохранять изменения до замены данных в памяти."""
    while True:
        print("\n1. Продукты и остатки   2. Добавить продукт\n"
              "3. Добавить партию      4. Партии по сроку годности\n"
              "5. Списать количество   6. Удалить партию\n"
              "7. Поиск продуктов      8. Просроченные и истекающие за 3 дня\n"
              "9. Список покупок      10. Статистика\n0. Выход")
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            return
        if choice not in {str(number) for number in range(1, 11)}:
            print("Неизвестная команда. Выберите пункт от 0 до 10.")
            continue
        try:
            if choice in {"2", "3", "5", "6"}:
                changed = deepcopy(data)
                change_data(choice, changed)
                save_data(path, changed)
                data = changed
                print("Изменения сохранены.")
            else:
                show_report(choice, data)
        except (ValueError, OSError) as error:
            print(f"Операция не выполнена: {error}")


def main() -> int:
    """Загрузить данные и запустить меню с обработкой ошибок."""
    parser = argparse.ArgumentParser(description="Контроль запасов продуктов")
    parser.add_argument("--data", type=Path, default=DEFAULT_PATH,
                        help="путь к JSON-файлу данных")
    args = parser.parse_args()
    try:
        data = load_data(args.data)
    except (ValueError, OSError) as error:
        print(f"Не удалось загрузить данные: {error}")
        print("Исправьте файл или укажите другой через --data. "
              "Файл не изменён.")
        return 1
    print(f"FoodStorage — контроль запасов продуктов\nДанные: {args.data}")
    try:
        run_menu(args.data, data)
    except (EOFError, KeyboardInterrupt):
        print("\nВвод прерван. Завершённые операции уже сохранены.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
