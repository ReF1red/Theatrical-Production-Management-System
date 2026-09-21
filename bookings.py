"""Функции бронирования билетов на театральные показы."""

from tickets import BASE_TICKET_PRICE, calculate_ticket_price


def is_seat_available(
    bookings: list[dict],
    show_id: int,
    seat_number: int,
) -> bool:
    """Проверить, свободно ли место на выбранный показ."""
    return not any(
        booking["show_id"] == show_id
        and booking["seat_number"] == seat_number
        for booking in bookings
    )


def create_booking(
    bookings: list[dict],
    show_id: int,
    seat_number: int,
    zone: int,
    category: str,
    base_price: float = BASE_TICKET_PRICE,
) -> dict:
    """Создать бронирование билета и вернуть созданную запись."""
    if seat_number <= 0:
        raise ValueError("Номер места должен быть положительным")
    if category not in {"полный", "льготный"}:
        raise ValueError("Категория должна быть 'полный' или 'льготный'")
    if not is_seat_available(bookings, show_id, seat_number):
        raise ValueError("Это место уже забронировано")

    price = calculate_ticket_price(
        base_price,
        zone,
        category == "льготный",
    )
    if price is None:
        raise ValueError("Несуществующая зона зала")

    next_id = max((item["id"] for item in bookings), default=0) + 1
    booking = {
        "id": next_id,
        "show_id": show_id,
        "seat_number": seat_number,
        "zone": zone,
        "category": category,
        "price": price,
    }
    bookings.append(booking)
    return booking


def cancel_booking(bookings: list[dict], booking_id: int) -> bool:
    """Удалить бронирование по идентификатору."""
    for index, booking in enumerate(bookings):
        if booking["id"] == booking_id:
            bookings.pop(index)
            return True
    return False


def find_bookings_by_show(
    bookings: list[dict],
    show_id: int,
) -> list[dict]:
    """Вернуть бронирования для конкретного показа."""
    return [
        booking
        for booking in bookings
        if booking["show_id"] == show_id
    ]


def get_booking_statistics(bookings: list[dict]) -> dict:
    """Рассчитать количество бронирований и выручку."""
    count = len(bookings)
    revenue = round(sum(float(item["price"]) for item in bookings), 2)
    average_price = round(revenue / count, 2) if count else 0.0
    discount_count = sum(
        1 for item in bookings if item["category"] == "льготный"
    )
    return {
        "count": count,
        "revenue": revenue,
        "average_price": average_price,
        "discount_count": discount_count,
    }
