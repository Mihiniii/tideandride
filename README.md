# Tide & Ride: beach vehicle rentals (Django)

A Django 5 web app for renting scooters, tuk-tuks, bicycles, beach buggies, jeeps and surf vans from beach towns on Sri Lanka's south and east coasts.

## Features

- **Home page** with a ticket-style search (beach, vehicle type, pickup and return dates)
- **Fleet page** with filters (beach, dates, max price per day, sort) and type chips; dates hide vehicles that are already booked
- **Vehicle page** with specs, features, booked dates and a booking form that shows the total live
- **Double-booking protection**: pending and confirmed bookings block the same dates
- **Hotel delivery** option (asks for the address only when chosen)
- **Rental ticket** page for each booking with a reference like `TR-K7M2QX`
- **My bookings** (upcoming and past) with online cancellation before pickup day
- **Accounts**: sign up, log in, log out (Django auth)
- **Contact form** saved to the database
- **Admin**: manage beaches, vehicle types, vehicles (photo upload, inline price edits), bookings (confirm/complete in bulk), messages
- Vehicles without a photo get a drawn illustration for their type, so the site looks complete before you upload photos
- Responsive down to phone width, keyboard focus styles, respects reduced motion
- Tests for pricing, availability, booking, cancelling and access control

## Run it

```bash
python -m venv venv
# Windows: venv\Scripts\activate    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

python manage.py makemigrations rentals   # should say "No changes detected"
python manage.py migrate
python manage.py seed_demo                # 5 beaches, 6 types, 14 vehicles
python manage.py createsuperuser          # for /admin/
python manage.py runserver
```

Open http://127.0.0.1:8000 and http://127.0.0.1:8000/admin/.

Run the tests with `python manage.py test rentals`.

## Project layout

```
tideride/            settings, root urls
rentals/
  models.py          Location, Category, Vehicle, Booking, ContactMessage
  views.py           home, fleet, vehicle detail + booking, bookings, signup, contact
  forms.py           search, booking (availability checks), signup, contact
  admin.py
  templatetags/rentals_tags.py   money / times filters, query_with tag
  management/commands/seed_demo.py
templates/           base + pages; partials/art.html holds the vehicle drawings
static/css/style.css design system (colours and type at the top)
static/js/main.js    mobile menu, live booking total, date pairing
```

## Customise

- Business name, phone, email, currency: bottom of `tideride/settings.py`
- Colours: `:root` variables at the top of `static/css/style.css`
- Real photos: upload in admin → Vehicles; they replace the drawings automatically

## Before going live

Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` and `DJANGO_ALLOWED_HOSTS`, run `python manage.py collectstatic`, and serve `media/` (uploaded photos) from your web server or a storage bucket.
