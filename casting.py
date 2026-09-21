"""Функции подбора актёров на роли."""


def can_cast_actor(
    actor_gender: str,
    actor_age: int,
    role_gender: str,
    role_min_age: int,
    role_max_age: int,
) -> str:
    """Проверить соответствие актёра роли по полу и возрасту."""
    if actor_gender != role_gender:
        return "Актёр не подходит на роль: не совпадает пол"
    if actor_age < role_min_age:
        return (
            "Актёр не подходит на роль: "
            "не достиг минимального возраста роли"
        )
    if actor_age > role_max_age:
        return "Актёр не подходит на роль: превышает максимальный возраст роли"
    return "Актёр подходит на роль по полу и возрасту"


def find_suitable_actors(actors: list[dict], role: dict) -> list[dict]:
    """Вернуть список актёров, подходящих под требования роли."""
    return [
        actor
        for actor in actors
        if actor["gender"] == role["required_gender"]
        and role["min_age"] <= actor["age"] <= role["max_age"]
    ]
