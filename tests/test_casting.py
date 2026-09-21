from casting import can_cast_actor, find_suitable_actors


def test_actor_matches_role():
    result = can_cast_actor("ж", 34, "ж", 30, 45)
    assert result == "Актёр подходит на роль по полу и возрасту"


def test_find_suitable_actors():
    actors = [
        {"name": "Анна", "gender": "ж", "age": 34},
        {"name": "Пётр", "gender": "м", "age": 40},
    ]
    role = {
        "required_gender": "ж",
        "min_age": 30,
        "max_age": 45,
    }
    result = find_suitable_actors(actors, role)
    assert [actor["name"] for actor in result] == ["Анна"]
