"""Загрузка данных для сайта."""

from functools import wraps
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.html import format_html
from django.views.decorators.http import require_safe

from storage import load_project

from .presentation import heading, page


def project_view(view: Callable) -> Callable:
    """Читаем JSON перед открытием страницы."""
    @wraps(view)
    def wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        try:
            data = load_project(settings.DATA_DIR)
        except (ValueError, OSError):
            content = format_html(
                '{}<p>Попробуйте открыть страницу позже.</p>',
                heading(
                    "Временно недоступно", "Не удалось загрузить данные",
                    "Информация театра сейчас недоступна.",
                ),
            )
            return HttpResponse(page("Данные недоступны", content), status=503)
        return view(request, *args, data=data, **kwargs)
    return require_safe(wrapped)
