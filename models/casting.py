from __future__ import annotations

from .productions import Production
from .validation import require_int, require_text


def can_cast_actor(
    actor_gender: str,
    actor_age: int,
    role_gender: str,
    role_min_age: int,
    role_max_age: int,
) -> str:
    if actor_gender != role_gender:
        return "Актёр не подходит на роль: не совпадает пол"
    if actor_age < role_min_age:
        return (
            "Актёр не подходит на роль: не достиг минимального возраста роли"
        )
    if actor_age > role_max_age:
        return "Актёр не подходит на роль: превышает максимальный возраст роли"
    return "Актёр подходит на роль по полу и возрасту"


class Actor:
    """Актёр."""

    def __init__(
        self, actor_id: int, name: str, gender: str, age: int,
    ) -> None:
        self.id = require_int(actor_id, "ID актёра")
        self.name = require_text(name, "Имя актёра")
        if gender not in {"м", "ж"}:
            raise ValueError("Пол актёра должен быть 'м' или 'ж'")
        self.gender = gender
        self.age = require_int(age, "Возраст", 0, 120)

    def can_play(self, role: Role) -> bool:
        return (
            self.gender == role.required_gender
            and role.min_age <= self.age <= role.max_age
        )

    @classmethod
    def from_data(cls, data: dict) -> Actor:
        return cls(data["id"], data["name"], data["gender"], data["age"])

    def to_data(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "gender": self.gender, "age": self.age,
        }

    def __str__(self) -> str:
        return f"{self.id}. {self.name}, {self.age} лет ({self.gender})"


class Role:
    """Роль в постановке."""

    def __init__(
        self,
        role_id: int,
        production: Production,
        title: str,
        required_gender: str,
        min_age: int,
        max_age: int,
    ) -> None:
        self.id = require_int(role_id, "ID роли")
        if not isinstance(production, Production):
            raise ValueError("Для роли требуется существующая постановка")
        self.production = production
        self.title = require_text(title, "Название роли")
        if required_gender not in {"м", "ж"}:
            raise ValueError("Пол для роли должен быть 'м' или 'ж'")
        self.required_gender = required_gender
        self.min_age = require_int(min_age, "Минимальный возраст", 0, 120)
        self.max_age = require_int(
            max_age, "Максимальный возраст", min_age, 120,
        )

    def to_data(self) -> dict:
        return {
            "id": self.id, "production_id": self.production.id,
            "title": self.title, "required_gender": self.required_gender,
            "min_age": self.min_age, "max_age": self.max_age,
        }

    @classmethod
    def from_data(cls, data: dict, production: Production) -> Role:
        return cls(
            data["id"], production, data["title"], data["required_gender"],
            data["min_age"], data["max_age"],
        )

    def __str__(self) -> str:
        return (
            f"{self.id}. {self.title} («{self.production.title}»): "
            f"пол {self.required_gender}, "
            f"возраст {self.min_age}-{self.max_age}"
        )


def find_suitable_actors(actors: list[Actor], role: Role) -> list[Actor]:
    return [actor for actor in actors if actor.can_play(role)]
