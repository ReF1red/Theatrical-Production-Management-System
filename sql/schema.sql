PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS productions (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    author TEXT NOT NULL,
    genre TEXT NOT NULL,
    premiere_date TEXT NOT NULL,
    rehearsals_done INTEGER NOT NULL CHECK (rehearsals_done IN (0, 1)),
    costumes_ready INTEGER NOT NULL CHECK (costumes_ready IN (0, 1)),
    scenery_ready INTEGER NOT NULL CHECK (scenery_ready IN (0, 1))
);

CREATE TABLE IF NOT EXISTS actors (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL,
    gender TEXT NOT NULL CHECK (gender IN ('м', 'ж')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120)
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    production_id INTEGER NOT NULL REFERENCES productions(id),
    title TEXT NOT NULL,
    required_gender TEXT NOT NULL CHECK (required_gender IN ('м', 'ж')),
    min_age INTEGER NOT NULL CHECK (min_age BETWEEN 0 AND 120),
    max_age INTEGER NOT NULL CHECK (max_age BETWEEN min_age AND 120)
);

CREATE TABLE IF NOT EXISTS shows (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    production_id INTEGER NOT NULL REFERENCES productions(id),
    datetime TEXT NOT NULL,
    hall TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    UNIQUE (hall, datetime)
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    show_id INTEGER NOT NULL REFERENCES shows(id),
    seat_number INTEGER NOT NULL CHECK (seat_number > 0),
    zone INTEGER NOT NULL CHECK (zone IN (1, 2, 3)),
    category TEXT NOT NULL CHECK (category IN ('полный', 'льготный')),
    price REAL NOT NULL CHECK (price >= 0),
    is_cancelled INTEGER NOT NULL DEFAULT 0 CHECK (is_cancelled IN (0, 1))
);

-- Отмена освобождает место.
CREATE UNIQUE INDEX IF NOT EXISTS unique_active_seat
    ON bookings(show_id, seat_number) WHERE is_cancelled = 0;
CREATE INDEX IF NOT EXISTS shows_production ON shows(production_id);
CREATE INDEX IF NOT EXISTS roles_production ON roles(production_id);

CREATE TRIGGER IF NOT EXISTS booking_capacity_insert
BEFORE INSERT ON bookings
WHEN NEW.seat_number > (SELECT capacity FROM shows WHERE id = NEW.show_id)
BEGIN
    SELECT RAISE(ABORT, 'Seat exceeds hall capacity');
END;

CREATE TRIGGER IF NOT EXISTS booking_capacity_update
BEFORE UPDATE OF show_id, seat_number ON bookings
WHEN NEW.seat_number > (SELECT capacity FROM shows WHERE id = NEW.show_id)
BEGIN
    SELECT RAISE(ABORT, 'Seat exceeds hall capacity');
END;
