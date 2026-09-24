"""Изолированные данные для проверки предметной области."""

import pytest


@pytest.fixture
def inventory():
    return {
        "products": [
            {"id": 1, "name": "Молоко", "unit": "л", "minimum_quantity": 5},
            {"id": 2, "name": "Рис", "unit": "кг", "minimum_quantity": 1},
        ],
        "stocks": [
            {"id": 1, "product_id": 1, "quantity": 2,
             "expiry_date": "2026-09-26"},
            {"id": 2, "product_id": 1, "quantity": 10,
             "expiry_date": "2026-09-23"},
            {"id": 3, "product_id": 2, "quantity": 3,
             "expiry_date": "2027-09-24"},
        ],
    }
