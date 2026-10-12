import pytest

from models.bookings import (
    cancel_booking,
    create_booking,
    get_booking_statistics,
    is_seat_available,
)


def test_seat_is_available_when_bookings_empty(show):
    assert is_seat_available([], show, 15)


def test_duplicate_seat_booking_is_forbidden(show):
    bookings = []
    create_booking(bookings, show, 15, 2, "полный")
    with pytest.raises(ValueError):
        create_booking(bookings, show, 15, 2, "полный")


def test_cancel_booking(show):
    bookings = []
    booking = create_booking(bookings, show, 15, 2, "полный")
    assert cancel_booking(bookings, booking.id)
    assert bookings == [booking]
    assert booking.is_cancelled
    assert is_seat_available(bookings, show, 15)
    replacement = create_booking(bookings, show, 15, 2, "полный")
    assert replacement.id == booking.id + 1


def test_booking_statistics(show):
    bookings = []
    create_booking(bookings, show, 1, 1, "полный")
    create_booking(bookings, show, 2, 3, "льготный")
    stats = get_booking_statistics(bookings)
    assert stats["count"] == 2
    assert stats["discount_count"] == 1
    assert stats["revenue"] == 2985.0


def test_cancelled_booking_does_not_count_as_sale(show):
    bookings = []
    booking = create_booking(bookings, show, 1, 1, "полный")
    booking.cancel()
    stats = get_booking_statistics(bookings)
    assert stats["count"] == 0
    assert stats["revenue"] == 0
    assert stats["average_price"] == 0
    assert stats["cancelled_count"] == 1


@pytest.mark.parametrize("seat", [0, -1, 121, True])
def test_nonexistent_seat_is_rejected(show, seat):
    bookings = []
    assert not is_seat_available(bookings, show, seat)
    with pytest.raises(ValueError):
        create_booking(bookings, show, seat, 1, "полный")
    assert bookings == []
