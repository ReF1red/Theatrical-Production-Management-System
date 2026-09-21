from datetime import date

from productions import (
    add_production,
    find_productions,
    get_production_status,
    sort_productions,
)


def test_get_production_status_in_progress():
    status = get_production_status(True, True, False)
    assert status == "Репетиции окончены, идёт оформление спектакля"


def test_add_and_find_production():
    productions = []
    add_production(
        productions,
        "Гамлет",
        "У. Шекспир",
        "трагедия",
        date(2027, 1, 20),
    )
    assert find_productions(productions, "шекспир")


def test_sort_productions_by_premiere_date():
    productions = [
        {"title": "Б", "premiere_date": "2027-02-01"},
        {"title": "А", "premiere_date": "2026-12-01"},
    ]
    result = sort_productions(productions)
    assert result[0]["title"] == "А"
