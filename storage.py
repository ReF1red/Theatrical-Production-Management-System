"""Данные в JSON."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable, TypeVar

from models import Actor, Booking, Production, Role, Show
from models.validation import require_int

T = TypeVar("T")


@dataclass
class TheatreData:
    """Данные театра."""

    productions: list[Production]
    actors: list[Actor]
    roles: list[Role]
    shows: list[Show]
    bookings: list[Booking]


def load_json(filename: str | Path) -> list[dict]:
    path = Path(filename)
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError(f"Некорректный JSON в файле {path}") from error

    if not isinstance(data, list):
        raise ValueError(f"Ожидался список в файле {path}")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError(f"Ожидался список объектов в файле {path}")
    return data


def save_json(filename: str | Path, data: list[dict]) -> None:
    """Сначала пишем временный файл."""
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False,
        ) as file:
            temporary = Path(file.name)
            json.dump(
                data, file, ensure_ascii=False, indent=2, allow_nan=False,
            )
            file.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _load_objects(
    filename: str | Path, factory: Callable[[dict], T],
) -> list[T]:
    objects = []
    identifiers = set()
    for index, row in enumerate(load_json(filename), 1):
        try:
            item = factory(row)
            if item.id in identifiers:
                raise ValueError(f"Повторный ID {item.id}")
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                f"Некорректная запись {index} в {filename}: {error}"
            ) from error
        identifiers.add(item.id)
        objects.append(item)
    return objects


def load_productions(filename: str | Path) -> list[Production]:
    return _load_objects(filename, Production.from_data)


def save_productions(filename: str | Path, items: list[Production]) -> None:
    save_json(filename, [item.to_data() for item in items])


def load_actors(filename: str | Path) -> list[Actor]:
    return _load_objects(filename, Actor.from_data)


def save_actors(filename: str | Path, items: list[Actor]) -> None:
    save_json(filename, [item.to_data() for item in items])


def load_roles(
    filename: str | Path, productions: list[Production],
) -> list[Role]:
    related = {item.id: item for item in productions}
    return _load_objects(
        filename,
        lambda row: Role.from_data(
            row, related[require_int(row["production_id"], "ID постановки")],
        ),
    )


def save_roles(filename: str | Path, items: list[Role]) -> None:
    save_json(filename, [item.to_data() for item in items])


def load_shows(
    filename: str | Path, productions: list[Production],
) -> list[Show]:
    related = {item.id: item for item in productions}
    return _load_objects(
        filename,
        lambda row: Show.from_data(
            row, related[require_int(row["production_id"], "ID постановки")],
        ),
    )


def save_shows(filename: str | Path, items: list[Show]) -> None:
    save_json(filename, [item.to_data() for item in items])


def load_bookings(filename: str | Path, shows: list[Show]) -> list[Booking]:
    related = {item.id: item for item in shows}
    bookings = _load_objects(
        filename, lambda row: Booking.from_data(
            row, related[require_int(row["show_id"], "ID показа")],
        ),
    )
    occupied = set()
    for item in bookings:
        if item.is_cancelled:
            continue
        seat = (item.show.id, item.seat_number)
        if seat in occupied:
            raise ValueError(f"Двойное бронирование места {seat} в {filename}")
        occupied.add(seat)
    return bookings


def save_bookings(filename: str | Path, items: list[Booking]) -> None:
    save_json(filename, [item.to_data() for item in items])


def load_project(directory: str | Path) -> TheatreData:
    """Загружаем связанные данные по порядку."""
    directory = Path(directory)
    productions = load_productions(directory / "productions.json")
    actors = load_actors(directory / "actors.json")
    roles = load_roles(directory / "roles.json", productions)
    shows = load_shows(directory / "shows.json", productions)
    bookings = load_bookings(directory / "bookings.json", shows)
    return TheatreData(productions, actors, roles, shows, bookings)
