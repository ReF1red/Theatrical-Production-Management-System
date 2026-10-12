from models.casting import can_cast_actor, find_suitable_actors
from models import Actor, Role


def test_actor_matches_role():
    result = can_cast_actor("ж", 34, "ж", 30, 45)
    assert result == "Актёр подходит на роль по полу и возрасту"


def test_find_suitable_actors(production):
    actors = [
        Actor(1, "Анна", "ж", 34),
        Actor(2, "Пётр", "м", 40),
    ]
    role = Role(1, production, "Офелия", "ж", 30, 45)
    result = find_suitable_actors(actors, role)
    assert [actor.name for actor in result] == ["Анна"]
