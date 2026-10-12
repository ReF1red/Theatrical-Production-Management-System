"""Страницы показов."""

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from homepage.data import project_view
from homepage.presentation import (
    empty_state, heading, missing_object, page, status_badge,
)
from models.bookings import get_available_seats
from models.shows import get_show_by_id, sort_shows
from storage import TheatreData


@project_view
def shows(request: HttpRequest, data: TheatreData) -> HttpResponse:
    rows = format_html_join(
        "", '<tr><td><a href="{}">{}</a></td><td>{}</td>'
        '<td>{}</td><td>{} из {}</td></tr>',
        ((reverse("performances:show_detail", args=[show.id]),
          show.production.title, show.datetime.strftime("%d.%m.%Y %H:%M"),
          show.hall, get_available_seats(data.bookings, show), show.capacity)
         for show in sort_shows(data.shows)),
    )
    schedule = format_html(
        '<div class="panel table-responsive"><table class="table">'
        '<thead><tr><th scope="col">Спектакль</th><th scope="col">Дата</th>'
        '<th scope="col">Зал</th><th scope="col">Свободно мест</th>'
        '</tr></thead><tbody>{}</tbody></table></div>', rows,
    ) if data.shows else empty_state("Показов пока нет.")
    content = format_html(
        '{}{}', heading("Расписание", "Показы спектаклей",
                        "Даты, залы и доступные места."), schedule,
    )
    return HttpResponse(page("Показы", content, "shows"))


@project_view
def show_detail(
    request: HttpRequest, show_id: int, data: TheatreData,
) -> HttpResponse:
    show = get_show_by_id(data.shows, show_id)
    if show is None:
        return missing_object(
            "Показ не найден", "performances:shows", "К расписанию",
        )
    available = get_available_seats(data.bookings, show)
    content = format_html(
        '<a class="back-link" href="{}">← К расписанию</a>{}'
        '<div class="detail-grid"><section class="panel">'
        '<h2>О показе</h2><dl><dt>Постановка</dt>'
        '<dd><a href="{}">{}</a></dd><dt>Дата и время</dt><dd>{}</dd>'
        '<dt>Зал</dt><dd>{}</dd><dt>Вместимость</dt><dd>{} мест</dd>'
        '</dl></section><section class="panel">'
        '<h2>Доступность мест</h2>'
        '<p class="seat-count">{}<small> / {}</small>'
        '</p><p class="muted">Свободно для бронирования</p>{}'
        '<p class="mt-3"><a href="{}">Все бронирования →</a></p>'
        '</section></div>',
        reverse("performances:shows"),
        heading("Показ спектакля", show.production.title,
                show.datetime.strftime("%d.%m.%Y · %H:%M")),
        reverse("repertoire:production_detail", args=[show.production.id]),
        show.production.title, show.datetime.strftime("%d.%m.%Y %H:%M"),
        show.hall, show.capacity, available, show.capacity,
        status_badge(
            "Есть свободные места" if available else "Все места заняты",
            "ready" if available else "cancelled",
        ),
        reverse("reservations:bookings"),
    )
    return HttpResponse(page(show.production.title, content, "shows"))
