from datetime import date, datetime

from django.shortcuts import render

from db.database import fetch
from homepage.data import project_view
from homepage.presentation import missing_object
from models.bookings import get_available_seats
from models.shows import get_show_by_id, sort_shows


def schedule_rows(data, conn=None, selected_date=None):
    if conn is not None:
        rows = (
            fetch(conn, "available_shows", (selected_date,))
            if selected_date else fetch(conn, "schedule")
        )
        return [dict(row, datetime=datetime.fromisoformat(row["datetime"]))
                for row in rows]
    rows = []
    for show in sort_shows(data.shows):
        available = get_available_seats(data.bookings, show)
        if selected_date and (
            show.datetime.date().isoformat() != selected_date or not available
        ):
            continue
        rows.append({
            "id": show.id, "title": show.production.title,
            "datetime": show.datetime, "hall": show.hall,
            "capacity": show.capacity, "available": available,
        })
    return rows


@project_view
def shows(request, data, conn=None):
    return render(request, "performances/show_list.html", {
        "title": "Показы", "section": "shows",
        "shows": schedule_rows(data, conn),
    })


@project_view
def available(request, data, conn=None):
    selected = request.GET.get("date", "")
    error = ""
    rows = []
    if selected:
        try:
            parsed = date.fromisoformat(selected)
            if parsed.isoformat() != selected:
                raise ValueError
        except ValueError:
            error = "Укажите дату в формате ГГГГ-ММ-ДД."
        else:
            rows = schedule_rows(data, conn, selected)
    return render(request, "performances/available.html", {
        "title": "Свободные места", "section": "available",
        "selected_date": selected, "shows": rows, "error": error,
    }, status=400 if error else 200)


@project_view
def show_detail(request, show_id, data, conn=None):
    show = get_show_by_id(data.shows, show_id)
    if show is None:
        return missing_object(request, "Показ не найден",
                              "performances:shows", "К расписанию")
    return render(request, "performances/show_detail.html", {
        "title": show.production.title, "section": "shows", "show": show,
        "available": get_available_seats(data.bookings, show),
    })
