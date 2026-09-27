"""Исполняемый прототип БД для ПР3: схема, импорт, проверки и SQL-отчёты.

Консольная версия main.py продолжает работать с JSON. Этот модуль готовит
реляционное хранилище для следующего этапа разработки монолита.
"""

import argparse
import json
import sqlite3
from contextlib import closing
from decimal import Decimal, InvalidOperation
from pathlib import Path

from storage import load_json

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = PROJECT_DIR / "data" / "theatre.sqlite3"
SCHEMA_FILE = PROJECT_DIR / "sql" / "schema.sql"
SCHEMA_VERSION = 1
DATA_TABLES = (
    "productions", "actors", "roles", "cast_assignments", "halls",
    "shows", "bookings",
)
SEAT_LOOKUP_SQL = (
    "SELECT id FROM bookings WHERE show_id = ? AND seat_number = ?"
)
SHOWS_LOOKUP_SQL = (
    "SELECT id, starts_at FROM shows "
    "WHERE production_id = ? ORDER BY starts_at"
)


def connect_database(
    filename: str | Path = DEFAULT_DATABASE,
    *,
    read_only: bool = False,
) -> sqlite3.Connection:
    """Открыть соединение с внешними ключами; вызывающий закрывает его.

    Новый файл создаётся с правами 0600 (на POSIX). Режим read_only не
    создаёт отсутствующую базу и запрещает запись средствами SQLite.
    """
    if sqlite3.sqlite_version_info < (3, 37, 0):
        raise RuntimeError("Для таблиц STRICT требуется SQLite 3.37+")
    path = Path(filename).resolve()
    if not read_only:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.touch(mode=0o600, exist_ok=False)
        except FileExistsError:
            pass
    mode = "ro" if read_only else "rw"
    connection = sqlite3.connect(
        f"{path.as_uri()}?mode={mode}", uri=True, timeout=5.0,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    """Создать схему один раз, не перезаписывая существующие данные."""
    if connection.in_transaction:
        raise ValueError("Инициализация требует отдельной транзакции")
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version == SCHEMA_VERSION:
        return
    if version != 0:
        raise ValueError(f"Неподдерживаемая версия схемы: {version}")
    existing = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchone()
    if existing:
        raise ValueError("База уже содержит таблицы без версии схемы")
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    try:
        connection.executescript(
            "BEGIN IMMEDIATE;\n" + schema
            + f"\nPRAGMA user_version = {SCHEMA_VERSION};\nCOMMIT;"
        )
    except sqlite3.Error:
        connection.rollback()
        raise


def _money_to_kopecks(value: object) -> int:
    """Перенести сохранённую цену без пересчёта тарифов и потери копеек."""
    try:
        amount = Decimal(str(value)) * 100
    except InvalidOperation as error:
        raise ValueError("Цена должна быть числом") from error
    if not amount.is_finite() or not 0 <= amount <= 2**63 - 1:
        raise ValueError("Цена вне допустимого диапазона")
    if amount != amount.to_integral_value():
        raise ValueError("Цена должна содержать не более двух знаков дроби")
    return int(amount)


def import_json_data(
    connection: sqlite3.Connection,
    source_dir: str | Path,
) -> dict[str, int]:
    """Атомарно импортировать все пять JSON-файлов в пустую схему.

    Ошибка в любой записи откатывает весь импорт. Повторный импорт в
    заполненную базу запрещён; исходные файлы никогда не изменяются.
    """
    if connection.in_transaction:
        raise ValueError("Импорт требует отдельной транзакции")
    source_dir = Path(source_dir)
    data = {}
    for name in ("productions", "actors", "roles", "shows", "bookings"):
        path = source_dir / f"{name}.json"
        if not path.is_file():
            raise ValueError(f"Отсутствует обязательный файл: {path}")
        records = load_json(path)
        if not all(isinstance(record, dict) for record in records):
            raise ValueError(f"Ожидался список объектов в {path}")
        data[name] = records

    with connection:
        connection.execute("BEGIN IMMEDIATE")
        if any(
            connection.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
            for table in DATA_TABLES
        ):
            raise ValueError("Импорт разрешён только в пустую базу")
        # Имена таблиц выше взяты только из константы, значения ниже —
        # только через параметры. Пользовательский текст не становится SQL.
        for item in data["productions"]:
            connection.execute(
                "INSERT INTO productions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (item["id"], item["title"], item["author"], item["genre"],
                 item["premiere_date"], item["rehearsals_done"],
                 item["costumes_ready"], item["scenery_ready"]),
            )
        for item in data["actors"]:
            connection.execute(
                "INSERT INTO actors VALUES (?, ?, ?, ?)",
                (item["id"], item["name"], item["gender"], item["age"]),
            )
        for item in data["roles"]:
            connection.execute(
                "INSERT INTO roles VALUES (?, ?, ?, ?, ?, ?)",
                (item["id"], item["production_id"], item["title"],
                 item["required_gender"], item["min_age"], item["max_age"]),
            )
        for item in data["shows"]:
            hall_name = item["hall"].strip()
            hall = connection.execute(
                "SELECT id, capacity FROM halls WHERE name = ?",
                (hall_name,),
            ).fetchone()
            if hall is None:
                cursor = connection.execute(
                    "INSERT INTO halls (name, capacity) VALUES (?, ?)",
                    (hall_name, item["capacity"]),
                )
                hall_id = cursor.lastrowid
            else:
                if hall["capacity"] != item["capacity"]:
                    raise ValueError(
                        f"Разная вместимость одного зала: {hall_name}"
                    )
                hall_id = hall["id"]
            connection.execute(
                "INSERT INTO shows VALUES (?, ?, ?, ?)",
                (item["id"], item["production_id"], hall_id,
                 item["datetime"]),
            )
        for item in data["bookings"]:
            connection.execute(
                "INSERT INTO bookings "
                "(id, show_id, seat_number, zone_id, category_code, "
                "price_kopecks) VALUES (?, ?, ?, ?, ?, ?)",
                (item["id"], item["show_id"], item["seat_number"],
                 item["zone"], item["category"],
                 _money_to_kopecks(item["price"])),
            )
        counts = {
            table: connection.execute(
                f"SELECT count(*) FROM {table}"
            ).fetchone()[0]
            for table in DATA_TABLES
        }
    return counts


