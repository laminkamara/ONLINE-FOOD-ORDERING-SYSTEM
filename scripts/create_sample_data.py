import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering_system.settings')
django.setup()

from core.models import Branch, Table, Restaurant, Category, MenuItem
from django.contrib.auth.models import User
from core.models import Customer

# Create Categories
print("Creating categories...")
categories_data = [
    {"name": "Burgers", "icon": "🍔", "description": "Delicious burgers"},
    {"name": "Pizza", "icon": "🍕", "description": "Fresh pizza"},
    {"name": "Local Dishes", "icon": "🍛", "description": "Sierra Leonean favorites"},
    {"name": "Sides", "icon": "🍟", "description": "Tasty sides"},
    {"name": "Desserts", "icon": "🍰", "description": "Sweet treats"},
    {"name": "Beverages", "icon": "🥤", "description": "Refreshing drinks"},
]

for cat_data in categories_data:
    Category.objects.create(**cat_data)

print(f"Created {Category.objects.count()} categories")

# Create Branches
print("Creating branches...")
branches_data = [
    {"name": "Downtown Hub", "address": "32 free town road, mile 91", "phone": "+232 76 123456", "opening_hours": "08:00 AM - 11:00 PM"},
    {"name": "Beachside Grill", "address": "45 Lumley Beach Rd, Freetown", "phone": "+232 76 234567", "opening_hours": "10:00 AM - 01:00 AM"},
    {"name": "Aberdeen Terrace", "address": "88 Wilkinson Rd, Freetown", "phone": "+232 76 345678", "opening_hours": "07:00 AM - 10:00 PM"},
]

for branch_data in branches_data:
    Branch.objects.create(**branch_data)

print(f"Created {Branch.objects.count()} branches")

# Create Tables for Downtown Hub
print("Creating tables...")
downtown = Branch.objects.get(name="Downtown Hub")
tables_data = [
    {"table_number": "T-01", "capacity": 4, "status": "available"},
    {"table_number": "T-02", "capacity": 2, "status": "occupied", "current_bill": 45},
    {"table_number": "T-03", "capacity": 6, "status": "available"},
    {"table_number": "T-04", "capacity": 4, "status": "reserved"},
    {"table_number": "T-05", "capacity": 8, "status": "occupied", "current_bill": 120},
    {"table_number": "T-06", "capacity": 2, "status": "available"},
]

for table_data in tables_data:
    Table.objects.create(branch=downtown, **table_data)

print(f"Created {Table.objects.count()} tables")

# Create Restaurant
print("Creating restaurant...")
restaurant = Restaurant.objects.create(
    name="yoni Fast Food Restaurant",
    description="Serving the best fast food in Sierra Leone. Quality ingredients, lightning-fast service, and great value since 2010.",
    address="32 free town road, mile 91",
    phone="+232 76 123456"
)

# Create Menu Items
print("Creating menu items...")
burgers_cat = Category.objects.get(name="Burgers")
pizza_cat = Category.objects.get(name="Pizza")
local_cat = Category.objects.get(name="Local Dishes")
sides_cat = Category.objects.get(name="Sides")
desserts_cat = Category.objects.get(name="Desserts")
beverages_cat = Category.objects.get(name="Beverages")

menu_items_data = [
    # Burgers
    {"name": "The Yoni Burger", "description": "Our signature beef burger with special sauce", "price": 85, "category": burgers_cat, "is_popular": True, "rating": 4.8, "review_count": 154},
    {"name": "Spicy Zinger Burger", "description": "Crispy chicken burger with spicy mayo", "price": 65, "category": burgers_cat, "is_new": True, "rating": 4.6, "review_count": 89},
    {"name": "Garden Fresh Veggie Burger", "description": "Plant-based patty with fresh vegetables", "price": 55, "category": burgers_cat, "rating": 4.4, "review_count": 67},
    
    # Pizza
    {"name": "Large Pepperoni Feast", "description": "Classic pepperoni pizza with extra cheese", "price": 120, "category": pizza_cat, "is_popular": True, "rating": 4.9, "review_count": 203},
    {"name": "Beef Suya Pizza", "description": "Fusion pizza with spiced beef and peppers", "price": 135, "category": pizza_cat, "rating": 4.8, "review_count": 145},
    
    # Local Dishes
    {"name": "Classic Jollof with Grilled Chicken", "description": "Authentic Sierra Leonean jollof rice with chicken", "price": 85, "category": local_cat, "is_popular": True, "rating": 4.8, "review_count": 312},
    {"name": "Supreme Jollof Box", "description": "Large jollof rice with assorted meats", "price": 95, "category": local_cat, "rating": 4.7, "review_count": 198},
    {"name": "Fried Rice & Plantain Special", "description": "Fried rice with sweet plantains", "price": 75, "category": local_cat, "rating": 4.7, "review_count": 156},
    
    # Sides
    {"name": "Crispy Peri-Peri Wings", "description": "Spicy chicken wings (12 pieces)", "price": 95, "category": sides_cat, "is_popular": True, "rating": 4.7, "review_count": 178},
    {"name": "Cheesy Garlic Breadsticks", "description": "Fresh breadsticks with garlic butter", "price": 35, "category": sides_cat, "rating": 4.5, "review_count": 92},
    
    # Desserts
    {"name": "Double Choco Brownie", "description": "Rich chocolate brownie with ice cream", "price": 45, "category": desserts_cat, "rating": 4.9, "review_count": 134},
    
    # Beverages
    {"name": "Fresh Ginger Beer", "description": "Homemade ginger beer", "price": 20, "category": beverages_cat, "rating": 4.6, "review_count": 87},
]

for item_data in menu_items_data:
    MenuItem.objects.create(restaurant=restaurant, **item_data)

print(f"Created {MenuItem.objects.count()} menu items")

print("\n✅ Sample data creation complete!")
print("\nYou can now:")
print("1. Create a superuser: python manage.py createsuperuser")
print("2. Run the server: python manage.py runserver")
print("3. Visit: http://127.0.0.1:8000")
print("4. Admin panel: http://127.0.0.1:8000/admin")
