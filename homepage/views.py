"""Главная и страница 404."""

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join

from models.bookings import get_booking_statistics
from models.shows import sort_shows
from storage import TheatreData

from .data import project_view
from .presentation import empty_state, heading, page


@project_view
def index(request: HttpRequest, data: TheatreData) -> HttpResponse:
    statistics = get_booking_statistics(data.bookings)
    counters = format_html_join(
        "", '<div class="metric"><strong>{}</strong><span>{}</span></div>',
        ((len(data.productions), "Постановок в репертуаре"),
         (len(data.shows), "Показов в расписании"),
         (statistics["count"], "Активных бронирований")),
    )
    upcoming = [
        show for show in sort_shows(data.shows)
        if show.datetime.date() >= timezone.localdate()
    ][:3]
    rows = format_html_join(
        "", '<a class="show-preview" href="{}">'
        '<span class="show-date">{}</span><strong>{}</strong>'
        '<span class="muted">{} · {}</span>'
        '<span aria-hidden="true">→</span></a>',
        ((reverse("performances:show_detail", args=[show.id]),
          show.datetime.strftime("%d.%m"), show.production.title,
          show.datetime.strftime("%H:%M"), show.hall) for show in upcoming),
    ) if upcoming else empty_state("Ближайших показов пока нет.")
    content = format_html(
        '{}<div class="hero-actions">'
        '<a class="btn btn-primary" href="{}">Открыть репертуар</a>'
        '<a class="btn btn-outline-secondary" href="{}">Расписание показов</a>'
        '</div><div class="metrics">{}</div>'
        '<section class="panel"><div class="panel-heading">'
        '<h2>Ближайшие показы</h2><a href="{}">Всё расписание →</a>'
        '</div>{}</section>',
        heading(
            "Театральный сезон", "От репетиции до полного зала",
            "Репертуар, готовность спектаклей, показы и бронирования "
            "в одном пространстве.",
        ),
        reverse("repertoire:productions"), reverse("performances:shows"),
        counters, reverse("performances:shows"), rows,
    )
    return HttpResponse(page("Главная", content, "home"))


def page_not_found(
    request: HttpRequest, exception: Exception,
) -> HttpResponse:
    content = format_html(
        '{}<a class="btn btn-primary" href="{}">На главную</a>',
        heading(
            "Ошибка 404", "Страница не найдена",
            "Проверьте адрес или вернитесь на главную страницу театра.",
        ),
        reverse("homepage:index"),
    )
    return HttpResponse(page("Страница не найдена", content), status=404)
