from django.urls import include, path

urlpatterns = [
    path("", include("homepage.urls")),
    path("productions/", include("repertoire.urls")),
    path("shows/", include("performances.urls")),
    path("bookings/", include("reservations.urls")),
]

handler404 = "homepage.views.page_not_found"
