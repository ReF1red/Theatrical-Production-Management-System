"""Функции работы с показами спектаклей."""

from datetime import datetime


def add_show(
    shows: list[dict],
    production_id: int,
    show_datetime: datetime,
    hall: str,
    capacity: int,
) -> dict:
    """Добавить показ постановки."""
    if capacity <= 0:
        raise ValueError("Вместимость должна быть положительной")
    next_id = max((item["id"] for item in shows), default=0) + 1
    show = {
        "id": next_id,
        "production_id": production_id,
        "datetime": show_datetime.isoformat(timespec="minutes"),
        "hall": hall.strip(),
        "capacity": capacity,
    }
    shows.append(show)
    return show


def get_show_by_id(shows: list[dict], show_id: int) -> dict | None:
    """Найти показ по идентификатору."""
    for show in shows:
        if show["id"] == show_id:
            return show
    return None


def sort_shows(shows: list[dict]) -> list[dict]:
    """Вернуть показы, отсортированные по дате и времени."""
    return sorted(shows, key=lambda item: item["datetime"])
