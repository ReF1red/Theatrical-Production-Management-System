import shutil
from pathlib import Path

import main
from storage import load_project


def test_console_create_cancel_rebook_and_reload(
    tmp_path, monkeypatch, capsys,
):
    source = Path(__file__).resolve().parents[1] / "data"
    for path in source.glob("*.json"):
        shutil.copy(path, tmp_path / path.name)
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    for name, filename in (
        ("PRODUCTIONS_FILE", "productions.json"),
        ("SHOWS_FILE", "shows.json"),
        ("BOOKINGS_FILE", "bookings.json"),
    ):
        monkeypatch.setattr(main, name, tmp_path / filename)
    answers = iter([
        "1", "7", "14", "1", "13", "2", "да",
        "10", "1", "16", "2", "полный",
        "11", "2",
        "10", "1", "16", "2", "льготный", "12", "15", "0",
    ])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    main.main()
    output = capsys.readouterr().out
    assert "Ошибка:" not in output
    assert "Бронирование отменено" in output
    assert "1260.00 руб." in output
    reloaded = load_project(tmp_path)
    assert reloaded.bookings[1].is_cancelled
    assert not reloaded.bookings[2].is_cancelled
    assert reloaded.bookings[2].show is reloaded.shows[0]


def test_console_reports_invalid_data(tmp_path, monkeypatch, capsys):
    (tmp_path / "productions.json").write_text("{")
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    main.main()
    assert "Не удалось загрузить данные" in capsys.readouterr().out
