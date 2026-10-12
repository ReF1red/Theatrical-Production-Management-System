from math import isfinite

from .validation import require_int

BASE_TICKET_PRICE = 1500.0
ZONE_MULTIPLIERS = {1: 1.5, 2: 1.2, 3: 0.7}
DISCOUNT_MULTIPLIER = 0.7


class Ticket:
    """Билет с сохранённой ценой."""

    category = "полный"

    def __init__(
        self,
        zone: int,
        base_price: float = BASE_TICKET_PRICE,
        price: float | None = None,
    ) -> None:
        self.zone = require_int(zone, "Зона", 1, 3)
        self.base_price = self.validate_price(base_price)
        self._price = (
            self.calculate_price()
            if price is None else self.validate_price(price)
        )

    @staticmethod
    def validate_price(value: float) -> float:
        if (
            type(value) not in (int, float)
            or not isfinite(value) or value < 0
        ):
            raise ValueError("Цена должна быть конечным числом не меньше нуля")
        return round(float(value), 2)

    @property
    def price(self) -> float:
        """Цена на момент бронирования."""
        return self._price

    def calculate_price(self) -> float:
        return round(self.base_price * ZONE_MULTIPLIERS[self.zone], 2)

    def __str__(self) -> str:
        return f"{self.category}, зона {self.zone}, {self.price:.2f} руб."


class DiscountTicket(Ticket):
    """Льготный билет."""

    category = "льготный"

    def calculate_price(self) -> float:
        return round(
            self.base_price * ZONE_MULTIPLIERS[self.zone]
            * DISCOUNT_MULTIPLIER, 2,
        )


def calculate_ticket_price(
    base_price: float, seat_zone: int, is_discount_eligible: bool,
) -> float | None:
    if type(seat_zone) is not int or seat_zone not in ZONE_MULTIPLIERS:
        return None
    ticket_class = DiscountTicket if is_discount_eligible else Ticket
    return ticket_class(seat_zone, base_price).price
