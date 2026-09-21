# Generated manually for seeding FoodShare default food categories

from django.db import migrations


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


def seed_default_categories(apps, schema_editor):
    FoodCategory = apps.get_model("donations", "FoodCategory")
    for item in DEFAULT_CATEGORIES:
        # Check by name and slug to guarantee idempotency and avoid duplicates
        existing = FoodCategory.objects.filter(name__iexact=item["name"]).first()
        if not existing:
            existing = FoodCategory.objects.filter(slug__iexact=item["slug"]).first()
        
        if existing:
            # Category already exists - ensure icon and is_active are set without overwriting user custom changes
            updated = False
            if not existing.icon and item.get("icon"):
                existing.icon = item["icon"]
                updated = True
            if updated:
                existing.save(update_fields=["icon"])
        else:
            FoodCategory.objects.create(
                name=item["name"],
                slug=item["slug"],
                description=item["description"],
                icon=item["icon"],
                is_active=item["is_active"],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0004_fooddonation_other_food_item"),
    ]

    operations = [
        migrations.RunPython(seed_default_categories, reverse_code=migrations.RunPython.noop),
    ]

