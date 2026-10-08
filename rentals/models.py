import secrets
import string
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


def unique_slug(instance, value, field="slug"):
    """Build a slug from `value` that is unique for the instance's model."""
    base = slugify(value)[:60] or "item"
    slug, n = base, 2
    model = type(instance)
    while model.objects.filter(**{field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


class Location(models.Model):
    """A beach town where vehicles are picked up."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    coast = models.CharField(
        max_length=40, blank=True, help_text="e.g. South coast, East coast"
    )
    tagline = models.CharField(max_length=140, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    """Vehicle type: scooter, tuk-tuk, bicycle, beach buggy, jeep, van."""

    ART_SCOOTER = "scooter"
    ART_TUKTUK = "tuktuk"
    ART_BICYCLE = "bicycle"
    ART_BUGGY = "buggy"
    ART_JEEP = "jeep"
    ART_VAN = "van"
    ART_CHOICES = [
        (ART_SCOOTER, "Scooter"),
        (ART_TUKTUK, "Tuk-tuk"),
        (ART_BICYCLE, "Bicycle"),
        (ART_BUGGY, "Beach buggy"),
        (ART_JEEP, "Jeep"),
        (ART_VAN, "Surf van"),
    ]

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)
    illustration = models.CharField(
        max_length=20,
        choices=ART_CHOICES,
        default=ART_SCOOTER,
        help_text="Drawing used when a vehicle has no photo.",
    )
    blurb = models.CharField(max_length=140, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)


class VehicleQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def available_between(self, start, end):
        """Vehicles with no pending/confirmed booking overlapping [start, end]."""
        busy = Booking.objects.filter(
            status__in=Booking.BLOCKING_STATUSES,
            pickup_date__lte=end,
            return_date__gte=start,
        ).values("vehicle_id")
        return self.exclude(pk__in=busy)


class Vehicle(models.Model):
    TRANSMISSION_CHOICES = [
        ("auto", "Automatic"),
        ("manual", "Manual"),
        ("pedal", "Pedal power"),
    ]
    FUEL_CHOICES = [
        ("petrol", "Petrol"),
        ("diesel", "Diesel"),
        ("electric", "Electric"),
        ("none", "None"),
    ]
    LICENCE_CHOICES = [
        ("none", "No licence needed"),
        ("bike", "Motorcycle licence"),
        ("three_wheel", "Three-wheeler licence"),
        ("car", "Car licence"),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="vehicles"
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name="vehicles"
    )
    image = models.ImageField(upload_to="vehicles/", blank=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    deposit = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    seats = models.PositiveSmallIntegerField(default=2)
    transmission = models.CharField(
        max_length=10, choices=TRANSMISSION_CHOICES, default="auto"
    )
    fuel = models.CharField(max_length=10, choices=FUEL_CHOICES, default="petrol")
    licence = models.CharField(
        max_length=15, choices=LICENCE_CHOICES, default="bike"
    )
    surfboard_rack = models.BooleanField(default=False)
    helmets_included = models.BooleanField(default=False)
    summary = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    features = models.TextField(
        blank=True, help_text="One feature per line, e.g. 'USB phone charger'."
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = VehicleQuerySet.as_manager()

    class Meta:
        ordering = ["-is_featured", "price_per_day"]

    def __str__(self):
        return f"{self.name} ({self.location})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, f"{self.name} {self.location.name}")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("vehicle_detail", kwargs={"slug": self.slug})

    @property
    def feature_list(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]

    def is_available(self, start, end, exclude_booking=None):
        qs = self.bookings.filter(
            status__in=Booking.BLOCKING_STATUSES,
            pickup_date__lte=end,
            return_date__gte=start,
        )
        if exclude_booking is not None:
            qs = qs.exclude(pk=exclude_booking.pk)
        return not qs.exists()

    def booked_ranges(self):
        """Upcoming blocked date ranges, for showing on the detail page."""
        today = timezone.localdate()
        return self.bookings.filter(
            status__in=Booking.BLOCKING_STATUSES, return_date__gte=today
        ).order_by("pickup_date").values_list("pickup_date", "return_date")


def make_reference():
    alphabet = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
    return "TR-" + "".join(secrets.choice(alphabet) for _ in range(6))


class Booking(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Waiting for confirmation"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_COMPLETED, "Completed"),
    ]
    BLOCKING_STATUSES = [STATUS_PENDING, STATUS_CONFIRMED]

    DROP_PICKUP = "shop"
    DROP_HOTEL = "hotel"
    HANDOVER_CHOICES = [
        (DROP_PICKUP, "I'll collect it from the beach shop"),
        (DROP_HOTEL, "Deliver it to my hotel"),
    ]

    reference = models.CharField(
        max_length=12, unique=True, default=make_reference, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT, related_name="bookings"
    )
    pickup_date = models.DateField()
    return_date = models.DateField()
    handover = models.CharField(
        max_length=10, choices=HANDOVER_CHOICES, default=DROP_PICKUP
    )
    hotel_name = models.CharField(max_length=120, blank=True)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    notes = models.TextField(blank=True)
    days = models.PositiveSmallIntegerField(default=1)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    deposit = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} · {self.vehicle.name}"

    @staticmethod
    def count_days(pickup, ret):
        """Same-day return counts as one day."""
        return max((ret - pickup).days, 1)

    def clean(self):
        if self.pickup_date and self.return_date:
            if self.return_date < self.pickup_date:
                raise ValidationError(
                    {"return_date": "Return date must be on or after the pickup date."}
                )
            if self.vehicle_id and not self.vehicle.is_available(
                self.pickup_date, self.return_date, exclude_booking=self
            ):
                raise ValidationError(
                    "This vehicle is already booked for some of those dates."
                )

    def save(self, *args, **kwargs):
        if self.pickup_date and self.return_date and self.vehicle_id:
            if not self.price_per_day:
                self.price_per_day = self.vehicle.price_per_day
            self.days = self.count_days(self.pickup_date, self.return_date)
            self.total_price = self.price_per_day * self.days
            if not self.pk:
                self.deposit = self.vehicle.deposit
        super().save(*args, **kwargs)

    @property
    def can_cancel(self):
        return (
            self.status in self.BLOCKING_STATUSES
            and self.pickup_date > timezone.localdate()
        )


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"
