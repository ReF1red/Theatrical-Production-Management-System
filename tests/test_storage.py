import json
from pathlib import Path

import pytest

from models import Actor, Booking, Role
from storage import (
    load_bookings, load_json, load_project, load_productions, load_shows,
    save_actors, save_bookings, save_json, save_productions, save_roles,
    save_shows,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_pr2_data_loads_without_changing_files():
    before = {path: path.read_bytes() for path in DATA_DIR.glob("*.json")}
    data = load_project(DATA_DIR)
    assert data.bookings[0].show is data.shows[0]
    assert data.shows[0].production is data.productions[0]
    assert data.roles[0].production is data.productions[0]
    assert not data.bookings[0].is_cancelled
    assert before == {path: path.read_bytes() for path in before}


def test_round_trip_preserves_links_price_and_cancellation(
    tmp_path, production, show,
):
    booking = Booking(1, show, 15, 2, "льготный", price=999.99)
    booking.cancel()
    save_productions(tmp_path / "productions.json", [production])
    save_actors(tmp_path / "actors.json", [Actor(1, "Анна", "ж", 34)])
    save_roles(
        tmp_path / "roles.json", [Role(1, production, "Офелия", "ж", 30, 45)],
    )
    save_shows(tmp_path / "shows.json", [show])
    save_bookings(tmp_path / "bookings.json", [booking])
    loaded = load_project(tmp_path)
    assert loaded.bookings[0].show is loaded.shows[0]
    assert loaded.roles[0].production is loaded.productions[0]
    assert loaded.shows[0].production is loaded.productions[0]
    assert loaded.bookings[0].price == 999.99
    assert loaded.bookings[0].is_cancelled
    assert loaded.actors[0].name == "Анна"


def test_missing_relationship_is_rejected(tmp_path, show):
    path = tmp_path / "shows.json"
    save_shows(path, [show])
    with pytest.raises(ValueError, match="Некорректная запись"):
        load_shows(path, [])


def test_duplicate_id_is_rejected(tmp_path, production):
    path = tmp_path / "productions.json"
    save_productions(path, [production, production])
    with pytest.raises(ValueError, match="Повторный ID"):
        load_productions(path)


def test_duplicate_active_seat_is_rejected(tmp_path, show):
    path = tmp_path / "bookings.json"
    items = [
        Booking(1, show, 1, 1, "полный"), Booking(2, show, 1, 1, "полный"),
    ]
    save_bookings(path, items)
    with pytest.raises(ValueError, match="Двойное бронирование"):
        load_bookings(path, [show])
    items[0].cancel()
    save_bookings(path, items)
    assert len(load_bookings(path, [show])) == 2


@pytest.mark.parametrize("content", ['{}', '[1]', '[', '[{"id": 1}]'])
def test_malformed_data_is_rejected(tmp_path, content):
    path = tmp_path / "productions.json"
    path.write_text(content)
    with pytest.raises(ValueError):
        load_productions(path)


def test_failed_save_preserves_previous_file(tmp_path):
    path = tmp_path / "bookings.json"
    save_json(path, [{"id": 1}])
    with pytest.raises(TypeError):
        save_json(path, [{"bad": object()}])
    assert json.loads(path.read_text()) == [{"id": 1}]
    assert list(tmp_path.iterdir()) == [path]


def test_missing_file_means_empty_collection(tmp_path):
    assert load_json(tmp_path / "absent.json") == []
