from django.contrib import admin
from django.utils.html import format_html

from .models import Booking, Category, ContactMessage, Location, Vehicle


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "coast", "order")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "illustration", "order")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "thumb",
        "name",
        "category",
        "location",
        "price_per_day",
        "seats",
        "is_featured",
        "is_active",
    )
    list_display_links = ("thumb", "name")
    list_editable = ("price_per_day", "is_featured", "is_active")
    list_filter = ("category", "location", "is_featured", "is_active", "fuel")
    search_fields = ("name", "summary", "description")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "location", "image", "summary")}),
        ("Pricing", {"fields": ("price_per_day", "deposit")}),
        (
            "Specs",
            {
                "fields": (
                    ("seats", "transmission", "fuel", "licence"),
                    ("surfboard_rack", "helmets_included"),
                    "features",
                    "description",
                )
            },
        ),
        ("Visibility", {"fields": ("is_featured", "is_active")}),
    )

    @admin.display(description="")
    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:56px;height:40px;object-fit:cover;border-radius:6px">',
                obj.image.url,
            )
        return "—"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "vehicle",
        "full_name",
        "phone",
        "pickup_date",
        "return_date",
        "total_price",
        "status",
    )
    list_editable = ("status",)
    list_filter = ("status", "vehicle__location", "handover", "pickup_date")
    search_fields = ("reference", "full_name", "email", "phone", "vehicle__name")
    date_hierarchy = "pickup_date"
    readonly_fields = ("reference", "days", "total_price", "created_at")
    autocomplete_fields = ("vehicle",)
    actions = ("mark_confirmed", "mark_completed")

    @admin.action(description="Mark selected bookings as confirmed")
    def mark_confirmed(self, request, queryset):
        n = queryset.filter(status=Booking.STATUS_PENDING).update(
            status=Booking.STATUS_CONFIRMED
        )
        self.message_user(request, f"{n} booking(s) confirmed.")

    @admin.action(description="Mark selected bookings as completed")
    def mark_completed(self, request, queryset):
        n = queryset.exclude(status=Booking.STATUS_CANCELLED).update(
            status=Booking.STATUS_COMPLETED
        )
        self.message_user(request, f"{n} booking(s) completed.")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "handled")
    list_editable = ("handled",)
    list_filter = ("handled",)
    search_fields = ("name", "email", "message")
