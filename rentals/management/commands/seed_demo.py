from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from rentals.models import Category, Location, Vehicle

LOCATIONS = [
    ("Mirissa", "South coast", "Whale-watching harbour and Coconut Tree Hill"),
    ("Unawatuna", "South coast", "Calm bay, close to Galle Fort"),
    ("Hikkaduwa", "South coast", "Reef snorkelling and sunset bars"),
    ("Weligama", "South coast", "Long beginner surf break"),
    ("Arugam Bay", "East coast", "Main Point surf, May to October"),
]

CATEGORIES = [
    ("Scooters", "scooter", "Easy automatics for coast-road hopping"),
    ("Tuk-tuks", "tuktuk", "Three wheels, room for three and a board"),
    ("Bicycles", "bicycle", "Slow mornings along the beach road"),
    ("Beach buggies", "buggy", "Open-air, sand-ready, loud and fun"),
    ("Jeeps", "jeep", "4x4 for safari days and back roads"),
    ("Surf vans", "van", "Boards on the roof, crew inside"),
]

# name, category, location, price/day, deposit, seats, transmission, fuel, licence,
# rack, helmets, featured, summary, features
VEHICLES = [
    ("Honda Dio 110", "scooter", "Mirissa", 3500, 10000, 2, "auto", "petrol", "bike", False, True, True,
     "Light, quick and easy to park outside any beach café.",
     "Two helmets\nUnder-seat storage\nPhone holder\nFull tank at pickup"),
    ("Yamaha Ray ZR", "scooter", "Unawatuna", 3800, 10000, 2, "auto", "petrol", "bike", True, True, False,
     "Peppy 125cc with a side rack for a shortboard.",
     "Side surf rack\nTwo helmets\nUSB charger"),
    ("TVS Ntorq", "scooter", "Weligama", 3600, 10000, 2, "auto", "petrol", "bike", True, True, True,
     "The surfer's pick in Weligama, rack already fitted.",
     "Side surf rack\nTwo helmets\nBungee cords"),
    ("Honda Navi", "scooter", "Arugam Bay", 3400, 8000, 2, "auto", "petrol", "bike", True, True, False,
     "Tiny, tough and fine on the sandy lanes to Whiskey Point.",
     "Side surf rack\nTwo helmets"),
    ("Bajaj RE classic", "tuktuk", "Mirissa", 6500, 20000, 3, "manual", "petrol", "three_wheel", True, False, True,
     "Drive yourself. Room for three and a board on the roof.",
     "Roof board rack\nBluetooth speaker\nRain curtains\nLocal SIM with data"),
    ("Bajaj RE electric", "tuktuk", "Hikkaduwa", 7200, 20000, 3, "auto", "electric", "three_wheel", False, False, False,
     "Silent electric tuk-tuk, about 90 km per charge.",
     "Charging cable\nRain curtains\nCooler box"),
    ("Beach cruiser", "bicycle", "Unawatuna", 900, 0, 1, "pedal", "none", "none", False, False, False,
     "Wide tyres and a front basket for towels and snacks.",
     "Front basket\nLock and key\nLights"),
    ("City bike with rack", "bicycle", "Hikkaduwa", 1100, 0, 1, "pedal", "none", "none", True, False, False,
     "Seven gears and a side rack for a soft-top board.",
     "Side board rack\nLock\nPuncture kit"),
    ("Sand buggy 250", "buggy", "Hikkaduwa", 14500, 40000, 2, "auto", "petrol", "car", False, True, True,
     "Roll-cage buggy for the backroads between Hikkaduwa and Galle.",
     "Two helmets\nRoll cage\nGoggles\nDry bag"),
    ("Sand buggy 400 XL", "buggy", "Arugam Bay", 17500, 50000, 4, "auto", "petrol", "car", True, True, False,
     "Four-seater for the lagoon tracks to Peanut Farm.",
     "Roof board rack\nFour helmets\nCooler box"),
    ("Suzuki Jimny", "jeep", "Weligama", 16000, 50000, 4, "manual", "petrol", "car", True, False, True,
     "Small 4x4 that handles Yala safari roads and hill country.",
     "Roof rack\nAir conditioning\nPhone mount\nChild seat on request"),
    ("Mahindra Thar soft-top", "jeep", "Arugam Bay", 19500, 60000, 4, "manual", "diesel", "car", True, False, False,
     "Roof off, boards on, out to Kumana for the elephants.",
     "Removable top\nRoof board rack\nCooler box"),
    ("Toyota HiAce surf van", "van", "Weligama", 24000, 60000, 8, "manual", "diesel", "car", True, False, True,
     "Eight seats, six boards on the roof, a cold box in the back.",
     "Six-board roof rack\nAir conditioning\nCooler box\nWet-bag hooks"),
    ("Nissan Caravan", "van", "Mirissa", 22000, 60000, 7, "auto", "diesel", "car", True, False, False,
     "Automatic minivan for families and airport runs.",
     "Roof rack\nAir conditioning\nTwo child seats on request"),
]


class Command(BaseCommand):
    help = "Create demo beaches, vehicle types and a fleet of vehicles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing vehicles, categories and locations first "
            "(fails if bookings exist).",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            Vehicle.objects.all().delete()
            Category.objects.all().delete()
            Location.objects.all().delete()

        locs = {}
        for i, (name, coast, tagline) in enumerate(LOCATIONS):
            locs[name], _ = Location.objects.update_or_create(
                name=name, defaults={"coast": coast, "tagline": tagline, "order": i}
            )

        cats = {}
        for i, (name, art, blurb) in enumerate(CATEGORIES):
            cats[art], _ = Category.objects.update_or_create(
                name=name, defaults={"illustration": art, "blurb": blurb, "order": i}
            )

        created = 0
        for (name, art, loc, price, dep, seats, trans, fuel, lic, rack, helmets,
             featured, summary, features) in VEHICLES:
            _, was_created = Vehicle.objects.update_or_create(
                name=name,
                location=locs[loc],
                defaults=dict(
                    category=cats[art],
                    price_per_day=Decimal(price),
                    deposit=Decimal(dep),
                    seats=seats,
                    transmission=trans,
                    fuel=fuel,
                    licence=lic,
                    surfboard_rack=rack,
                    helmets_included=helmets,
                    is_featured=featured,
                    summary=summary,
                    features=features,
                    description=(
                        f"{summary}\n\nPicked up from our {loc} beach shop, "
                        "or delivered to your hotel for free within 5 km. "
                        "Serviced before every rental. Fuel is full at pickup; "
                        "return it the same way."
                    ),
                ),
            )
            created += was_created

        self.stdout.write(
            self.style.SUCCESS(
                f"Ready: {len(locs)} beaches, {len(cats)} vehicle types, "
                f"{len(VEHICLES)} vehicles ({created} new)."
            )
        )
