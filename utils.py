"""Проверка значений и безопасный консольный ввод."""

from datetime import date
from math import isfinite


def validate_identifier(value: int) -> None:
    """Проверить ID независимо от источника создания объекта."""
    if type(value) is not int or value <= 0:
        raise ValueError("ID должен быть целым числом больше нуля.")


def validate_quantity(value: float, positive: bool = False) -> None:
    """Отклонить отрицательные, бесконечные и нечисловые количества."""
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError("Количество должно быть конечным числом.")
    if value < 0 or (positive and value == 0):
        raise ValueError("Количество вне допустимого диапазона.")


def input_text(prompt: str) -> str:
    """Запрашивать непустой текст до корректного ввода."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Введите непустое значение.")


def input_int(prompt: str) -> int:
    """Запрашивать положительный целочисленный идентификатор."""
    while True:
        try:
            value = int(input(prompt))
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            print("Введите целое число больше нуля.")


def input_quantity(prompt: str, positive: bool = False) -> float:
    """Прочитать количество, поддерживая точку и запятую."""
    while True:
        try:
            value = float(input(prompt).replace(",", "."))
            validate_quantity(value, positive)
            return value
        except ValueError:
            limit = "больше нуля" if positive else "не меньше нуля"
            print(f"Введите конечное число {limit}.")


def input_date(prompt: str) -> date:
    """Прочитать существующую календарную дату в формате ГГГГ-ММ-ДД."""
    while True:
        try:
            value = input(prompt).strip()
            parsed = date.fromisoformat(value)
            if parsed.isoformat() != value:
                raise ValueError
            return parsed
        except ValueError:
            print("Введите существующую дату в формате ГГГГ-ММ-ДД.")
