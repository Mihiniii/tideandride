from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("fleet/", views.vehicle_list, name="vehicle_list"),
    path("fleet/<slug:slug>/", views.vehicle_detail, name="vehicle_detail"),
    path("bookings/", views.my_bookings, name="my_bookings"),
    path("bookings/<str:reference>/", views.booking_detail, name="booking_detail"),
    path(
        "bookings/<str:reference>/cancel/",
        views.cancel_booking,
        name="cancel_booking",
    ),
    path("signup/", views.signup, name="signup"),
    path("contact/", views.contact, name="contact"),
]
