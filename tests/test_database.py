"""Проверки реляционной модели и безопасного переноса данных ПР2."""

import json
import sqlite3
from contextlib import closing

import pytest

from database import (
    DATA_TABLES,
    booking_statistics,
    check_database,
    connect_database,
    import_json_data,
    initialize_database,
    main,
    query_plans,
)


@pytest.fixture
def source_dir(tmp_path):
    source = tmp_path / "json"
    source.mkdir()
    records = {
        "productions": [{
            "id": 7, "title": "Вишнёвый сад", "author": "А. П. Чехов",
            "genre": "драма", "premiere_date": "2026-10-15",
            "rehearsals_done": True, "costumes_ready": True,
            "scenery_ready": False,
        }],
        "actors": [{"id": 3, "name": "Анна", "gender": "ж", "age": 34}],
        "roles": [{
            "id": 5, "production_id": 7, "title": "Раневская",
            "required_gender": "ж", "min_age": 30, "max_age": 45,
        }],
        "shows": [
            {"id": 2, "production_id": 7, "datetime": "2026-10-20T19:00",
             "hall": "Большой зал", "capacity": 120},
            {"id": 4, "production_id": 7, "datetime": "2026-10-21T19:00",
             "hall": "Большой зал", "capacity": 120},
        ],
        "bookings": [{
            "id": 8, "show_id": 2, "seat_number": 15, "zone": 2,
            "category": "полный", "price": 1800.01,
        }],
    }
    for name, items in records.items():
        (source / f"{name}.json").write_text(
            json.dumps(items, ensure_ascii=False), encoding="utf-8",
        )
    return source


@pytest.fixture
def empty_db(tmp_path):
    with closing(connect_database(tmp_path / "theatre.sqlite3")) as conn:
        initialize_database(conn)
        yield conn


@pytest.fixture
def populated_db(empty_db, source_dir):
    import_json_data(empty_db, source_dir)
    return empty_db


def change_source(source_dir, name, field, value, index=0):
    path = source_dir / f"{name}.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    records[index][field] = value
    path.write_text(json.dumps(records), encoding="utf-8")


def test_import_preserves_data_and_normalizes_halls(empty_db, source_dir):
    original = {path: path.read_bytes() for path in source_dir.iterdir()}
    counts = import_json_data(empty_db, source_dir)
    assert counts == {
        "productions": 1, "actors": 1, "roles": 1, "cast_assignments": 0,
        "halls": 1, "shows": 2, "bookings": 1,
    }
    booking = empty_db.execute("SELECT * FROM bookings").fetchone()
    assert dict(booking) == {
        "id": 8, "show_id": 2, "seat_number": 15, "zone_id": 2,
        "category_code": "полный", "price_kopecks": 180001,
    }
    assert empty_db.execute("SELECT id FROM productions").fetchone()[0] == 7
    assert all(path.read_bytes() == value for path, value in original.items())
    assert check_database(empty_db)["ok"]


def test_initialization_is_idempotent_and_import_cannot_overwrite(
    populated_db, source_dir,
):
    before = booking_statistics(populated_db)
    initialize_database(populated_db)
    with pytest.raises(ValueError, match="пустую базу"):
        import_json_data(populated_db, source_dir)
    assert booking_statistics(populated_db) == before


@pytest.mark.parametrize("table, field, value, error", [
    ("bookings", "show_id", 999, sqlite3.IntegrityError),
    ("bookings", "price", 1.234, ValueError),
    ("bookings", "price", "NaN", ValueError),
    ("bookings", "price", -1, ValueError),
    ("bookings", "seat_number", 121, sqlite3.IntegrityError),
    ("shows", "capacity", 110, ValueError),
    ("roles", "max_age", 20, sqlite3.IntegrityError),
    ("productions", "premiere_date", "2026-02-30", sqlite3.IntegrityError),
])
def test_failed_import_rolls_back_every_table(
    empty_db, source_dir, table, field, value, error,
):
    change_source(source_dir, table, field, value)
    with pytest.raises(error):
        import_json_data(empty_db, source_dir)
    for name in DATA_TABLES:
        count = empty_db.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        assert count == 0
    assert not empty_db.in_transaction
    assert check_database(empty_db)["ok"]


def test_missing_source_file_does_not_become_empty_data(empty_db, source_dir):
    (source_dir / "actors.json").unlink()
    with pytest.raises(ValueError, match="Отсутствует обязательный файл"):
        import_json_data(empty_db, source_dir)
    count = empty_db.execute("SELECT count(*) FROM productions").fetchone()[0]
    assert count == 0


@pytest.mark.parametrize("statement", [
    "UPDATE bookings SET seat_number = 121",
    "UPDATE bookings SET seat_number = 1.5",
    "UPDATE bookings SET seat_number = 0",
    "UPDATE bookings SET show_id = 999",
    "UPDATE bookings SET zone_id = 10",
    "UPDATE bookings SET category_code = 'неизвестная'",
    "UPDATE bookings SET price_kopecks = -1",
    "UPDATE halls SET capacity = 14",
    "UPDATE halls SET capacity = 0",
    "UPDATE productions SET title = ' '",
    "UPDATE productions SET rehearsals_done = 2",
    "UPDATE productions SET premiere_date = '2026-02-30'",
    "UPDATE productions SET premiere_date = 'не дата'",
    "UPDATE actors SET age = -1",
    "UPDATE roles SET min_age = 46",
    "UPDATE shows SET starts_at = '2026-02-30T19:00'",
    "UPDATE shows SET starts_at = '2026-10-21T25:00'",
    "UPDATE shows SET starts_at = '2026-10-20T19:00' WHERE id = 4",
    "DELETE FROM shows WHERE id = 2",
    "DELETE FROM productions WHERE id = 7",
    "DELETE FROM ticket_zones WHERE id = 2",
])
def test_database_rejects_invalid_writes(populated_db, statement):
    with pytest.raises(sqlite3.IntegrityError):
        with populated_db:
            populated_db.execute(statement)
    assert check_database(populated_db)["ok"]


