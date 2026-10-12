from datetime import date
from typing import Iterator

from .validation import require_bool, require_int, require_text


def get_production_status(
    rehearsals_done: bool,
    costumes_done: bool,
    scenery_done: bool,
) -> str:
    if not rehearsals_done:
        return "Идут репетиции"
    if not costumes_done or not scenery_done:
        return "Репетиции окончены, идёт оформление спектакля"
    return "Постановка готова к выпуску на сцену"


class Production:
    """Постановка."""

    def __init__(
        self,
        production_id: int,
        title: str,
        author: str,
        genre: str,
        premiere_date: date,
        rehearsals_done: bool = False,
        costumes_ready: bool = False,
        scenery_ready: bool = False,
    ) -> None:
        self.id = require_int(production_id, "ID постановки")
        self.title = require_text(title, "Название")
        self.author = require_text(author, "Автор")
        self.genre = require_text(genre, "Жанр")
        if type(premiere_date) is not date:
            raise ValueError("Дата премьеры должна быть объектом date")
        self.premiere_date = premiere_date
        self.update_readiness(rehearsals_done, costumes_ready, scenery_ready)

    def update_readiness(
        self,
        rehearsals_done: bool,
        costumes_ready: bool,
        scenery_ready: bool,
    ) -> None:
        flags = [
            require_bool(rehearsals_done, "Репетиции"),
            require_bool(costumes_ready, "Костюмы"),
            require_bool(scenery_ready, "Декорации"),
        ]
        self.rehearsals_done, self.costumes_ready, self.scenery_ready = flags

    def get_status(self) -> str:
        return get_production_status(
            self.rehearsals_done, self.costumes_ready, self.scenery_ready,
        )

    def to_data(self) -> dict:
        return {
            "id": self.id, "title": self.title, "author": self.author,
            "genre": self.genre,
            "premiere_date": self.premiere_date.isoformat(),
            "rehearsals_done": self.rehearsals_done,
            "costumes_ready": self.costumes_ready,
            "scenery_ready": self.scenery_ready,
        }

    @classmethod
    def from_data(cls, data: dict) -> "Production":
        return cls(
            data["id"], data["title"], data["author"], data["genre"],
            date.fromisoformat(data["premiere_date"]),
            data["rehearsals_done"], data["costumes_ready"],
            data["scenery_ready"],
        )

    def __str__(self) -> str:
        return (
            f"{self.id}. «{self.title}» — {self.author}, {self.genre}; "
            f"премьера {self.premiere_date}; {self.get_status()}"
        )


def add_production(
    productions: list[Production],
    title: str,
    author: str,
    genre: str,
    premiere_date: date,
) -> Production:
    next_id = max((item.id for item in productions), default=0) + 1
    production = Production(next_id, title, author, genre, premiere_date)
    productions.append(production)
    return production


def get_production_by_id(
    productions: list[Production], production_id: int,
) -> Production | None:
    return next(
        (item for item in productions if item.id == production_id), None,
    )


def find_productions(
    productions: list[Production], query: str,
) -> list[Production]:
    query = query.strip().casefold()
    return [
        item for item in productions
        if any(query in text.casefold()
               for text in (item.title, item.author, item.genre))
    ]


def iter_productions_by_genre(
    productions: list[Production], genre: str,
) -> Iterator[Production]:
    for item in productions:
        if item.genre.casefold() == genre.strip().casefold():
            yield item


def sort_productions(
    productions: list[Production], key: str = "premiere_date",
) -> list[Production]:
    if key not in {"title", "author", "genre", "premiere_date"}:
        raise ValueError("Недопустимое поле сортировки")
    return sorted(
        productions, key=lambda item: str(getattr(item, key)).lower(),
    )


def update_readiness(
    productions: list[Production],
    production_id: int,
    rehearsals_done: bool,
    costumes_ready: bool,
    scenery_ready: bool,
) -> bool:
    production = get_production_by_id(productions, production_id)
    if production is None:
        return False
    production.update_readiness(rehearsals_done, costumes_ready, scenery_ready)
    return True
