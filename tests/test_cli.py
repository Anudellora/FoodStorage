"""Проверки пользовательского ввода, перезапуска и ошибок сохранения."""

import subprocess
import sys
from pathlib import Path

import main
from storage import load_data
from utils import input_date, input_quantity


SCRIPT = Path(__file__).resolve().parents[1] / "main.py"


def test_input_retries_invalid_numbers_and_dates(monkeypatch):
    answers = iter(["abc", "-1", "nan", "inf", "1,5"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert input_quantity("Количество: ") == 1.5
    answers = iter(["2026-02-30", "24.09.2026", "2026-09-24"])
    assert input_date("Дата: ").isoformat() == "2026-09-24"


def test_cli_create_consume_and_reload(tmp_path):
    path = tmp_path / "inventory.json"
    command = [sys.executable, str(SCRIPT), "--data", str(path)]
    commands = "x\n2\nМолоко\nл\n5\n3\n1\n2\n2099-01-01\n5\n1\n0,5\n0\n"
    first = subprocess.run(command, input=commands, text=True,
                           capture_output=True, timeout=10)
    assert first.returncode == 0, first.stderr
    assert "Неизвестная команда" in first.stdout
    assert load_data(path)["stocks"][0]["quantity"] == 1.5
    second = subprocess.run(command, input="1\n9\n10\n0\n", text=True,
                            capture_output=True, timeout=10)
    assert second.returncode == 0, second.stderr
    assert "Молоко — 1.5 л" in second.stdout
    assert "купить 3.5 л" in second.stdout


def test_cli_corrupt_file_exits_without_traceback(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{broken", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--data", str(path)],
        text=True, capture_output=True, timeout=10,
    )
    assert result.returncode == 1
    assert "Файл не изменён" in result.stdout
    assert not result.stderr
    assert path.read_text(encoding="utf-8") == "{broken"


def test_failed_save_does_not_change_menu_data(tmp_path, monkeypatch, capsys):
    answers = iter(["2", "Молоко", "л", "5", "1", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    def fail_save(path, data):
        raise PermissionError("Запись запрещена")

    monkeypatch.setattr(main, "save_data", fail_save)
    main.run_menu(tmp_path / "inventory.json", {"products": [], "stocks": []})
    output = capsys.readouterr().out
    assert "Операция не выполнена" in output
    assert "Продукты не найдены" in output


def test_eof_cancels_unfinished_operation(tmp_path):
    path = tmp_path / "inventory.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--data", str(path)],
        input="2\nМолоко\n", text=True, capture_output=True, timeout=10,
    )
    assert result.returncode == 0
    assert "Ввод прерван" in result.stdout
    assert not path.exists()
