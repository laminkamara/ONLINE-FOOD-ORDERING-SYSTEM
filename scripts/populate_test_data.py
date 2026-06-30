"""
Comprehensive Test Data Script for yoni Fast Food Restaurant
Run this with: python manage.py shell < populate_test_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering_system.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Customer, Branch, Table, Category, Restaurant, MenuItem

print("=" * 60)
print("yoni Fast Food Restaurant - Test Data Population")
print("=" * 60)
print()

# Check if data already exists
if Category.objects.exists():
    print("⚠️  Data already exists. Clearing old data...")
    MenuItem.objects.all().delete()
    Restaurant.objects.all().delete()
    Category.objects.all().delete()
    Table.objects.all().delete()
    Branch.objects.all().delete()
    print("✓ Old data cleared")
    print()

# 1. Create Categories
print("📦 Creating Categories...")
categories_data = [
    {"name": "Burgers", "icon": "🍔", "description": "Delicious gourmet burgers"},
    {"name": "Pizza", "icon": "🍕", "description": "Fresh wood-fired pizza"},
    {"name": "Local Dishes", "icon": "🍛", "description": "Authentic Sierra Leonean cuisine"},
    {"name": "Rice Dishes", "icon": "🍚", "description": "Flavorful rice meals"},
    {"name": "Chicken", "icon": "🍗", "description": "Tender chicken dishes"},
    {"name": "Sides", "icon": "🍟", "description": "Tasty side dishes"},
    {"name": "Desserts", "icon": "🍰", "description": "Sweet treats"},
    {"name": "Beverages", "icon": "🥤", "description": "Refreshing drinks"},
]

for cat_data in categories_data:
    cat, created = Category.objects.get_or_create(**cat_data)
    if created:
        print(f"  ✓ Created: {cat.icon} {cat.name}")

print(f"✅ Total Categories: {Category.objects.count()}")
print()

# 2. Create Branches
print("🏢 Creating Branches...")
branches_data = [
    {
        "name": "Main Branch - Downtown",
        "address": "32 free town road, mile 91",
        "phone": "+232 76 123456",
        "opening_hours": "08:00 AM - 11:00 PM"
    },
    {
        "name": "Beachside Grill",
        "address": "45 Lumley Beach Rd, Freetown",
        "phone": "+232 76 234567",
        "opening_hours": "10:00 AM - 01:00 AM"
    },
    {
        "name": "Aberdeen Terrace",
        "address": "88 Wilkinson Rd, Freetown",
        "phone": "+232 76 345678",
        "opening_hours": "07:00 AM - 10:00 PM"
    },
]

for branch_data in branches_data:
    branch, created = Branch.objects.get_or_create(**branch_data)
    if created:
        print(f"  ✓ Created: {branch.name}")

print(f"✅ Total Branches: {Branch.objects.count()}")
print()

# 3. Create Tables for Main Branch
print("🪑 Creating Tables...")
main_branch = Branch.objects.get(name__contains="Main Branch")

tables_data = [
    {"table_number": "T-01", "capacity": 4, "status": "available"},
    {"table_number": "T-02", "capacity": 2, "status": "occupied", "current_bill": 45},
    {"table_number": "T-03", "capacity": 6, "status": "available"},
    {"table_number": "T-04", "capacity": 4, "status": "reserved"},
    {"table_number": "T-05", "capacity": 8, "status": "occupied", "current_bill": 312},
    {"table_number": "T-06", "capacity": 2, "status": "available"},
    {"table_number": "T-07", "capacity": 4, "status": "occupied", "current_bill": 88},
    {"table_number": "T-08", "capacity": 4, "status": "available"},
    {"table_number": "T-09", "capacity": 6, "status": "available"},
    {"table_number": "T-10", "capacity": 2, "status": "reserved"},
    {"table_number": "T-11", "capacity": 4, "status": "available"},
    {"table_number": "T-12", "capacity": 8, "status": "available"},
]

for table_data in tables_data:
    table, created = Table.objects.get_or_create(branch=main_branch, **table_data)
    if created:
        status_icon = "✅" if table.status == "available" else "👥" if table.status == "occupied" else "🕐"
        print(f"  ✓ Created: {table.table_number} ({table.capacity} seats) - {status_icon} {table.get_status_display()}")

print(f"✅ Total Tables: {Table.objects.count()}")
print()

# 4. Create Restaurant
print("🍽️  Creating Restaurant...")
restaurant, created = Restaurant.objects.get_or_create(
    name="yoni Fast Food Restaurant",
    defaults={
        "description": "Serving the best fast food in Sierra Leone. Quality ingredients, lightning-fast service, and great value since 2010.",
        "address": "32 free town road, mile 91",
        "phone": "+232 76 123456"
    }
)
if created:
    print(f"  ✓ Created: {restaurant.name}")
print(f"✅ Restaurant: {restaurant.name}")
print()

# 5. Create Menu Items
print("🍔 Creating Menu Items...")

# Get categories
burgers_cat = Category.objects.get(name="Burgers")
pizza_cat = Category.objects.get(name="Pizza")
local_cat = Category.objects.get(name="Local Dishes")
rice_cat = Category.objects.get(name="Rice Dishes")
chicken_cat = Category.objects.get(name="Chicken")
sides_cat = Category.objects.get(name="Sides")
desserts_cat = Category.objects.get(name="Desserts")
beverages_cat = Category.objects.get(name="Beverages")

menu_items_data = [
    # Burgers
    {"name": "The Yoni Burger", "description": "Our signature beef burger with special sauce, lettuce, tomato, and cheese", "price": 85, "category": burgers_cat, "is_popular": True, "rating": 4.8, "review_count": 154},
    {"name": "Spicy Zinger Burger", "description": "Crispy chicken burger with spicy mayo and jalapeños", "price": 65, "category": burgers_cat, "is_new": True, "rating": 4.6, "review_count": 89},
    {"name": "Garden Fresh Veggie Burger", "description": "Plant-based patty with fresh vegetables and vegan sauce", "price": 55, "category": burgers_cat, "rating": 4.4, "review_count": 67},
    {"name": "Double Cheese Burger", "description": "Double beef patty with extra cheese and bacon", "price": 95, "category": burgers_cat, "is_popular": True, "rating": 4.7, "review_count": 198},

    # Pizza
    {"name": "Large Pepperoni Feast", "description": "Classic pepperoni pizza with extra mozzarella cheese", "price": 120, "category": pizza_cat, "is_popular": True, "rating": 4.9, "review_count": 203},
    {"name": "Beef Suya Pizza", "description": "Fusion pizza with spiced beef, peppers, and onions", "price": 135, "category": pizza_cat, "rating": 4.8, "review_count": 145},
    {"name": "Margherita Classic", "description": "Traditional pizza with tomato, mozzarella, and basil", "price": 95, "category": pizza_cat, "rating": 4.7, "review_count": 167},
    {"name": "BBQ Chicken Pizza", "description": "Grilled chicken with BBQ sauce and red onions", "price": 125, "category": pizza_cat, "is_new": True, "rating": 4.6, "review_count": 78},

    # Local Dishes
    {"name": "Classic Jollof with Grilled Chicken", "description": "Authentic Sierra Leonean jollof rice with tender grilled chicken", "price": 85, "category": local_cat, "is_popular": True, "rating": 4.8, "review_count": 312},
    {"name": "Supreme Jollof Box", "description": "Large jollof rice with assorted meats and fried plantain", "price": 95, "category": local_cat, "rating": 4.7, "review_count": 198},
    {"name": "Cassava Leaf with Rice", "description": "Traditional cassava leaf stew served with white rice", "price": 75, "category": local_cat, "is_popular": True, "rating": 4.9, "review_count": 256},

    # Rice Dishes
    {"name": "Fried Rice & Plantain Special", "description": "Chinese-style fried rice with sweet fried plantains", "price": 75, "category": rice_cat, "rating": 4.7, "review_count": 156},
    {"name": "Beef Fried Rice", "description": "Fried rice with tender beef strips and vegetables", "price": 85, "category": rice_cat, "rating": 4.6, "review_count": 134},
    {"name": "Chicken Biryani", "description": "Aromatic basmati rice with spiced chicken", "price": 95, "category": rice_cat, "is_new": True, "rating": 4.8, "review_count": 92},

    # Chicken
    {"name": "Crispy Peri-Peri Wings", "description": "Spicy grilled chicken wings (12 pieces) with peri-peri sauce", "price": 95, "category": chicken_cat, "is_popular": True, "rating": 4.7, "review_count": 178},
    {"name": "Grilled Chicken Quarter", "description": "Juicy quarter chicken with herbs and spices", "price": 85, "category": chicken_cat, "rating": 4.6, "review_count": 145},
    {"name": "Chicken Wings (6 pcs)", "description": "Crispy fried chicken wings with dipping sauce", "price": 55, "category": chicken_cat, "rating": 4.5, "review_count": 112},

    # Sides
    {"name": "Cheesy Garlic Breadsticks", "description": "Fresh baked breadsticks with garlic butter and cheese", "price": 35, "category": sides_cat, "rating": 4.5, "review_count": 92},
    {"name": "French Fries (Large)", "description": "Crispy golden french fries", "price": 25, "category": sides_cat, "is_popular": True, "rating": 4.6, "review_count": 234},
    {"name": "Coleslaw", "description": "Fresh homemade coleslaw", "price": 15, "category": sides_cat, "rating": 4.3, "review_count": 67},
    {"name": "Extra Fried Plantain", "description": "Sweet fried plantain slices", "price": 20, "category": sides_cat, "is_popular": True, "rating": 4.8, "review_count": 189},

    # Desserts
    {"name": "Double Choco Brownie", "description": "Rich chocolate brownie with vanilla ice cream", "price": 45, "category": desserts_cat, "rating": 4.9, "review_count": 134},
    {"name": "Vanilla Ice Cream", "description": "Creamy vanilla ice cream (3 scoops)", "price": 25, "category": desserts_cat, "rating": 4.6, "review_count": 87},
    {"name": "Fruit Salad", "description": "Fresh seasonal fruit salad", "price": 30, "category": desserts_cat, "rating": 4.5, "review_count": 56},

    # Beverages
    {"name": "Fresh Ginger Beer", "description": "Homemade spicy ginger beer", "price": 20, "category": beverages_cat, "is_popular": True, "rating": 4.7, "review_count": 187},
    {"name": "Hibiscus Juice (Bissap)", "description": "Traditional hibiscus flower drink", "price": 15, "category": beverages_cat, "is_popular": True, "rating": 4.8, "review_count": 203},
    {"name": "Fresh Lemonade", "description": "Freshly squeezed lemonade with mint", "price": 18, "category": beverages_cat, "rating": 4.6, "review_count": 145},
    {"name": "Coca-Cola (500ml)", "description": "Chilled Coca-Cola", "price": 12, "category": beverages_cat, "rating": 4.5, "review_count": 312},
    {"name": "Mineral Water", "description": "Pure bottled water (500ml)", "price": 8, "category": beverages_cat, "rating": 4.4, "review_count": 234},
]

for item_data in menu_items_data:
    item, created = MenuItem.objects.get_or_create(
        restaurant=restaurant,
        name=item_data["name"],
        defaults=item_data
    )
    if created:
        badges = []
        if item.is_popular:
            badges.append("⭐ Popular")
        if item.is_new:
            badges.append("🆕 New")
        badge_str = " | ".join(badges) if badges else ""
        print(f"  ✓ Created: {item.name} (Le {item.price:,.0f}) - {item.category.icon} {item.category.name} {badge_str}")

print(f"✅ Total Menu Items: {MenuItem.objects.count()}")
print()

# Summary
print("=" * 60)
print("✅ TEST DATA POPULATION COMPLETE!")
print("=" * 60)
print()
print("Database Summary:")
print(f"  • Categories: {Category.objects.count()}")
print(f"  • Branches: {Branch.objects.count()}")
print(f"  • Tables: {Table.objects.count()}")
print(f"  • Restaurants: {Restaurant.objects.count()}")
print(f"  • Menu Items: {MenuItem.objects.count()}")
print()
print("Next Steps:")
print("  1. Create admin user: python manage.py createsuperuser")
print("  2. Visit: http://127.0.0.1:8000")
print("  3. Admin panel: http://127.0.0.1:8000/admin")
print("  4. Register a test customer account")
print("  5. Test the complete ordering flow")
print()
