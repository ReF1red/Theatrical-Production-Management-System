"""Расчёт стоимости билетов."""

BASE_TICKET_PRICE = 1500.0
ZONE_MULTIPLIERS = {
    1: 1.5,  # партер
    2: 1.2,  # бельэтаж
    3: 0.7,  # балкон
}
DISCOUNT_MULTIPLIER = 0.7


def calculate_ticket_price(
    base_price: float,
    seat_zone: int,
    is_discount_eligible: bool,
) -> float | None:
    """Рассчитать стоимость билета с учётом зоны и льготы."""
    multiplier = ZONE_MULTIPLIERS.get(seat_zone)
    if multiplier is None:
        return None

    price = base_price * multiplier
    if is_discount_eligible:
        price *= DISCOUNT_MULTIPLIER
    return round(price, 2)
