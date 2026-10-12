from django.urls import path

from . import views

app_name = "reservations"
urlpatterns = [
    path("", views.bookings, name="bookings"),
    path("<int:booking_id>/", views.booking_detail, name="booking_detail"),
]
