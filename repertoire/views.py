from django.shortcuts import render

from db.database import fetch
from db.repository import production_from_row
from homepage.data import project_view
from homepage.presentation import missing_object
from models.casting import find_suitable_actors
from models.productions import get_production_by_id, sort_productions


@project_view
def productions(request, data, conn=None):
    genre = request.GET.get("genre", "").strip()
    items = sort_productions(data.productions)
    if genre:
        items = (
            [production_from_row(row) for row in
             fetch(conn, "productions_by_genre", (genre,))]
            if conn is not None else
            [item for item in items if item.genre == genre]
        )
    return render(request, "repertoire/production_list.html", {
        "title": "Репертуар новый", "section": "productions",
        "productions": items, "genre": genre,
        "genres": sorted({item.genre for item in data.productions}),
    })


@project_view
def production_detail(request, production_id, data, conn=None):
    production = get_production_by_id(data.productions, production_id)
    if production is None:
        return missing_object(request, "Постановка не найдена",
                              "repertoire:productions", "К репертуару")
    matches = (fetch(conn, "suitable_actors", (production_id,))
               if conn is not None else None)
    roles = []
    for role in data.roles:
        if role.production is production:
            names = ([row["name"] for row in matches
                      if row["role_id"] == role.id] if matches is not None
                     else [actor.name for actor in
                           find_suitable_actors(data.actors, role)])
            roles.append({"role": role, "actors": names})
    return render(request, "repertoire/production_detail.html", {
        "title": production.title, "section": "productions",
        "production": production, "roles": roles,
        "shows": sorted(
            [show for show in data.shows if show.production is production],
            key=lambda show: show.datetime,
        ),
        "readiness": [
            ("Репетиции", production.rehearsals_done),
            ("Костюмы", production.costumes_ready),
            ("Декорации", production.scenery_ready),
        ],
    })
