"""Проверки сценариев учёта продуктов и партий."""

from datetime import date, timedelta

import pytest

from products import Product, add_product, search_products
from stocks import (
    Stock, add_stock, available_quantity,
    consume_stock, expiring_stocks,
    inventory_statistics, remove_stock, shopping_list,
)


TODAY = date(2026, 9, 24)


def test_add_search_and_reject_duplicate(inventory):
    products = inventory["products"]
    added = add_product(products, " Масло ", "г", 200)
    assert added.id == 3
    assert search_products(products, "МАС") == [added]
    with pytest.raises(ValueError, match="уже существует"):
        add_product(products, "масло", "кг", 1)
    assert len(products) == 3


def test_new_product_without_stocks_needs_purchase():
    products = []
    add_product(products, "Рис", "кг", 2)
    assert shopping_list(products, [], TODAY) == [
        {"name": "Рис", "unit": "кг", "quantity": 2}
    ]


def test_purchase_ignores_expired_batches(inventory):
    assert available_quantity(inventory["stocks"], 1, TODAY) == 2
    assert shopping_list(
        inventory["products"], inventory["stocks"], TODAY
    ) == [{"name": "Молоко", "unit": "л", "quantity": 3}]


def test_expiry_today_still_counts(inventory):
    add_stock(inventory["products"], inventory["stocks"], 1, 3, TODAY)
    assert available_quantity(inventory["stocks"], 1, TODAY) == 5
    assert shopping_list(
        inventory["products"], inventory["stocks"], TODAY
    ) == []


def test_consume_partial_then_complete(inventory):
    stocks = inventory["stocks"]
    consume_stock(stocks, 1, 0.5)
    assert stocks[0].quantity == 1.5
    consume_stock(stocks, 1, 1.5)
    assert all(stock.id != 1 for stock in stocks)


def test_fractional_consumption_does_not_leave_phantom_stock(inventory):
    stocks = []
    add_stock(inventory["products"], stocks, 1, 0.3, TODAY)
    consume_stock(stocks, 1, 0.1)
    consume_stock(stocks, 1, 0.2)
    assert stocks == []
    product = Product(1, "Молоко", "л", 0.3)
    assert product.calculate_purchase_quantity(0.1) == 0.2


def test_overconsumption_preserves_stock(inventory):
    with pytest.raises(ValueError, match="больше"):
        consume_stock(inventory["stocks"], 1, 3)
    assert inventory["stocks"][0].quantity == 2


@pytest.mark.parametrize("quantity", [-1, 0, float("nan"), float("inf")])
def test_reject_invalid_stock_quantity(inventory, quantity):
    with pytest.raises(ValueError):
        add_stock(inventory["products"], [], 1, quantity, TODAY)


def test_reject_unknown_product_and_batch(inventory):
    with pytest.raises(ValueError, match="не найден"):
        add_stock(inventory["products"], [], 99, 1, TODAY)
    with pytest.raises(ValueError, match="не найдена"):
        remove_stock(inventory["stocks"], 99)


def test_urgent_batches_sorted_and_deletion_updates_statistics(inventory):
    stocks = inventory["stocks"]
    assert [item.id for item in expiring_stocks(stocks, TODAY)] == [2, 1]
    remove_stock(stocks, 2)
    assert inventory_statistics(inventory["products"], stocks, TODAY) == {
        "products": 2, "stocks": 2, "expired": 0, "need_purchase": 1,
    }


@pytest.mark.parametrize("days, expected", [
    (-1, "Срок годности истёк"),
    (0, "Срок годности истекает сегодня"),
    (3, "Срок годности скоро истекает"),
    (4, "Срок годности не истекает"),
])
def test_pr1_expiry_boundaries(days, expected):
    product = Product(1, "Молоко", "л", 5)
    stock = Stock(1, product, 2, TODAY + timedelta(days=days))
    assert stock.get_expiry_status(TODAY).startswith(expected)


def test_pr1_stock_status_and_no_unnecessary_purchase():
    product = Product(1, "Молоко", "л", 5)
    assert product.get_stock_status(0) == "Запас отсутствует"
    assert product.get_stock_status(2) == "Запас нужно пополнить"
    assert product.get_stock_status(5) == "Запаса достаточно"
    assert product.calculate_purchase_quantity(7) == 0
