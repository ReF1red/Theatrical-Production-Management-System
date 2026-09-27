-- ПР3, часть 1. Схема для монолитного приложения, SQLite >= 3.37.
-- На КАЖДОМ соединении приложение включает PRAGMA foreign_keys = ON.
-- Транзакцией и версией схемы управляет database.py.

CREATE TABLE productions (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    author TEXT NOT NULL CHECK (length(trim(author)) > 0),
    genre TEXT NOT NULL CHECK (length(trim(genre)) > 0),
    premiere_date TEXT NOT NULL CHECK (coalesce(
        length(premiere_date) = 10
        AND date(premiere_date, '+0 days') = premiere_date, 0)),
    rehearsals_done INTEGER NOT NULL DEFAULT 0 CHECK (rehearsals_done IN (0, 1)),
    costumes_ready INTEGER NOT NULL DEFAULT 0 CHECK (costumes_ready IN (0, 1)),
    scenery_ready INTEGER NOT NULL DEFAULT 0 CHECK (scenery_ready IN (0, 1))
) STRICT;

CREATE TABLE actors (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    gender TEXT NOT NULL CHECK (gender IN ('м', 'ж')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120)
) STRICT;

CREATE TABLE roles (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    production_id INTEGER NOT NULL REFERENCES productions(id) ON DELETE RESTRICT,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    required_gender TEXT NOT NULL CHECK (required_gender IN ('м', 'ж')),
    min_age INTEGER NOT NULL CHECK (min_age BETWEEN 0 AND 120),
    max_age INTEGER NOT NULL CHECK (max_age BETWEEN min_age AND 120),
    UNIQUE (production_id, title)
) STRICT;

CREATE TABLE cast_assignments (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    actor_id INTEGER NOT NULL REFERENCES actors(id) ON DELETE RESTRICT,
    PRIMARY KEY (role_id, actor_id)
) STRICT;

CREATE TABLE halls (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0),
    capacity INTEGER NOT NULL CHECK (capacity > 0)
) STRICT;

CREATE TABLE shows (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    production_id INTEGER NOT NULL REFERENCES productions(id) ON DELETE RESTRICT,
    hall_id INTEGER NOT NULL REFERENCES halls(id) ON DELETE RESTRICT,
    starts_at TEXT NOT NULL CHECK (coalesce(
        length(starts_at) = 16 AND
        strftime('%Y-%m-%dT%H:%M', starts_at, '+0 days') = starts_at, 0)),
    UNIQUE (hall_id, starts_at)
) STRICT;

CREATE TABLE ticket_zones (
    id INTEGER PRIMARY KEY CHECK (id IN (1, 2, 3)),
    name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0),
    multiplier_percent INTEGER NOT NULL CHECK (multiplier_percent > 0)
) STRICT;

CREATE TABLE ticket_categories (
    code TEXT PRIMARY KEY CHECK (code IN ('полный', 'льготный')),
    price_percent INTEGER NOT NULL CHECK (price_percent BETWEEN 0 AND 100)
) STRICT;

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT CHECK (id > 0),
    show_id INTEGER NOT NULL REFERENCES shows(id) ON DELETE RESTRICT,
    seat_number INTEGER NOT NULL CHECK (seat_number > 0),
    zone_id INTEGER NOT NULL REFERENCES ticket_zones(id) ON DELETE RESTRICT,
    category_code TEXT NOT NULL
        REFERENCES ticket_categories(code) ON DELETE RESTRICT,
    price_kopecks INTEGER NOT NULL CHECK (price_kopecks >= 0),
    UNIQUE (show_id, seat_number)
) STRICT;

-- UNIQUE уже создаёт индексы для броней по показу, ролей по постановке
-- и показов по залу. Не дублируем их отдельными индексами.
CREATE INDEX idx_productions_premiere ON productions(premiere_date);
CREATE INDEX idx_productions_genre ON productions(genre);
CREATE INDEX idx_shows_starts_at ON shows(starts_at);
CREATE INDEX idx_shows_production_date ON shows(production_id, starts_at);
CREATE INDEX idx_actors_gender_age ON actors(gender, age);
CREATE INDEX idx_cast_assignments_actor ON cast_assignments(actor_id);
CREATE INDEX idx_bookings_zone ON bookings(zone_id);
CREATE INDEX idx_bookings_category ON bookings(category_code);

-- CHECK не может проверять другую таблицу, поэтому границы мест
-- защищены триггерами для вставки И для изменения связанных данных.
CREATE TRIGGER bookings_capacity_insert
BEFORE INSERT ON bookings
WHEN NEW.seat_number > (
    SELECT h.capacity FROM shows AS s
    JOIN halls AS h ON h.id = s.hall_id WHERE s.id = NEW.show_id
)
BEGIN
    SELECT RAISE(ABORT, 'Номер места превышает вместимость зала');
END;

CREATE TRIGGER bookings_capacity_update
BEFORE UPDATE OF show_id, seat_number ON bookings
WHEN NEW.seat_number > (
    SELECT h.capacity FROM shows AS s
    JOIN halls AS h ON h.id = s.hall_id WHERE s.id = NEW.show_id
)
BEGIN
    SELECT RAISE(ABORT, 'Номер места превышает вместимость зала');
END;

CREATE TRIGGER halls_capacity_update
BEFORE UPDATE OF capacity ON halls
WHEN EXISTS (
    SELECT 1 FROM shows AS s JOIN bookings AS b ON b.show_id = s.id
    WHERE s.hall_id = OLD.id AND b.seat_number > NEW.capacity
)
BEGIN
    SELECT RAISE(ABORT, 'В зале есть брони за пределами новой вместимости');
END;

CREATE TRIGGER shows_hall_update
BEFORE UPDATE OF hall_id ON shows
WHEN EXISTS (
    SELECT 1 FROM bookings AS b
    WHERE b.show_id = OLD.id
      AND b.seat_number > (SELECT capacity FROM halls WHERE id = NEW.hall_id)
)
BEGIN
    SELECT RAISE(ABORT, 'В новом зале недостаточно мест для существующих броней');
END;

-- Агрегирование без сохранения устаревающего счётчика в shows.
CREATE VIEW show_booking_statistics AS
SELECT s.id AS show_id, p.title, s.starts_at, h.name AS hall,
       h.capacity, count(b.id) AS booking_count,
       h.capacity - count(b.id) AS available_seats,
       coalesce(sum(b.price_kopecks), 0) AS revenue_kopecks,
       coalesce(sum(b.category_code = 'льготный'), 0) AS discount_count
FROM shows AS s
JOIN productions AS p ON p.id = s.production_id
JOIN halls AS h ON h.id = s.hall_id
LEFT JOIN bookings AS b ON b.show_id = s.id
GROUP BY s.id, p.title, s.starts_at, h.name, h.capacity;

INSERT INTO ticket_zones (id, name, multiplier_percent) VALUES
    (1, 'партер', 150), (2, 'бельэтаж', 120), (3, 'балкон', 70);
INSERT INTO ticket_categories (code, price_percent) VALUES
    ('полный', 100), ('льготный', 70);
