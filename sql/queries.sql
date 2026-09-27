-- Примеры параметризованных запросов для будущего слоя доступа монолита.
-- :production_id, :role_id, :show_id, :seat_number — связанные параметры,
-- а не фрагменты SQL, полученные из пользовательского ввода.

-- Репертуар по дате премьеры.
SELECT id, title, author, genre, premiere_date
FROM productions ORDER BY premiere_date;

-- Ближайшие показы выбранной постановки.
SELECT s.id, s.starts_at, h.name AS hall, h.capacity
FROM shows AS s JOIN halls AS h ON h.id = s.hall_id
WHERE s.production_id = :production_id
ORDER BY s.starts_at;

-- Предварительная проверка места. При создании брони окончательную
-- защиту от гонки обеспечивает UNIQUE(show_id, seat_number).
SELECT NOT EXISTS (
    SELECT 1 FROM bookings
    WHERE show_id = :show_id AND seat_number = :seat_number
) AS is_available;

-- Подбор актёров по тем же критериям, что использует casting.py.
SELECT a.id, a.name, a.gender, a.age
FROM actors AS a JOIN roles AS r
  ON a.gender = r.required_gender AND a.age BETWEEN r.min_age AND r.max_age
WHERE r.id = :role_id;

-- Сводка без дублирования счётчиков и сумм в основных таблицах.
SELECT * FROM show_booking_statistics ORDER BY starts_at;

-- Сумма считается в целых копейках; округление среднего — при выводе.
SELECT count(*) AS booking_count,
       coalesce(sum(price_kopecks), 0) AS revenue_kopecks,
       coalesce(avg(price_kopecks), 0) AS average_price_kopecks
FROM bookings;
