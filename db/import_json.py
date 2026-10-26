"""Импорт JSON в SQLite."""

import argparse

from storage import load_project

from .database import BASE_DIR, DEFAULT_PATH, connect, initialize_database


def import_json(
    directory=BASE_DIR / "data", path=DEFAULT_PATH, *, replace=False,
):
    data = load_project(directory)
    initialize_database(path)
    groups = {
        "productions": [item.to_data() for item in data.productions],
        "actors": [item.to_data() for item in data.actors],
        "roles": [item.to_data() for item in data.roles],
        "shows": [item.to_data() for item in data.shows],
        "bookings": [item.to_data() for item in data.bookings],
    }
    with connect(path) as conn:
        populated = any(
            conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
            for table in groups
        )
        if populated and not replace:
            raise ValueError(
                "База уже содержит данные. Для повторного импорта "
                "явно укажите --replace."
            )
        if replace:
            for table in reversed(groups):
                conn.execute("DELETE FROM " + table)
        for table, rows in groups.items():
            if not rows:
                continue
            columns = list(rows[0])
            # Имена полей заданы моделями.
            placeholders = ", ".join("?" for _ in columns)
            statement = (
                "INSERT INTO " + table + " (" + ", ".join(columns)
                + ") VALUES (" + placeholders + ")"
            )
            conn.executemany(statement, [
                tuple(row[column] for column in columns) for row in rows
            ])
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Нарушены внешние ключи")
    return {name: len(rows) for name, rows in groups.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=BASE_DIR / "data")
    parser.add_argument("--database", default=DEFAULT_PATH)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    try:
        counts = import_json(
            args.data_dir, args.database, replace=args.replace,
        )
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + "\n")
    for table, count in counts.items():
        print(f"{table}: {count}")


if __name__ == "__main__":
    main()
