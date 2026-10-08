import django.db.models.deletion
import rentals.models
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=70, unique=True)),
                ("illustration", models.CharField(choices=[("scooter", "Scooter"), ("tuktuk", "Tuk-tuk"), ("bicycle", "Bicycle"), ("buggy", "Beach buggy"), ("jeep", "Jeep"), ("van", "Surf van")], default="scooter", help_text="Drawing used when a vehicle has no photo.", max_length=20)),
                ("blurb", models.CharField(blank=True, max_length=140)),
                ("order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "verbose_name_plural": "categories",
                "ordering": ["order", "name"],
            },
        ),
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("handled", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=90, unique=True)),
                ("coast", models.CharField(blank=True, help_text="e.g. South coast, East coast", max_length=40)),
                ("tagline", models.CharField(blank=True, max_length=140)),
                ("order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "ordering": ["order", "name"],
            },
        ),
        migrations.CreateModel(
            name="Vehicle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("slug", models.SlugField(blank=True, max_length=110, unique=True)),
                ("image", models.ImageField(blank=True, upload_to="vehicles/")),
                ("price_per_day", models.DecimalField(decimal_places=2, max_digits=10)),
                ("deposit", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("seats", models.PositiveSmallIntegerField(default=2)),
                ("transmission", models.CharField(choices=[("auto", "Automatic"), ("manual", "Manual"), ("pedal", "Pedal power")], default="auto", max_length=10)),
                ("fuel", models.CharField(choices=[("petrol", "Petrol"), ("diesel", "Diesel"), ("electric", "Electric"), ("none", "None")], default="petrol", max_length=10)),
                ("licence", models.CharField(choices=[("none", "No licence needed"), ("bike", "Motorcycle licence"), ("three_wheel", "Three-wheeler licence"), ("car", "Car licence")], default="bike", max_length=15)),
                ("surfboard_rack", models.BooleanField(default=False)),
                ("helmets_included", models.BooleanField(default=False)),
                ("summary", models.CharField(blank=True, max_length=160)),
                ("description", models.TextField(blank=True)),
                ("features", models.TextField(blank=True, help_text="One feature per line, e.g. 'USB phone charger'.")),
                ("is_featured", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vehicles", to="rentals.category")),
                ("location", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vehicles", to="rentals.location")),
            ],
            options={
                "ordering": ["-is_featured", "price_per_day"],
            },
        ),
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(default=rentals.models.make_reference, editable=False, max_length=12, unique=True)),
                ("pickup_date", models.DateField()),
                ("return_date", models.DateField()),
                ("handover", models.CharField(choices=[("shop", "I'll collect it from the beach shop"), ("hotel", "Deliver it to my hotel")], default="shop", max_length=10)),
                ("hotel_name", models.CharField(blank=True, max_length=120)),
                ("full_name", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=30)),
                ("email", models.EmailField(max_length=254)),
                ("notes", models.TextField(blank=True)),
                ("days", models.PositiveSmallIntegerField(default=1)),
                ("price_per_day", models.DecimalField(decimal_places=2, max_digits=10)),
                ("total_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("deposit", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("status", models.CharField(choices=[("pending", "Waiting for confirmation"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"), ("completed", "Completed")], default="pending", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bookings", to=settings.AUTH_USER_MODEL)),
                ("vehicle", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="rentals.vehicle")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
