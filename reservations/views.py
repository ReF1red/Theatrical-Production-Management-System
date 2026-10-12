"""Страницы бронирований."""

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from homepage.data import project_view
from homepage.presentation import (
    ZONE_NAMES, empty_state, heading, missing_object, page, status_badge,
)
from models.bookings import get_booking_by_id, get_booking_statistics
from storage import TheatreData


@project_view
def bookings(request: HttpRequest, data: TheatreData) -> HttpResponse:
    stats = get_booking_statistics(data.bookings)
    rows = format_html_join(
        "", '<tr><td><a href="{}">#{}</a></td>'
        '<td><a href="{}">{}</a><small class="table-note">{}</small></td>'
        '<td>{}</td><td>{} · {}</td><td>{} руб.</td><td>{}</td></tr>',
        ((reverse("reservations:booking_detail", args=[item.id]), item.id,
          reverse("performances:show_detail", args=[item.show.id]),
          item.show.production.title,
          item.show.datetime.strftime("%d.%m.%Y %H:%M"),
          item.seat_number, ZONE_NAMES[item.zone], item.category,
          f"{item.price:.2f}", status_badge(
              item.get_status(), "cancelled" if item.is_cancelled else "ready",
          )) for item in sorted(data.bookings, key=lambda item: -item.id)),
    )
    table = format_html(
        '<div class="panel table-responsive"><table class="table">'
        '<thead><tr><th scope="col">Бронь</th><th scope="col">Показ</th>'
        '<th scope="col">Место</th><th scope="col">Билет</th>'
        '<th scope="col">Стоимость</th><th scope="col">Статус</th>'
        '</tr></thead><tbody>{}</tbody></table></div>', rows,
    ) if data.bookings else empty_state("Бронирований пока нет.")
    content = format_html(
        '{}<div class="metrics"><div class="metric"><strong>{}</strong>'
        '<span>Активных бронирований</span></div>'
        '<div class="metric"><strong>{}</strong><span>Отменено</span></div>'
        '<div class="metric"><strong>{} ₽</strong>'
        '<span>Выручка</span>'
        '</div></div>{}',
        heading("Билеты", "Бронирования", "Продажи и история отмен."),
        stats["count"], stats["cancelled_count"],
        f'{stats["revenue"]:.2f}', table,
    )
    return HttpResponse(page("Бронирования", content, "bookings"))


@project_view
def booking_detail(
    request: HttpRequest, booking_id: int, data: TheatreData,
) -> HttpResponse:
    booking = get_booking_by_id(data.bookings, booking_id)
    if booking is None:
        return missing_object(
            "Бронирование не найдено", "reservations:bookings",
            "К бронированиям",
        )
    content = format_html(
        '<a class="back-link" href="{}">← К бронированиям</a>{}'
        '<div class="detail-grid"><section class="panel">'
        '<h2>Спектакль и показ</h2><dl><dt>Постановка</dt>'
        '<dd><a href="{}">{}</a></dd><dt>Показ</dt>'
        '<dd><a href="{}">{}</a></dd><dt>Зал</dt><dd>{}</dd></dl>'
        '</section><section class="panel"><h2>Билет</h2>{}'
        '<dl><dt>Место</dt><dd>{}</dd><dt>Зона</dt><dd>{}</dd>'
        '<dt>Категория</dt><dd>{}</dd><dt>Стоимость</dt>'
        '<dd class="price">{} руб.</dd></dl></section></div>',
        reverse("reservations:bookings"),
        heading("Бронирование", f"Бронь #{booking.id}",
                booking.show.production.title),
        reverse("repertoire:production_detail",
                args=[booking.show.production.id]),
        booking.show.production.title,
        reverse("performances:show_detail", args=[booking.show.id]),
        booking.show.datetime.strftime("%d.%m.%Y %H:%M"), booking.show.hall,
        status_badge(booking.get_status(),
                     "cancelled" if booking.is_cancelled else "ready"),
        booking.seat_number, ZONE_NAMES[booking.zone], booking.category,
        f"{booking.price:.2f}",
    )
    return HttpResponse(page(f"Бронь #{booking.id}", content, "bookings"))
