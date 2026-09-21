import pytest

from bookings import (
    cancel_booking,
    create_booking,
    get_booking_statistics,
    is_seat_available,
)


def test_seat_is_available_when_bookings_empty():
    assert is_seat_available([], 1, 15)


def test_duplicate_seat_booking_is_forbidden():
    bookings = []
    create_booking(bookings, 1, 15, 2, "полный")
    with pytest.raises(ValueError):
        create_booking(bookings, 1, 15, 2, "полный")


def test_cancel_booking():
    bookings = []
    booking = create_booking(bookings, 1, 15, 2, "полный")
    assert cancel_booking(bookings, booking["id"])
    assert bookings == []


def test_booking_statistics():
    bookings = []
    create_booking(bookings, 1, 1, 1, "полный")
    create_booking(bookings, 1, 2, 3, "льготный")
    stats = get_booking_statistics(bookings)
    assert stats["count"] == 2
    assert stats["discount_count"] == 1
    assert stats["revenue"] == 2985.0
