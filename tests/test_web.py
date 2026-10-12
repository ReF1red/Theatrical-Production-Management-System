import os
import shutil
from pathlib import Path
from unittest.mock import patch

import django
import pytest
from django.test import Client, override_settings
from django.urls import reverse

from storage import load_project, save_bookings, save_productions

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theatre.settings")
django.setup()

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
URLS = [
    "/", "/productions/", "/productions/1/", "/shows/", "/shows/1/",
    "/bookings/", "/bookings/1/",
]


@pytest.fixture
def web_data(tmp_path):
    for path in DATA_DIR.glob("*.json"):
        shutil.copy(path, tmp_path / path.name)
    with override_settings(DATA_DIR=tmp_path):
        yield tmp_path


@pytest.mark.parametrize("url", URLS)
def test_pages_use_project_data_and_navigation(url, web_data):
    response = Client().get(url)
    assert response.status_code == 200
    content = response.content.decode()
    assert '<html lang="ru">' in content
    assert 'name="viewport"' in content
    assert "bootstrap@5.3.3" in content
    for link in ("/productions/", "/shows/", "/bookings/"):
        assert f'href="{link}"' in content
    assert "Вишнёвый сад" in content


@pytest.mark.parametrize("url", [
    "/productions/999/", "/shows/999/", "/bookings/999/",
])
def test_missing_objects_have_custom_404(url, web_data):
    response = Client().get(url)
    assert response.status_code == 404
    assert "Ошибка 404" in response.content.decode()


@pytest.mark.parametrize("url", [
    "/nonexistent/", "/productions/not-an-id/", "/shows/-1/",
])
def test_unknown_routes_use_root_handler404(url, web_data):
    with override_settings(DEBUG=False):
        response = Client().get(url)
    assert response.status_code == 404
    assert "Страница не найдена" in response.content.decode()
    assert "На главную" in response.content.decode()


def test_booking_links_to_same_show_and_production(web_data):
    response = Client().get("/bookings/1/")
    content = response.content.decode()
    assert 'href="/shows/1/"' in content
    assert 'href="/productions/1/"' in content
    assert "Большой зал" in content
    assert "1800.00 руб." in content
    assert "Бельэтаж" in content


def test_readiness_and_actor_matching_are_reused(web_data):
    content = Client().get("/productions/1/").content.decode()
    assert "Репетиции окончены, идёт оформление спектакля" in content
    assert "Раневская" in content
    assert "Анна Иванова" in content
    assert "Мария Орлова" in content
    assert "Пётр Смирнов" not in content


def test_cancelled_booking_is_shown_and_frees_capacity(web_data):
    client = Client()
    before = client.get("/shows/1/").content.decode()
    assert 'class="seat-count">119' in before
    data = load_project(web_data)
    data.bookings[0].cancel()
    save_bookings(web_data / "bookings.json", data.bookings)
    after = client.get("/shows/1/").content.decode()
    assert 'class="seat-count">120' in after
    detail = client.get("/bookings/1/").content.decode()
    assert "Отменено" in detail
    assert "status-cancelled" in detail
    assert "1800.00 руб." in detail


def test_dynamic_json_content_is_escaped_everywhere(web_data):
    data = load_project(web_data)
    data.productions[0].title = '<script>alert("x")</script>'
    save_productions(web_data / "productions.json", data.productions)
    for url in URLS:
        content = Client().get(url).content.decode()
        assert '<script>alert("x")</script>' not in content
        assert "&lt;script&gt;" in content


def test_empty_collections_have_messages(web_data):
    for path in web_data.glob("*.json"):
        path.write_text("[]")
    for url in ("/", "/productions/", "/shows/", "/bookings/"):
        response = Client().get(url)
        assert response.status_code == 200
        assert "пока нет" in response.content.decode()


def test_malformed_json_returns_503_without_technical_details(web_data):
    (web_data / "productions.json").write_text("{")
    response = Client().get("/productions/")
    assert response.status_code == 503
    assert "Не удалось загрузить данные" in response.content.decode()
    assert str(web_data) not in response.content.decode()


def test_views_do_not_use_database_or_write_json(web_data):
    before = {path: path.read_bytes() for path in web_data.glob("*.json")}
    with patch(
        "django.db.backends.dummy.base.DatabaseWrapper.cursor",
        side_effect=AssertionError("ПР5 не использует ORM"),
    ):
        for url in URLS:
            assert Client().get(url).status_code == 200
    assert before == {path: path.read_bytes() for path in before}


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_web_methods_cannot_change_data(method, web_data):
    before = {path: path.read_bytes() for path in web_data.glob("*.json")}
    response = getattr(Client(), method)("/bookings/1/")
    assert response.status_code == 405
    assert before == {path: path.read_bytes() for path in before}


def test_head_and_named_routes(web_data):
    assert (
        reverse("repertoire:production_detail", args=[1]) == "/productions/1/"
    )
    assert reverse("performances:show_detail", args=[1]) == "/shows/1/"
    assert reverse("reservations:booking_detail", args=[1]) == "/bookings/1/"
    response = Client().head("/shows/1/")
    assert response.status_code == 200
    assert response.content == b""
