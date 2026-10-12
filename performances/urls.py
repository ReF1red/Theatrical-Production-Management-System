from django.urls import path

from . import views

app_name = "performances"
urlpatterns = [
    path("", views.shows, name="shows"),
    path("<int:show_id>/", views.show_detail, name="show_detail"),
]
