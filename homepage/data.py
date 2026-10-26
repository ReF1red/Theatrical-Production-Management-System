import sqlite3
from contextlib import nullcontext
from functools import wraps
from typing import Callable

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_safe

from db.database import connect
from db.repository import load_project as load_sqlite
from storage import load_project


def project_view(view: Callable) -> Callable:
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            if settings.DATA_SOURCE not in {"json", "sqlite"}:
                raise ValueError("Неизвестный источник данных")
            connection = (
                connect(settings.SQLITE_PATH, readonly=True)
                if settings.DATA_SOURCE == "sqlite" else nullcontext(None)
            )
            with connection as conn:
                data = (load_sqlite(conn) if conn is not None
                        else load_project(settings.DATA_DIR))
                return view(request, *args, data=data, conn=conn, **kwargs)
        except (ValueError, OSError, sqlite3.Error, KeyError):
            return render(request, "503.html", status=503)
    return require_safe(wrapped)
