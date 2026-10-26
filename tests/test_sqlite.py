import json
import shutil
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from django.test import Client, override_settings
from django.test.utils import setup_test_environment, teardown_test_environment

from db.database import QUERIES, connect, fetch
from db.import_json import import_json

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def sql_data(tmp_path):
    source = tmp_path / "json"
    source.mkdir()
    for path in DATA_DIR.glob("*.json"):
        shutil.copy(path, source / path.name)
    database = tmp_path / "theatre.sqlite"
    counts = import_json(source, database)
    assert counts == {
        "productions": 2, "actors": 3, "roles": 2,
        "shows": 2, "bookings": 1,
    }
    with override_settings(
        DATA_SOURCE="sqlite", SQLITE_PATH=database, DATA_DIR=source,
    ):
        yield source, database


def test_all_queries_execute_on_imported_data(sql_data):
    _, database = sql_data
    parameters = {
        "productions_by_genre": ("комедия",), "bookings_by_status": (0,),
        "booking_detail": (1,), "popular_productions": (0,),
        "available_shows": ("2026-10-20",), "suitable_actors": (1,),
    }
    with connect(database) as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert not conn.execute("PRAGMA foreign_key_check").fetchall()
        assert len(QUERIES) == 16
        for name in QUERIES:
            rows = fetch(conn, name, parameters.get(name, ()))
            assert all(isinstance(row, sqlite3.Row) for row in rows)
        assert fetch(conn, "available_shows", ("2026-10-20",))[0][
            "available"
        ] == 119
        assert fetch(conn, "booking_statistics")[0]["revenue"] == 1800


@pytest.mark.parametrize("url", [
    "/", "/productions/", "/productions/1/", "/shows/", "/shows/1/",
    "/bookings/", "/bookings/1/", "/shows/available/?date=2026-10-20",
    "/statistics/", "/productions/?genre=комедия",
    "/bookings/?status=active", "/bookings/?status=cancelled",
])
def test_pages_read_sqlite_without_loading_json(url, sql_data):
    source, database = sql_data
    for path in source.glob("*.json"):
        path.write_text("{")
    before = database.read_bytes()
    with patch("homepage.data.load_project", side_effect=AssertionError):
        response = Client().get(url)
    assert response.status_code == 200
    assert database.read_bytes() == before
    assert "<html lang=\"ru\">" in response.content.decode()


def test_filters_and_sql_parameters(sql_data):
    client = Client()
    content = client.get("/productions/?genre=комедия").content.decode()
    assert "Ревизор" in content
    assert "Вишнёвый сад" not in content
    assert "Вишнёвый сад" in client.get(
        "/bookings/?status=active",
    ).content.decode()
    assert "Бронирований пока нет" in client.get(
        "/bookings/?status=cancelled",
    ).content.decode()
    assert "119 из 120" in client.get(
        "/shows/available/?date=2026-10-20",
    ).content.decode()
    assert "Подходящих показов пока нет" in client.get(
        "/shows/available/?date=2026-10-21",
    ).content.decode()
    response = client.get("/productions/", {"genre": "' OR 1=1 --"})
    assert "Постановок пока нет" in response.content.decode()
    assert client.get("/productions/").status_code == 200


def test_cancelled_bookings_and_group_counts(sql_data):
    _, database = sql_data
    with connect(database) as conn:
        conn.execute("UPDATE bookings SET is_cancelled = 1 WHERE id = 1")
        conn.execute("""
            INSERT INTO bookings VALUES (2, 1, 15, 2, 'полный', 2000, 0)
        """)
        conn.execute("""
            INSERT INTO bookings VALUES (3, 1, 16, 2, 'льготный', 1400, 0)
        """)
        row = fetch(conn, "production_statistics")[0]
        assert (row["show_count"], row["booking_count"]) == (1, 2)
        assert row["revenue"] == 3400
        assert fetch(conn, "hall_statistics")[0]["show_count"] == 2
        assert fetch(conn, "booking_statistics")[0]["cancelled_count"] == 1
    content = Client().get("/bookings/1/").content.decode()
    assert "Отменено" in content and "1800.00 руб." in content
    assert 'class="seat-count">118' in Client().get(
        "/shows/1/",
    ).content.decode()


