from django.urls import path

from . import views

app_name = "repertoire"
urlpatterns = [
    path("", views.productions, name="productions"),
    path("<int:production_id>/", views.production_detail,
         name="production_detail"),
]
