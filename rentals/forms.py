from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Booking, Category, ContactMessage, Location


class DateInput(forms.DateInput):
    input_type = "date"


class SearchForm(forms.Form):
    """Used on the home page ticket and the fleet filter bar (GET)."""

    SORT_CHOICES = [
        ("", "Recommended"),
        ("price", "Price: low to high"),
        ("-price", "Price: high to low"),
        ("seats", "Most seats"),
    ]

    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        empty_label="Any beach",
        to_field_name="slug",
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Any vehicle",
        to_field_name="slug",
    )
    pickup = forms.DateField(required=False, widget=DateInput)
    dropoff = forms.DateField(required=False, widget=DateInput, label="Return")
    max_price = forms.IntegerField(
        required=False,
        min_value=0,
        label="Max per day",
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 8000", "step": 500}),
    )
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate().isoformat()
        self.fields["pickup"].widget.attrs["min"] = today
        self.fields["dropoff"].widget.attrs["min"] = today

    def clean(self):
        data = super().clean()
        pickup, dropoff = data.get("pickup"), data.get("dropoff")
        if pickup and dropoff and dropoff < pickup:
            self.add_error("dropoff", "Return date must be on or after pickup.")
        return data


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            "pickup_date",
            "return_date",
            "handover",
            "hotel_name",
            "full_name",
            "phone",
            "email",
            "notes",
        ]
        widgets = {
            "pickup_date": DateInput,
            "return_date": DateInput,
            "handover": forms.RadioSelect,
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Flight time, surfboard size, child seat…",
                }
            ),
            "hotel_name": forms.TextInput(
                attrs={"placeholder": "Hotel or villa name and road"}
            ),
            "phone": forms.TextInput(attrs={"placeholder": "+94 7X XXX XXXX"}),
        }
        labels = {
            "pickup_date": "Pickup",
            "return_date": "Return",
            "handover": "Handover",
            "hotel_name": "Hotel address",
            "full_name": "Full name",
            "notes": "Anything we should know?",
        }

    def __init__(self, *args, vehicle=None, **kwargs):
        self.vehicle = vehicle
        super().__init__(*args, **kwargs)
        today = timezone.localdate().isoformat()
        self.fields["pickup_date"].widget.attrs["min"] = today
        self.fields["return_date"].widget.attrs["min"] = today
        self.fields["hotel_name"].required = False

    def clean_pickup_date(self):
        pickup = self.cleaned_data["pickup_date"]
        if pickup < timezone.localdate():
            raise forms.ValidationError("Pickup can't be in the past.")
        return pickup

    def clean(self):
        data = super().clean()
        pickup, ret = data.get("pickup_date"), data.get("return_date")
        if pickup and ret:
            if ret < pickup:
                self.add_error("return_date", "Return must be on or after pickup.")
            elif (ret - pickup).days > 60:
                self.add_error(
                    "return_date",
                    "For rentals longer than 60 days, contact us for a monthly rate.",
                )
            elif self.vehicle and not self.vehicle.is_available(pickup, ret):
                raise forms.ValidationError(
                    "Someone has already booked this vehicle for part of those "
                    "dates. Try different dates or pick another vehicle."
                )
        if data.get("handover") == Booking.DROP_HOTEL and not data.get("hotel_name"):
            self.add_error("hotel_name", "Tell us where to bring the vehicle.")
        return data


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=60, label="First name")
    email = forms.EmailField()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class StyledAuthenticationForm(AuthenticationForm):
    """Same as Django's login form; kept as a hook for styling attrs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"autocomplete": "username"})
        self.fields["password"].widget.attrs.update(
            {"autocomplete": "current-password"}
        )


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}
