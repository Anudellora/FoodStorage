"""Проверки сохранения, схемы и защиты существующего файла."""

import json
from pathlib import Path

import pytest

from storage import load_data, save_data, serialize_data


def test_missing_file_and_round_trip(tmp_path, inventory):
    path = tmp_path / "data" / "inventory.json"
    assert load_data(path) == {"products": [], "stocks": []}
    save_data(path, inventory)
    assert serialize_data(load_data(path)) == serialize_data(inventory)
    assert "Молоко" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("text", ["{broken", "[]", '{"products": []}'])
def test_invalid_file_is_not_overwritten(tmp_path, text):
    path = tmp_path / "broken.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        load_data(path)
    assert path.read_text(encoding="utf-8") == text


@pytest.mark.parametrize("field, value", [
    ("quantity", -1), ("quantity", True), ("quantity", float("nan")),
    ("expiry_date", "2026-02-30"), ("product_id", 99),
])
def test_invalid_batch_rejected_on_load(tmp_path, raw_inventory, field, value):
    raw_inventory["stocks"][0][field] = value
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(raw_inventory), encoding="utf-8")
    with pytest.raises(ValueError):
        load_data(path)


def test_failed_replace_preserves_previous_file(
    tmp_path, inventory, monkeypatch
):
    path = tmp_path / "inventory.json"
    save_data(path, inventory)
    previous = path.read_bytes()
    inventory["stocks"][0].consume(1)

    def fail_replace(self, target):
        raise PermissionError("Запись запрещена")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(PermissionError):
        save_data(path, inventory)
    assert path.read_bytes() == previous
    assert list(tmp_path.iterdir()) == [path]
