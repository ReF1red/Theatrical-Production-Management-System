"""Страницы постановок."""

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from homepage.data import project_view
from homepage.presentation import (
    empty_state, heading, missing_object, page, status_badge,
)
from models.casting import find_suitable_actors
from models.productions import get_production_by_id, sort_productions
from storage import TheatreData


@project_view
def productions(request: HttpRequest, data: TheatreData) -> HttpResponse:
    cards = []
    for item in sort_productions(data.productions):
        ready = all((
            item.rehearsals_done, item.costumes_ready, item.scenery_ready,
        ))
        cards.append(format_html(
            '<article class="production-card"><p class="eyebrow">{}</p>'
            '<h2><a href="{}">{}</a></h2><p class="muted">{}</p>'
            '<p>Премьера · {}</p>{}'
            '<a class="card-link" href="{}">Подробнее →</a></article>',
            item.genre,
            reverse("repertoire:production_detail", args=[item.id]),
            item.title, item.author, item.premiere_date.strftime("%d.%m.%Y"),
            status_badge(item.get_status(), "ready" if ready else "pending"),
            reverse("repertoire:production_detail", args=[item.id]),
        ))
    content = format_html(
        '{}<div class="production-grid">{}</div>',
        heading("Репертуар", "Постановки театра", "Репертуар и готовность."),
        format_html_join("", "{}", ((card,) for card in cards))
        if cards else empty_state("Постановок пока нет."),
    )
    return HttpResponse(page("Репертуар", content, "productions"))


@project_view
def production_detail(
    request: HttpRequest, production_id: int, data: TheatreData,
) -> HttpResponse:
    production = get_production_by_id(data.productions, production_id)
    if production is None:
        return missing_object(
            "Постановка не найдена", "repertoire:productions", "К репертуару",
        )
    readiness = format_html_join(
        "", '<div class="detail-row"><span>{}</span>{}</div>',
        ((label, status_badge(
            "Готово" if value else "В работе",
            "ready" if value else "pending",
        ))
         for label, value in (
             ("Репетиции", production.rehearsals_done),
             ("Костюмы", production.costumes_ready),
             ("Декорации", production.scenery_ready),
         )),
    )
    related_shows = [
        show for show in data.shows if show.production is production
    ]
    show_links = format_html_join(
        "", '<li><a href="{}">{} · {}</a></li>',
        ((reverse("performances:show_detail", args=[show.id]),
          show.datetime.strftime("%d.%m.%Y %H:%M"), show.hall)
         for show in sorted(related_shows, key=lambda item: item.datetime)),
    ) if related_shows else format_html(
        '<li class="muted">{}</li>', "Показы ещё не запланированы.",
    )
    roles = [role for role in data.roles if role.production is production]
    role_rows = format_html_join(
        "", '<li><strong>{}</strong><p class="muted">'
        'Возраст {}–{}, пол {}. Подходят: {}</p></li>',
        ((role.title, role.min_age, role.max_age, role.required_gender,
          ", ".join(actor.name for actor in
                    find_suitable_actors(data.actors, role)) or "нет актёров")
         for role in roles),
    ) if roles else format_html(
        '<li class="muted">{}</li>', "Роли ещё не добавлены.",
    )
    content = format_html(
        '<a class="back-link" href="{}">← К репертуару</a>{}'
        '<div class="detail-grid"><section class="panel">'
        '<h2>Подготовка спектакля</h2>{}<p class="muted">{}</p></section>'
        '<section class="panel"><h2>О постановке</h2>'
        '<dl><dt>Автор</dt><dd>{}</dd><dt>Жанр</dt><dd>{}</dd>'
        '<dt>Премьера</dt><dd>{}</dd></dl></section></div>'
        '<div class="detail-grid"><section class="panel">'
        '<h2>Показы</h2><ul class="plain-list">{}</ul></section>'
        '<section class="panel"><h2>Роли и актёры</h2>'
        '<ul class="plain-list">{}</ul></section></div>',
        reverse("repertoire:productions"),
        heading("Постановка", production.title, production.author),
        readiness, production.get_status(),
        production.author, production.genre,
        production.premiere_date.strftime("%d.%m.%Y"), show_links, role_rows,
    )
    return HttpResponse(page(production.title, content, "productions"))
