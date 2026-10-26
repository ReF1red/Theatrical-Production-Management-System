from django.shortcuts import render
from django.utils import timezone

from db.database import fetch
from models.bookings import get_booking_statistics
from models.shows import sort_shows

from .data import project_view


@project_view
def index(request, data, conn=None):
    stats = get_booking_statistics(data.bookings)
    counters = (
        fetch(conn, "counters")[0] if conn is not None else {
            "productions": len(data.productions), "shows": len(data.shows),
            "active": stats["count"],
        }
    )
    upcoming = [show for show in sort_shows(data.shows)
                if show.datetime.date() >= timezone.localdate()][:3]
    return render(request, "homepage/index.html", {
        "title": "Главная", "section": "home", "counters": counters,
        "upcoming": upcoming, "productions": data.productions[:2],
    })


@project_view
def statistics(request, data, conn=None):
    if conn is None:
        return render(request, "homepage/statistics.html", {
            "title": "Статистика", "section": "statistics",
        })
    raw_threshold = request.GET.get("threshold", "0")
    try:
        threshold = int(raw_threshold)
        if not 0 <= threshold <= 1_000_000:
            raise ValueError
    except ValueError:
        return render(request, "homepage/statistics.html", {
            "title": "Статистика", "section": "statistics",
            "error": "Введите порог от 0 до 1000000.",
        }, status=400)
    return render(request, "homepage/statistics.html", {
        "title": "Статистика", "section": "statistics",
        "stats": fetch(conn, "booking_statistics")[0],
        "productions": fetch(conn, "production_statistics"),
        "halls": fetch(conn, "hall_statistics"),
        "popular": fetch(conn, "popular_productions", (threshold,)),
        "threshold": threshold,
    })


def page_not_found(request, exception):
    return render(request, "404.html", {
        "title": "Страница не найдена",
        "back_route": "homepage:index", "back_label": "На главную",
    }, status=404)