def test_full_show_is_excluded_and_cancelled_seat_becomes_available(sql_data):
    _, database = sql_data
    with connect(database) as conn:
        conn.execute("UPDATE bookings SET seat_number = 1 WHERE id = 1")
        conn.execute("UPDATE shows SET capacity = 1 WHERE id = 1")
        assert not fetch(conn, "available_shows", ("2026-10-20",))
        conn.execute("UPDATE bookings SET is_cancelled = 1 WHERE id = 1")
        assert fetch(conn, "available_shows", ("2026-10-20",))[0][
            "available"
        ] == 1


@pytest.mark.parametrize("statement", [
    "INSERT INTO roles VALUES (99, 999, 'Роль', 'м', 20, 30)",
    "INSERT INTO bookings VALUES (99, 1, 15, 2, 'полный', 1800, 0)",
    "INSERT INTO bookings VALUES (99, 1, 121, 2, 'полный', 1800, 0)",
    "UPDATE bookings SET seat_number = 121 WHERE id = 1",
])
def test_database_constraints(statement, sql_data):
    _, database = sql_data
    with pytest.raises(sqlite3.IntegrityError), connect(database) as conn:
        conn.execute(statement)


def test_repeat_import_and_failed_replace_are_safe(sql_data):
    source, database = sql_data
    with pytest.raises(ValueError, match="--replace"):
        import_json(source, database)
    import_json(source, database, replace=True)
    rows = json.loads((source / "shows.json").read_text())
    rows[1]["datetime"] = rows[0]["datetime"]
    (source / "shows.json").write_text(json.dumps(rows))
    with pytest.raises(sqlite3.IntegrityError):
        import_json(source, database, replace=True)
    with connect(database) as conn:
        assert len(fetch(conn, "shows")) == 2
        assert len(fetch(conn, "bookings")) == 1
        assert fetch(conn, "shows")[1]["datetime"] == "2026-11-25T19:30"


@pytest.mark.parametrize("url", [
    "/shows/available/?date=bad", "/shows/available/?date=2026-02-30",
    "/bookings/?status=bad", "/statistics/?threshold=bad",
    "/statistics/?threshold=-1",
])
def test_invalid_search_parameters(url, sql_data):
    assert Client().get(url).status_code == 400


def test_templates_and_static_assets(sql_data):
    setup_test_environment()
    try:
        response = Client().get("/productions/")
        names = {template.name for template in response.templates}
        assert {"base.html", "includes/navigation.html",
                "includes/production_card.html"} <= names
        assert len(response.context["productions"]) == 2
        for asset in ("style.css", "theatre.svg", "main.js"):
            assert f"/static/homepage/{asset}" in response.content.decode()
    finally:
        teardown_test_environment()


def test_missing_database_returns_503_without_creating_file(tmp_path):
    path = tmp_path / "absent.sqlite"
    with override_settings(DATA_SOURCE="sqlite", SQLITE_PATH=path):
        response = Client().get("/productions/")
    assert response.status_code == 503
    assert str(path) not in response.content.decode()
    assert not path.exists()


def test_sqlite_content_is_escaped(sql_data):
    _, database = sql_data
    with connect(database) as conn:
        conn.execute("UPDATE productions SET title = ? WHERE id = 1",
                     ('<script>alert("x")</script>',))
    for url in ("/", "/productions/", "/productions/1/", "/shows/",
                "/bookings/", "/bookings/1/", "/statistics/"):
        content = Client().get(url).content.decode()
        assert '<script>alert("x")</script>' not in content
        assert "&lt;script&gt;" in content


def test_empty_sqlite_collections_and_zero_aggregates(sql_data):
    _, database = sql_data
    with connect(database) as conn:
        for table in ("bookings", "shows", "roles", "actors", "productions"):
            conn.execute("DELETE FROM " + table)
        assert fetch(conn, "booking_statistics")[0]["revenue"] == 0
    for url in ("/", "/productions/", "/shows/", "/bookings/",
                "/statistics/"):
        response = Client().get(url)
        assert response.status_code == 200
        assert "пока нет" in response.content.decode()
