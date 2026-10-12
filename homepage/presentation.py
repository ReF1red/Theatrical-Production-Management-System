"""HTML для страниц."""

from django.http import HttpResponse
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeString

ZONE_NAMES = {1: "Партер", 2: "Бельэтаж", 3: "Балкон"}


def page(title: str, content: SafeString, section: str = "") -> SafeString:
    links = [
        ("homepage:index", "Главная", "home"),
        ("repertoire:productions", "Репертуар", "productions"),
        ("performances:shows", "Показы", "shows"),
        ("reservations:bookings", "Бронирования", "bookings"),
    ]
    navigation = format_html_join(
        "", '<a class="nav-link {}" href="{}">{}</a>',
        (("active" if key == section else "", reverse(name), label)
         for name, label, key in links),
    )
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
        "/dist/css/bootstrap.min.css"
    )
    return format_html(
        """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{} · Театр</title>
    <link rel="stylesheet" href="{}">
    <link rel="stylesheet" href="{}">
</head>
<body>
    <header class="site-header">
        <div class="shell header-inner">
            <a class="brand" href="{}">
                <span class="brand-symbol" aria-hidden="true">Т</span>
                <span>Театр<small>Управление постановками</small></span>
            </a>
            <nav class="nav" aria-label="Основная навигация">{}</nav>
        </div>
    </header>
    <main class="shell main-content">{}</main>
    <footer class="shell site-footer">
        Театр · Система управления театральными постановками
    </footer>
</body>
</html>""",
        title, bootstrap, static("homepage/style.css"),
        reverse("homepage:index"), navigation, content,
    )


def heading(label: str, title: str, description: str) -> SafeString:
    return format_html(
        '<div class="section-heading"><p class="eyebrow">{}</p>'
        '<h1>{}</h1><p class="description">{}</p></div>',
        label, title, description,
    )


def status_badge(text: str, kind: str) -> SafeString:
    return format_html('<span class="status status-{}">{}</span>', kind, text)


def empty_state(text: str) -> SafeString:
    return format_html('<p class="empty-state">{}</p>', text)


def missing_object(title: str, route: str, label: str) -> HttpResponse:
    content = format_html(
        '{}<a class="btn btn-primary" href="{}">{}</a>',
        heading("Ошибка 404", title, "Проверьте адрес или откройте список."),
        reverse(route), label,
    )
    return HttpResponse(page(title, content), status=404)
