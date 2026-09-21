from django.core.management.base import BaseCommand
from apps.donations.models import FoodCategory


DEFAULT_CATEGORIES = [
    {
        "name": "Rice & Grains",
        "slug": "rice-grains",
        "description": "Cooked or raw rice, wheat, flour, oats, cereals, and staple grains.",
        "icon": "🌾",
        "is_active": True,
    },
    {
        "name": "Bakery & Bread",
        "slug": "bakery-bread",
        "description": "Fresh bread, buns, pastries, baked goods, and sandwich loaves.",
        "icon": "🍞",
        "is_active": True,
    },
    {
        "name": "Fruits & Vegetables",
        "slug": "fruits-vegetables",
        "description": "Fresh surplus fruits, raw vegetables, herbs, and farm produce.",
        "icon": "🥦",
        "is_active": True,
    },
    {
        "name": "Dairy & Milk",
        "slug": "dairy-milk",
        "description": "Milk, curd, cheese, butter, paneer, and chilled dairy products.",
        "icon": "🥛",
        "is_active": True,
    },
    {
        "name": "Cooked Meals",
        "slug": "cooked-meals",
        "description": "Prepared hot meals, curries, thalis, cafeteria surplus, and catering dishes.",
        "icon": "🍲",
        "is_active": True,
    },
    {
        "name": "Packaged & Canned Food",
        "slug": "packaged-canned-food",
        "description": "Sealed packaged groceries, canned food items, sauces, and dry rations.",
        "icon": "🥫",
        "is_active": True,
    },
    {
        "name": "Pulses & Legumes",
        "slug": "pulses-legumes",
        "description": "Lentils, dal, chickpeas, kidney beans, beans, and dried legumes.",
        "icon": "🫘",
        "is_active": True,
    },
    {
        "name": "Snacks & Dry Food",
        "slug": "snacks-dry-food",
        "description": "Biscuits, dry snacks, crackers, chips, energy bars, and nuts.",
        "icon": "🍪",
        "is_active": True,
    },
    {
        "name": "Beverages",
        "slug": "beverages",
        "description": "Bottled water, fruit juices, milkshakes, tea, and sealed drinks.",
        "icon": "🧃",
        "is_active": True,
    },
    {
        "name": "Baby Food",
        "slug": "baby-food",
        "description": "Infant formula, baby cereals, purees, and toddler food products.",
        "icon": "🍼",
        "is_active": True,
    },
    {
        "name": "Other",
        "slug": "other",
        "description": "Other assorted edible food supplies and miscellaneous surplus items.",
        "icon": "📦",
        "is_active": True,
    },
]


class Command(BaseCommand):
    help = "Seed default FoodShare food categories idempotently without duplicates."

    def handle(self, *args, **options):
        created_count = 0
        existing_count = 0

        for item in DEFAULT_CATEGORIES:
            existing = FoodCategory.objects.filter(name__iexact=item["name"]).first()
            if not existing:
                existing = FoodCategory.objects.filter(slug__iexact=item["slug"]).first()

            if existing:
                existing_count += 1
                if not existing.icon and item.get("icon"):
                    existing.icon = item["icon"]
                    existing.save(update_fields=["icon"])
                self.stdout.write(f"Category '{existing.name}' already exists.")
            else:
                cat = FoodCategory.objects.create(
                    name=item["name"],
                    slug=item["slug"],
                    description=item["description"],
                    icon=item["icon"],
                    is_active=item["is_active"],
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created category '{cat.name}'."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeding completed: {created_count} created, {existing_count} already existed."
            )
        )