def test_duplicate_seat_is_forbidden_even_in_another_zone(populated_db):
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        populated_db.execute(
            "INSERT INTO bookings "
            "(show_id, seat_number, zone_id, category_code, price_kopecks) "
            "VALUES (2, 15, 3, 'льготный', 73500)"
        )
    populated_db.rollback()
    with populated_db:
        populated_db.execute(
            "INSERT INTO bookings "
            "(show_id, seat_number, zone_id, category_code, price_kopecks) "
            "VALUES (4, 15, 3, 'льготный', 73500)"
        )
    assert booking_statistics(populated_db)[1]["booking_count"] == 1


def test_show_and_booking_cannot_move_to_smaller_hall(populated_db):
    with populated_db:
        populated_db.execute(
            "INSERT INTO halls VALUES (2, 'Малый зал', 10)"
        )
        populated_db.execute(
            "INSERT INTO shows VALUES (6, 7, 2, '2026-10-22T19:00')"
        )
    with pytest.raises(sqlite3.IntegrityError, match="недостаточно мест"):
        with populated_db:
            populated_db.execute("UPDATE shows SET hall_id = 2 WHERE id = 2")
    with pytest.raises(sqlite3.IntegrityError, match="вместимость"):
        with populated_db:
            populated_db.execute("UPDATE bookings SET show_id = 6")


def test_statistics_include_empty_shows_and_exact_revenue(populated_db):
    rows = booking_statistics(populated_db)
    assert rows[0]["booking_count"] == 1
    assert rows[0]["revenue_kopecks"] == 180001
    assert rows[0]["available_seats"] == 119
    assert rows[1]["booking_count"] == 0
    assert rows[1]["revenue_kopecks"] == 0
    assert rows[1]["discount_count"] == 0
    assert rows[1]["available_seats"] == 120


def test_parameterized_import_treats_sql_as_text(empty_db, source_dir):
    title = "Спектакль'); DROP TABLE actors; --"
    change_source(source_dir, "productions", "title", title)
    import_json_data(empty_db, source_dir)
    saved = empty_db.execute("SELECT title FROM productions").fetchone()[0]
    assert saved == title
    assert empty_db.execute("SELECT count(*) FROM actors").fetchone()[0] == 1


def test_query_plans_use_indexes(populated_db):
    plans = query_plans(populated_db)
    assert any(
        "SEARCH bookings USING" in line for line in plans["seat_lookup"]
    )
    assert any(
        "idx_shows_production_date" in line
        for line in plans["shows_by_production"]
    )


def test_two_connections_cannot_book_same_seat(populated_db, tmp_path):
    with closing(connect_database(tmp_path / "theatre.sqlite3")) as second:
        for conn in (populated_db, second):
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            lookup = conn.execute(
                "SELECT id FROM bookings "
                "WHERE show_id = 2 AND seat_number = 16"
            ).fetchone()
            assert lookup is None
        statement = (
            "INSERT INTO bookings "
            "(show_id, seat_number, zone_id, category_code, price_kopecks) "
            "VALUES (2, 16, 1, 'полный', 225000)"
        )
        with populated_db:
            populated_db.execute(statement)
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            with second:
                second.execute(statement)


def test_read_only_connection_rejects_changes(populated_db, tmp_path):
    with closing(connect_database(
        tmp_path / "theatre.sqlite3", read_only=True,
    )) as conn:
        assert check_database(conn)["ok"]
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("DELETE FROM bookings")


def test_cancelled_booking_id_is_not_reused(populated_db):
    with populated_db:
        populated_db.execute("DELETE FROM bookings WHERE id = 8")
        cursor = populated_db.execute(
            "INSERT INTO bookings "
            "(show_id, seat_number, zone_id, category_code, price_kopecks) "
            "VALUES (2, 15, 2, 'полный', 180000)"
        )
    assert cursor.lastrowid > 8


def test_cli_init_check_stats_and_explain(tmp_path, source_dir, capsys):
    args = ["--db", str(tmp_path / "cli.sqlite3")]
    assert main(args + ["init", "--import-json", str(source_dir)]) == 0
    assert json.loads(capsys.readouterr().out)["imported"]["bookings"] == 1
    assert main(args + ["check"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"]
    assert main(args + ["stats"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 2
    assert main(args + ["explain"]) == 0
    assert "seat_lookup" in json.loads(capsys.readouterr().out)


def test_cli_check_does_not_create_missing_database(tmp_path, capsys):
    path = tmp_path / "missing.sqlite3"
    with pytest.raises(SystemExit) as error:
        main(["--db", str(path), "check"])
    assert error.value.code == 1
    assert "Ошибка базы данных" in capsys.readouterr().err
    assert not path.exists()