def check_database(connection: sqlite3.Connection) -> dict:
    """Проверить версию, физическую целостность и внешние ключи."""
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    integrity = [
        row[0] for row in connection.execute("PRAGMA integrity_check")
    ]
    foreign_keys = [
        tuple(row) for row in connection.execute("PRAGMA foreign_key_check")
    ]
    return {
        "ok": version == SCHEMA_VERSION
        and integrity == ["ok"] and not foreign_keys,
        "schema_version": version,
        "integrity": integrity,
        "foreign_key_errors": foreign_keys,
    }


def booking_statistics(connection: sqlite3.Connection) -> list[dict]:
    """Получить сводку по всем показам, включая показы без бронирований."""
    return [dict(row) for row in connection.execute(
        "SELECT * FROM show_booking_statistics ORDER BY starts_at, show_id"
    )]


def query_plans(connection: sqlite3.Connection) -> dict[str, list[str]]:
    """Показать использование индексов для двух типичных запросов."""
    queries = {
        "seat_lookup": (SEAT_LOOKUP_SQL, (1, 15)),
        "shows_by_production": (SHOWS_LOOKUP_SQL, (1,)),
    }
    return {
        name: [row[3] for row in connection.execute(
            "EXPLAIN QUERY PLAN " + sql, parameters
        )]
        for name, (sql, parameters) in queries.items()
    }


def main(argv: list[str] | None = None) -> int:
    """Запустить утилиту БД; ошибки возвращают ненулевой код завершения."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DATABASE)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Создать схему БД")
    init.add_argument("--import-json", type=Path, metavar="DIRECTORY")
    commands.add_parser("check", help="Проверить целостность")
    commands.add_parser("stats", help="Сводка по показам, суммы в копейках")
    commands.add_parser("explain", help="Показать планы запросов")
    args = parser.parse_args(argv)
    try:
        with closing(connect_database(
            args.db, read_only=args.command != "init",
        )) as connection:
            if args.command == "init":
                initialize_database(connection)
                result = {"database": str(args.db), "schema_version": 1}
                if args.import_json is not None:
                    result["imported"] = import_json_data(
                        connection, args.import_json,
                    )
            elif args.command == "check":
                result = check_database(connection)
            elif args.command == "stats":
                result = booking_statistics(connection)
            else:
                result = query_plans(connection)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if args.command == "check" and not result["ok"]:
                return 1
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError,
            AttributeError, OverflowError, RuntimeError) as error:
        parser.exit(1, f"Ошибка базы данных: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
