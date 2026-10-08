from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Min, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BookingForm, ContactForm, SearchForm, SignUpForm
from .models import Booking, Category, Location, Vehicle


def home(request):
    active = Q(vehicles__is_active=True)
    categories = Category.objects.annotate(
        n=Count("vehicles", filter=active),
        from_price=Min("vehicles__price_per_day", filter=active),
    )
    locations = Location.objects.annotate(n=Count("vehicles", filter=active))
    featured = (
        Vehicle.objects.active()
        .filter(is_featured=True)
        .select_related("category", "location")[:6]
    )
    return render(
        request,
        "rentals/home.html",
        {
            "form": SearchForm(),
            "categories": categories,
            "locations": locations,
            "featured": featured,
            "fleet_size": Vehicle.objects.active().count(),
        },
    )


def vehicle_list(request):
    form = SearchForm(request.GET or None)
    vehicles = Vehicle.objects.active().select_related("category", "location")
    pickup = dropoff = None

    if form.is_valid():
        d = form.cleaned_data
        if d.get("location"):
            vehicles = vehicles.filter(location=d["location"])
        if d.get("category"):
            vehicles = vehicles.filter(category=d["category"])
        if d.get("max_price"):
            vehicles = vehicles.filter(price_per_day__lte=d["max_price"])
        pickup, dropoff = d.get("pickup"), d.get("dropoff")
        if pickup and not dropoff:
            dropoff = pickup
        if pickup and dropoff:
            vehicles = vehicles.available_between(pickup, dropoff)
        sort = d.get("sort")
        if sort == "price":
            vehicles = vehicles.order_by("price_per_day")
        elif sort == "-price":
            vehicles = vehicles.order_by("-price_per_day")
        elif sort == "seats":
            vehicles = vehicles.order_by("-seats", "price_per_day")

    page = Paginator(vehicles, 9).get_page(request.GET.get("page"))

    # Keep filters in pagination links
    params = request.GET.copy()
    params.pop("page", None)

    days = Booking.count_days(pickup, dropoff) if pickup and dropoff else None
    return render(
        request,
        "rentals/vehicle_list.html",
        {
            "form": form,
            "page": page,
            "querystring": params.urlencode(),
            "categories": Category.objects.all(),
            "days": days,
            "pickup": pickup,
            "dropoff": dropoff,
        },
    )


def vehicle_detail(request, slug):
    vehicle = get_object_or_404(
        Vehicle.objects.select_related("category", "location"),
        slug=slug,
        is_active=True,
    )

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.info(request, "Log in or create an account to finish your booking.")
            return redirect(f"{reverse('login')}?next={vehicle.get_absolute_url()}")
        form = BookingForm(request.POST, vehicle=vehicle)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.vehicle = vehicle
            booking.price_per_day = vehicle.price_per_day
            booking.save()
            messages.success(request, "Booking sent. We'll confirm it by phone shortly.")
            return redirect("booking_detail", reference=booking.reference)
    else:
        initial = {}
        # Carry dates over from the search page
        for src, dst in (("pickup", "pickup_date"), ("dropoff", "return_date")):
            if request.GET.get(src):
                initial[dst] = request.GET[src]
        if request.user.is_authenticated:
            u = request.user
            initial.setdefault("full_name", u.get_full_name() or u.first_name)
            initial.setdefault("email", u.email)
        form = BookingForm(initial=initial, vehicle=vehicle)

    similar = (
        Vehicle.objects.active()
        .filter(Q(category=vehicle.category) | Q(location=vehicle.location))
        .exclude(pk=vehicle.pk)
        .select_related("category", "location")[:3]
    )
    return render(
        request,
        "rentals/vehicle_detail.html",
        {
            "vehicle": vehicle,
            "form": form,
            "similar": similar,
            "booked_ranges": vehicle.booked_ranges()[:6],
        },
    )


@login_required
def booking_detail(request, reference):
    booking = get_object_or_404(
        Booking.objects.select_related("vehicle__category", "vehicle__location"),
        reference=reference,
        user=request.user,
    )
    return render(request, "rentals/booking_detail.html", {"booking": booking})


@login_required
def my_bookings(request):
    today = timezone.localdate()
    qs = Booking.objects.filter(user=request.user).select_related(
        "vehicle__category", "vehicle__location"
    )
    upcoming = qs.filter(
        return_date__gte=today, status__in=Booking.BLOCKING_STATUSES
    ).order_by("pickup_date")
    past = qs.exclude(pk__in=upcoming.values("pk"))
    return render(
        request,
        "rentals/my_bookings.html",
        {"upcoming": upcoming, "past": past},
    )


@login_required
@require_POST
def cancel_booking(request, reference):
    booking = get_object_or_404(Booking, reference=reference, user=request.user)
    if booking.can_cancel:
        booking.status = Booking.STATUS_CANCELLED
        booking.save(update_fields=["status"])
        messages.success(request, f"Booking {booking.reference} cancelled.")
    else:
        messages.error(
            request,
            "This booking can't be cancelled online. Call us and we'll sort it out.",
        )
    return redirect("my_bookings")


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    next_url = request.GET.get("next") or request.POST.get("next") or ""
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}. Your account is ready.")
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect("vehicle_list")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form, "next": next_url})


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Message sent. We reply within a few hours.")
            return redirect("contact")
    else:
        form = ContactForm()
    return render(
        request,
        "rentals/contact.html",
        {"form": form, "locations": Location.objects.all()},
    )
