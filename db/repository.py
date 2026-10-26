from models import Actor, Booking, Production, Role, Show
from storage import TheatreData

from .database import fetch


def production_from_row(row):
    values = dict(row)
    for field in ("rehearsals_done", "costumes_ready", "scenery_ready"):
        values[field] = bool(values[field])
    return Production.from_data(values)


def load_project(conn):
    productions = [
        production_from_row(row) for row in fetch(conn, "productions")
    ]
    actors = [Actor.from_data(dict(row)) for row in fetch(conn, "actors")]
    production_map = {item.id: item for item in productions}
    roles = [
        Role.from_data(dict(row), production_map[row["production_id"]])
        for row in fetch(conn, "roles")
    ]
    shows = [
        Show.from_data(dict(row), production_map[row["production_id"]])
        for row in fetch(conn, "shows")
    ]
    show_map = {item.id: item for item in shows}
    bookings = []
    for row in fetch(conn, "bookings"):
        values = dict(row)
        values["is_cancelled"] = bool(values["is_cancelled"])
        bookings.append(Booking.from_data(values, show_map[row["show_id"]]))
    return TheatreData(productions, actors, roles, shows, bookings)
