from datetime import date

from models import Production
from models.productions import (
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
        Production(1, "Б", "Автор", "драма", date(2027, 2, 1)),
        Production(2, "А", "Автор", "драма", date(2026, 12, 1)),
    ]
    result = sort_productions(productions)
    assert result[0].title == "А"
