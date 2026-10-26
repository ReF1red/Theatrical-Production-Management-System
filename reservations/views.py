from django.shortcuts import render

from db.database import fetch
from homepage.data import project_view
from homepage.presentation import ZONE_NAMES, missing_object
from models.bookings import get_booking_by_id, get_booking_statistics


@project_view
def bookings(request, data, conn=None):
    status = request.GET.get("status", "all")
    if status not in {"all", "active", "cancelled"}:
        return render(request, "400.html", status=400)
    items = sorted(data.bookings, key=lambda item: -item.id)
    if status != "all":
        cancelled = status == "cancelled"
        if conn is not None:
            identifiers = {row["id"] for row in
                           fetch(conn, "bookings_by_status", (cancelled,))}
            items = [item for item in items if item.id in identifiers]
        else:
            items = [item for item in items
                     if item.is_cancelled == cancelled]
    stats = (fetch(conn, "booking_statistics")[0] if conn is not None
             else get_booking_statistics(data.bookings))
    return render(request, "reservations/booking_list.html", {
        "title": "Бронирования", "section": "bookings", "stats": stats,
        "bookings": [{"booking": item, "zone": ZONE_NAMES[item.zone]}
                     for item in items], "status": status,
    })


@project_view
def booking_detail(request, booking_id, data, conn=None):
    booking = get_booking_by_id(data.bookings, booking_id)
    if booking is None:
        return missing_object(request, "Бронирование не найдено",
                              "reservations:bookings", "К бронированиям")
    details = (fetch(conn, "booking_detail", (booking_id,))[0]
               if conn is not None else {"hall": booking.show.hall})
    return render(request, "reservations/booking_detail.html", {
        "title": f"Бронь #{booking.id}", "section": "bookings",
        "booking": booking, "zone": ZONE_NAMES[booking.zone],
        "details": details,
    })
