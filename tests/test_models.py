"""Объекты, инкапсуляция и сохранение связей при переходе с ПР2."""

import json
from copy import deepcopy
from datetime import date

import pytest

from products import Product
from stocks import Stock, add_stock, consume_stock
from storage import load_data, save_data, serialize_data


TODAY = date(2026, 9, 24)


def test_constructors_and_string_representations():
    product = Product(1, " Молоко ", " л ", 5)
    stock = Stock(1, product, 2, date(2026, 9, 26))
    assert stock.product is product
    assert stock.quantity == 2
    assert stock.expiry_date == date(2026, 9, 26)
    assert str(product) == "ID 1: Молоко"
    assert str(stock) == "Партия 1: Молоко — 2 л; годен до 26.09.2026"


@pytest.mark.parametrize("identifier", [0, -1, True, 1.5])
def test_constructors_reject_invalid_ids(identifier):
    with pytest.raises(ValueError, match="ID"):
        Product(identifier, "Молоко", "л", 5)
    with pytest.raises(ValueError, match="ID"):
        Stock(identifier, Product(1, "Молоко", "л", 5), 2, TODAY)


@pytest.mark.parametrize("name, unit", [
    (" ", "л"), ("Молоко", ""), (None, "л"), ("Молоко", None),
])
def test_product_requires_name_and_unit(name, unit):
    with pytest.raises(ValueError):
        Product(1, name, unit, 5)


def test_stock_requires_product_object_and_date():
    product = Product(1, "Молоко", "л", 5)
    with pytest.raises(ValueError, match="Product"):
        Stock(1, 1, 2, TODAY)
    with pytest.raises(ValueError, match="date"):
        Stock(1, product, 2, "2026-09-24")


def test_quantity_and_identifiers_cannot_be_assigned(inventory):
    stock = inventory["stocks"][0]
    with pytest.raises(AttributeError):
        stock.quantity = -1
    with pytest.raises(AttributeError):
        stock.id = 99
    with pytest.raises(AttributeError):
        stock.product.id = 99
    assert stock.quantity == 2
    assert stock.id == 1


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True])
def test_minimum_setter_rejects_invalid_value_without_changing_it(value):
    product = Product(1, "Молоко", "л", 5)
    with pytest.raises(ValueError):
        product.minimum_quantity = value
    assert product.minimum_quantity == 5
    product.minimum_quantity = 3
    assert product.calculate_purchase_quantity(2) == 1


def test_multiple_batches_share_one_product_but_have_independent_quantity(
    inventory,
):
    stocks = inventory["stocks"]
    assert stocks[0].product is stocks[1].product
    stocks[0].consume(1)
    assert stocks[0].quantity == 1
    assert stocks[1].quantity == 10


def test_new_batch_uses_catalog_object(inventory):
    stock = add_stock(inventory["products"], inventory["stocks"], 1, 3, TODAY)
    assert stock.product is inventory["products"][0]


def test_pr2_json_loads_as_objects_and_round_trips_unchanged(
    tmp_path, raw_inventory,
):
    path = tmp_path / "pr2.json"
    path.write_text(json.dumps(raw_inventory), encoding="utf-8")
    inventory = load_data(path)
    assert all(isinstance(item, Product) for item in inventory["products"])
    assert all(isinstance(item, Stock) for item in inventory["stocks"])
    assert inventory["stocks"][0].product is inventory["products"][0]
    assert inventory["stocks"][1].product is inventory["products"][0]
    save_data(path, inventory)
    assert json.loads(path.read_text(encoding="utf-8")) == raw_inventory
    reloaded = load_data(path)
    assert reloaded["stocks"][0].product is reloaded["products"][0]


def test_deepcopy_preserves_internal_links_without_mutating_original(
    inventory,
):
    changed = deepcopy(inventory)
    assert changed["stocks"][0].product is changed["products"][0]
    assert changed["stocks"][0].product is not inventory["products"][0]
    consume_stock(changed["stocks"], 1, 1)
    assert inventory["stocks"][0].quantity == 2
    assert changed["stocks"][0].quantity == 1


def test_detached_product_rejected_before_file_is_changed(tmp_path, inventory):
    path = tmp_path / "inventory.json"
    save_data(path, inventory)
    previous = path.read_bytes()
    detached = Product(1, "Другой продукт", "кг", 1)
    inventory["stocks"].append(Stock(4, detached, 2, TODAY))
    with pytest.raises(ValueError, match="вне каталога"):
        save_data(path, inventory)
    assert path.read_bytes() == previous


def test_duplicate_objects_are_not_silently_serialized(inventory):
    inventory["products"].append(inventory["products"][0])
    with pytest.raises(ValueError, match="повторяющиеся ID"):
        serialize_data(inventory)
