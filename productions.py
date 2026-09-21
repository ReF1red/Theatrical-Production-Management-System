"""Функции для работы с театральными постановками."""

from datetime import date
from typing import Iterator


def get_production_status(
    rehearsals_done: bool,
    costumes_done: bool,
    scenery_done: bool,
) -> str:
    """Определить этап подготовки постановки по степени готовности."""
    if not rehearsals_done:
        return "Идут репетиции"
    if not costumes_done or not scenery_done:
        return "Репетиции окончены, идёт оформление спектакля"
    return "Постановка готова к выпуску на сцену"


def add_production(
    productions: list[dict],
    title: str,
    author: str,
    genre: str,
    premiere_date: date,
) -> dict:
    """Добавить новую постановку и вернуть созданную запись."""
    next_id = max((item["id"] for item in productions), default=0) + 1
    production = {
        "id": next_id,
        "title": title.strip(),
        "author": author.strip(),
        "genre": genre.strip(),
        "premiere_date": premiere_date.isoformat(),
        "rehearsals_done": False,
        "costumes_ready": False,
        "scenery_ready": False,
    }
    productions.append(production)
    return production


def get_production_by_id(
    productions: list[dict],
    production_id: int,
) -> dict | None:
    """Найти постановку по идентификатору."""
    for production in productions:
        if production["id"] == production_id:
            return production
    return None


def find_productions(productions: list[dict], query: str) -> list[dict]:
    """Найти постановки по части названия, автора или жанра."""
    normalized_query = query.strip().lower()
    return [
        production
        for production in productions
        if normalized_query in production["title"].lower()
        or normalized_query in production["author"].lower()
        or normalized_query in production["genre"].lower()
    ]


def iter_productions_by_genre(
    productions: list[dict],
    genre: str,
) -> Iterator[dict]:
    """Последовательно выдавать постановки указанного жанра."""
    normalized_genre = genre.strip().lower()
    for production in productions:
        if production["genre"].lower() == normalized_genre:
            yield production


def sort_productions(
    productions: list[dict],
    key: str = "premiere_date",
) -> list[dict]:
    """Вернуть новый список постановок, отсортированный по выбранному полю."""
    allowed_keys = {"title", "author", "genre", "premiere_date"}
    if key not in allowed_keys:
        raise ValueError("Недопустимое поле сортировки")
    return sorted(productions, key=lambda item: str(item[key]).lower())


def update_readiness(
    productions: list[dict],
    production_id: int,
    rehearsals_done: bool,
    costumes_ready: bool,
    scenery_ready: bool,
) -> bool:
    """Обновить признаки готовности постановки."""
    production = get_production_by_id(productions, production_id)
    if production is None:
        return False
    production["rehearsals_done"] = rehearsals_done
    production["costumes_ready"] = costumes_ready
    production["scenery_ready"] = scenery_ready
    return True
