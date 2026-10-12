from .shows import Show
from .tickets import BASE_TICKET_PRICE, DiscountTicket, Ticket
from .validation import require_bool, require_int


class Booking:
    """Бронь на показ."""

    def __init__(
        self,
        booking_id: int,
        show: Show,
        seat_number: int,
        zone: int,
        category: str,
        base_price: float = BASE_TICKET_PRICE,
        price: float | None = None,
        is_cancelled: bool = False,
    ) -> None:
        self.id = require_int(booking_id, "ID бронирования")
        if not isinstance(show, Show):
            raise ValueError("Для бронирования требуется существующий показ")
        if not show.has_seat(seat_number):
            raise ValueError("Номер места вне вместимости зала")
        if category not in {"полный", "льготный"}:
            raise ValueError("Категория должна быть 'полный' или 'льготный'")
        self.show = show
        self.seat_number = seat_number
        ticket_class = DiscountTicket if category == "льготный" else Ticket
        self.ticket = ticket_class(zone, base_price, price)
        self.is_cancelled = require_bool(is_cancelled, "Статус отмены")

    @property
    def zone(self) -> int:
        return self.ticket.zone

    @property
    def category(self) -> str:
        return self.ticket.category

    @property
    def price(self) -> float:
        return self.ticket.price

    def cancel(self) -> None:
        """Отменённая бронь остаётся в списке."""
        self.is_cancelled = True

    def get_status(self) -> str:
        return "Отменено" if self.is_cancelled else "Активно"

    def to_data(self) -> dict:
        return {
            "id": self.id, "show_id": self.show.id,
            "seat_number": self.seat_number, "zone": self.zone,
            "category": self.category, "price": self.price,
            "is_cancelled": self.is_cancelled,
        }

    @classmethod
    def from_data(cls, data: dict, show: Show) -> "Booking":
        return cls(
            data["id"], show, data["seat_number"], data["zone"],
            data["category"], price=data["price"],
            is_cancelled=data.get("is_cancelled", False),
        )

    def __str__(self) -> str:
        return (
            f"#{self.id}: «{self.show.production.title}», "
            f"показ {self.show.id}, место {self.seat_number}, "
            f"{self.ticket}; {self.get_status()}"
        )


def is_seat_available(
    bookings: list[Booking], show: Show, seat_number: int,
) -> bool:
    return show.has_seat(seat_number) and not any(
        item.show.id == show.id and item.seat_number == seat_number
        and not item.is_cancelled for item in bookings
    )


def create_booking(
    bookings: list[Booking],
    show: Show,
    seat_number: int,
    zone: int,
    category: str,
    base_price: float = BASE_TICKET_PRICE,
) -> Booking:
    if not show.has_seat(seat_number):
        raise ValueError("Номер места вне вместимости зала")
    if not is_seat_available(bookings, show, seat_number):
        raise ValueError("Это место уже забронировано")
    next_id = max((item.id for item in bookings), default=0) + 1
    booking = Booking(next_id, show, seat_number, zone, category, base_price)
    bookings.append(booking)
    return booking


def get_booking_by_id(
    bookings: list[Booking], booking_id: int,
) -> Booking | None:
    return next((item for item in bookings if item.id == booking_id), None)


def cancel_booking(bookings: list[Booking], booking_id: int) -> bool:
    booking = get_booking_by_id(bookings, booking_id)
    if booking is None or booking.is_cancelled:
        return False
    booking.cancel()
    return True


def find_bookings_by_show(
    bookings: list[Booking], show_id: int,
) -> list[Booking]:
    return [item for item in bookings if item.show.id == show_id]


def get_available_seats(bookings: list[Booking], show: Show) -> int:
    occupied = {
        item.seat_number for item in bookings
        if item.show.id == show.id and not item.is_cancelled
    }
    return show.capacity - len(occupied)


def get_booking_statistics(bookings: list[Booking]) -> dict:
    active = [item for item in bookings if not item.is_cancelled]
    count = len(active)
    revenue = round(sum(item.price for item in active), 2)
    return {
        "count": count, "revenue": revenue,
        "average_price": round(revenue / count, 2) if count else 0.0,
        "discount_count": sum(item.category == "льготный" for item in active),
        "cancelled_count": len(bookings) - count,
    }
