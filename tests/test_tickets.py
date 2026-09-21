from tickets import calculate_ticket_price


def test_ticket_price_with_discount():
    price = calculate_ticket_price(1500.0, 2, True)
    assert price == 1260.0


def test_unknown_zone_returns_none():
    assert calculate_ticket_price(1500.0, 10, False) is None
