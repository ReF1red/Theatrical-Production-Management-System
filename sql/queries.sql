-- name: productions
SELECT * FROM productions ORDER BY premiere_date, id;

-- name: actors
SELECT * FROM actors ORDER BY name, id;

-- name: roles
SELECT * FROM roles ORDER BY production_id, id;

-- name: shows
SELECT * FROM shows ORDER BY datetime, id;

-- name: bookings
SELECT * FROM bookings ORDER BY id DESC;

-- name: productions_by_genre
SELECT * FROM productions WHERE genre = ? ORDER BY premiere_date, id;

-- name: bookings_by_status
-- 0: активные, 1: отменённые.
SELECT * FROM bookings WHERE is_cancelled = ? ORDER BY id DESC;

-- name: schedule
SELECT s.*, p.title, s.capacity - COUNT(b.id) AS available
FROM shows AS s
JOIN productions AS p ON p.id = s.production_id
LEFT JOIN bookings AS b ON b.show_id = s.id AND b.is_cancelled = 0
GROUP BY s.id
ORDER BY s.datetime, s.id;

-- name: booking_detail
SELECT b.*, s.production_id, p.title, s.datetime, s.hall
FROM bookings AS b
JOIN shows AS s ON s.id = b.show_id
JOIN productions AS p ON p.id = s.production_id
WHERE b.id = ?;

-- name: counters
SELECT (SELECT COUNT(*) FROM productions) AS productions,
       (SELECT COUNT(*) FROM shows) AS shows,
       (SELECT COUNT(*) FROM bookings WHERE is_cancelled = 0) AS active;

-- name: booking_statistics
SELECT COUNT(CASE WHEN is_cancelled = 0 THEN 1 END) AS count,
       COALESCE(SUM(CASE WHEN is_cancelled = 0 THEN price END), 0) AS revenue,
       COALESCE(AVG(CASE WHEN is_cancelled = 0 THEN price END), 0) AS average_price,
       COUNT(CASE WHEN is_cancelled = 0 AND category = 'льготный' THEN 1 END)
           AS discount_count,
       COUNT(CASE WHEN is_cancelled = 1 THEN 1 END) AS cancelled_count
FROM bookings;

-- name: production_statistics
SELECT p.id, p.title, COUNT(DISTINCT s.id) AS show_count,
       COUNT(b.id) AS booking_count, COALESCE(SUM(b.price), 0) AS revenue
FROM productions AS p
LEFT JOIN shows AS s ON s.production_id = p.id
LEFT JOIN bookings AS b ON b.show_id = s.id AND b.is_cancelled = 0
GROUP BY p.id
ORDER BY booking_count DESC, p.id;

-- name: hall_statistics
SELECT s.hall, COUNT(DISTINCT s.id) AS show_count,
       COUNT(b.id) AS booking_count, COALESCE(SUM(b.price), 0) AS revenue
FROM shows AS s
LEFT JOIN bookings AS b ON b.show_id = s.id AND b.is_cancelled = 0
GROUP BY s.hall
ORDER BY s.hall;

-- name: popular_productions
SELECT p.id, p.title, COUNT(b.id) AS booking_count
FROM productions AS p
JOIN shows AS s ON s.production_id = p.id
JOIN bookings AS b ON b.show_id = s.id AND b.is_cancelled = 0
GROUP BY p.id
HAVING COUNT(b.id) > ?
ORDER BY booking_count DESC, p.id;

-- name: available_shows
SELECT s.*, p.title, s.capacity - COUNT(b.id) AS available
FROM shows AS s
JOIN productions AS p ON p.id = s.production_id
LEFT JOIN bookings AS b ON b.show_id = s.id AND b.is_cancelled = 0
WHERE substr(s.datetime, 1, 10) = ?
GROUP BY s.id
HAVING s.capacity - COUNT(b.id) > 0
ORDER BY s.datetime, s.id;

-- name: suitable_actors
SELECT r.id AS role_id, a.id AS actor_id, a.name
FROM roles AS r
JOIN actors AS a ON a.gender = r.required_gender
    AND a.age BETWEEN r.min_age AND r.max_age
WHERE r.production_id = ?
ORDER BY r.id, a.name;
