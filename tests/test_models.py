from datetime import datetime

import pytest

from models import Actor, Booking, DiscountTicket, Role, Ticket
from models.bookings import get_available_seats
from models.productions import iter_productions_by_genre, update_readiness
from models.shows import add_show


def test_readiness_changes_same_object_seen_by_show(production, show):
    assert update_readiness([production], 1, True, True, True)
    assert show.production is production
    assert (
        show.production.get_status() == "Постановка готова к выпуску на сцену"
    )
    assert "Гамлет" in str(production)
    assert list(iter_productions_by_genre([production], " ТРАГЕДИЯ ")) == [
        production,
    ]


def test_invalid_readiness_does_not_partly_change_object(production):
    with pytest.raises(ValueError):
        production.update_readiness(True, "false", True)
    assert not production.rehearsals_done


def test_related_objects_and_string_representations(production, show):
    actor = Actor.from_data({
        "id": 1, "name": "Анна", "gender": "ж", "age": 34,
    })
    role = Role(1, production, "Офелия", "ж", 30, 45)
    booking = Booking(1, show, 1, 2, "льготный")
    assert actor.can_play(role)
    assert role.production is production
    assert booking.show is show
    assert booking.show.production is production
    assert isinstance(booking.ticket, DiscountTicket)
    for item in (actor, role, show, booking):
        assert str(item)
    assert "Гамлет" in str(booking)


def test_ticket_polymorphism_and_read_only_price():
    tickets = [Ticket(2), DiscountTicket(2)]
    assert [item.calculate_price() for item in tickets] == [1800, 1260]
    with pytest.raises(AttributeError):
        tickets[0].price = 100


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True])
def test_invalid_price_is_rejected(value):
    with pytest.raises(ValueError):
        Ticket(1, value)


def test_hall_cannot_have_two_shows_at_same_time(production, show):
    shows = [show]
    with pytest.raises(ValueError):
        add_show(shows, production, show.datetime, show.hall, 120)
    assert shows == [show]
    added = add_show(
        shows, production, datetime(2027, 1, 21, 19), show.hall, 120,
    )
    assert added.production is production


def test_cancelled_booking_frees_seat_count(show):
    booking = Booking(1, show, 1, 1, "полный")
    assert get_available_seats([booking], show) == 119
    booking.cancel()
    assert get_available_seats([booking], show) == 120
