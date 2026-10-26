from django.shortcuts import render

ZONE_NAMES = {1: "Партер", 2: "Бельэтаж", 3: "Балкон"}


def missing_object(request, title, route, label):
    return render(request, "404.html", {
        "title": title, "back_route": route, "back_label": label,
    }, status=404)
