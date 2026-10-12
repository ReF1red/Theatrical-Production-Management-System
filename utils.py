"""Ввод данных."""

from datetime import date, datetime


def input_int(
    prompt: str,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    while True:
        try:
            value = int(input(prompt))
            if min_value is not None and value < min_value:
                raise ValueError
            if max_value is not None and value > max_value:
                raise ValueError
            return value
        except ValueError:
            print("Введите корректное целое число.")


def input_date(prompt: str) -> date:
    while True:
        try:
            return datetime.strptime(input(prompt), "%d.%m.%Y").date()
        except ValueError:
            print("Введите дату в формате ДД.ММ.ГГГГ.")


def input_datetime(prompt: str) -> datetime:
    while True:
        try:
            return datetime.strptime(input(prompt), "%d.%m.%Y %H:%M")
        except ValueError:
            print("Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ.")


def input_yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"да", "д", "yes", "y"}:
            return True
        if answer in {"нет", "н", "no", "n"}:
            return False
        print("Введите 'да' или 'нет'.")
