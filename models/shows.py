from datetime import datetime

from .productions import Production
from .validation import require_int, require_text


class Show:
    """Показ постановки."""

    def __init__(
        self,
        show_id: int,
        production: Production,
        show_datetime: datetime,
        hall: str,
        capacity: int,
    ) -> None:
        self.id = require_int(show_id, "ID показа")
        if not isinstance(production, Production):
            raise ValueError("Для показа требуется существующая постановка")
        self.production = production
        if not isinstance(show_datetime, datetime):
            raise ValueError("Дата и время должны быть объектом datetime")
        self.datetime = show_datetime
        self.hall = require_text(hall, "Название зала")
        self.capacity = require_int(capacity, "Вместимость")

    def has_seat(self, seat_number: int) -> bool:
        return (
            type(seat_number) is int
            and 1 <= seat_number <= self.capacity
        )

    def to_data(self) -> dict:
        return {
            "id": self.id, "production_id": self.production.id,
            "datetime": self.datetime.isoformat(timespec="minutes"),
            "hall": self.hall, "capacity": self.capacity,
        }

    @classmethod
    def from_data(cls, data: dict, production: Production) -> "Show":
        return cls(
            data["id"], production, datetime.fromisoformat(data["datetime"]),
            data["hall"], data["capacity"],
        )

    def __str__(self) -> str:
        return (
            f"{self.id}. «{self.production.title}» — "
            f"{self.datetime:%d.%m.%Y %H:%M}, {self.hall}, "
            f"мест: {self.capacity}"
        )


def add_show(
    shows: list[Show],
    production: Production,
    show_datetime: datetime,
    hall: str,
    capacity: int,
) -> Show:
    hall = require_text(hall, "Название зала")
    if any(item.hall == hall and item.datetime == show_datetime
           for item in shows):
        raise ValueError("В этом зале уже есть показ на указанное время")
    next_id = max((item.id for item in shows), default=0) + 1
    show = Show(next_id, production, show_datetime, hall, capacity)
    shows.append(show)
    return show


def get_show_by_id(shows: list[Show], show_id: int) -> Show | None:
    return next((item for item in shows if item.id == show_id), None)


def sort_shows(shows: list[Show]) -> list[Show]:
    return sorted(shows, key=lambda item: item.datetime)
