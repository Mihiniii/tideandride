from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, Category, Location, Vehicle


class RentalFlowTests(TestCase):
    def setUp(self):
        self.loc = Location.objects.create(name="Mirissa")
        self.cat = Category.objects.create(name="Scooters", illustration="scooter")
        self.vehicle = Vehicle.objects.create(
            name="Honda Dio", category=self.cat, location=self.loc,
            price_per_day=Decimal("3500"), deposit=Decimal("10000"),
        )
        self.user = User.objects.create_user("sam", "sam@example.com", "pw-Beach-2026")
        self.today = timezone.localdate()

    def book(self, start, end):
        return Booking.objects.create(
            user=self.user, vehicle=self.vehicle, pickup_date=start, return_date=end,
            full_name="Sam", phone="0771234567", email="sam@example.com",
            price_per_day=self.vehicle.price_per_day, total_price=0,
        )

    def test_pages_load(self):
        for name in ("home", "vehicle_list", "contact", "signup", "login"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(self.vehicle.get_absolute_url()).status_code, 200)

    def test_total_price(self):
        b = self.book(self.today + timedelta(days=1), self.today + timedelta(days=4))
        self.assertEqual(b.days, 3)
        self.assertEqual(b.total_price, Decimal("10500"))
        self.assertEqual(b.deposit, Decimal("10000"))

    def test_overlap_blocks_availability(self):
        self.book(self.today + timedelta(days=2), self.today + timedelta(days=5))
        self.assertFalse(
            self.vehicle.is_available(self.today + timedelta(days=4), self.today + timedelta(days=6))
        )
        self.assertTrue(
            self.vehicle.is_available(self.today + timedelta(days=6), self.today + timedelta(days=8))
        )
        free = Vehicle.objects.available_between(
            self.today + timedelta(days=3), self.today + timedelta(days=3)
        )
        self.assertNotIn(self.vehicle, free)

    def test_booking_via_form(self):
        self.client.login(username="sam", password="pw-Beach-2026")
        start = self.today + timedelta(days=3)
        resp = self.client.post(self.vehicle.get_absolute_url(), {
            "pickup_date": start.isoformat(),
            "return_date": (start + timedelta(days=2)).isoformat(),
            "handover": "shop",
            "full_name": "Sam Perera",
            "phone": "0771234567",
            "email": "sam@example.com",
        })
        booking = Booking.objects.get()
        self.assertRedirects(resp, reverse("booking_detail", args=[booking.reference]))
        self.assertEqual(booking.total_price, Decimal("7000"))

    def test_hotel_delivery_needs_address(self):
        self.client.login(username="sam", password="pw-Beach-2026")
        start = self.today + timedelta(days=3)
        resp = self.client.post(self.vehicle.get_absolute_url(), {
            "pickup_date": start.isoformat(),
            "return_date": start.isoformat(),
            "handover": "hotel",
            "full_name": "Sam", "phone": "077", "email": "sam@example.com",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Booking.objects.exists())

    def test_cancel(self):
        self.client.login(username="sam", password="pw-Beach-2026")
        b = self.book(self.today + timedelta(days=3), self.today + timedelta(days=4))
        self.client.post(reverse("cancel_booking", args=[b.reference]))
        b.refresh_from_db()
        self.assertEqual(b.status, Booking.STATUS_CANCELLED)

    def test_other_users_cannot_see_booking(self):
        b = self.book(self.today + timedelta(days=3), self.today + timedelta(days=4))
        User.objects.create_user("eve", "eve@example.com", "pw-Beach-2026")
        self.client.login(username="eve", password="pw-Beach-2026")
        resp = self.client.get(reverse("booking_detail", args=[b.reference]))
        self.assertEqual(resp.status_code, 404)
