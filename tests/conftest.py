from datetime import date, datetime

import pytest

from models import Production, Show


@pytest.fixture
def production():
    return Production(1, "Гамлет", "У. Шекспир", "трагедия", date(2027, 1, 20))


@pytest.fixture
def show(production):
    return Show(1, production, datetime(2027, 1, 20, 19), "Большой зал", 120)
