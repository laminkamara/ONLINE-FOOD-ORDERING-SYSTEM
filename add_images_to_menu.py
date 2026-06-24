"""
Add Images to Menu Items Script
Downloads and assigns high-quality images to all menu items from Unsplash
Run: python add_images_to_menu.py
"""

import os
import requests
from io import BytesIO
from django.core.files.base import ContentFile
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering_system.settings')
django.setup()

from core.models import MenuItem

# Image mapping for each menu item (Unsplash free images)
ITEM_IMAGES = {
    # Burgers
    "The Yoni Burger": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800",
    "Spicy Zinger Burger": "https://images.unsplash.com/photo-1513185158878-8d8c2a2a3da3?w=800",
    "Garden Fresh Veggie Burger": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=800",
    "Double Cheese Burger": "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=800",
    
    # Pizza
    "Large Pepperoni Feast": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=800",
    "Beef Suya Pizza": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800",
    "Margherita Classic": "https://images.unsplash.com/photo-1604382355076-af4b0eb60143?w=800",
    "BBQ Chicken Pizza": "https://images.unsplash.com/photo-1593560708920-61dd98c46a4e?w=800",
    
    # Local Dishes
    "Classic Jollof with Grilled Chicken": "https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=800",
    "Supreme Jollof Box": "https://images.unsplash.com/photo-1596797038530-2c107229654b?w=800",
    "Cassava Leaf with Rice": "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=800",
    
    # Rice Dishes
    "Fried Rice & Plantain Special": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=800",
    "Beef Fried Rice": "https://images.unsplash.com/photo-1516673454558-365267d2a3ce?w=800",
    "Chicken Biryani": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800",
    
    # Chicken
    "Crispy Peri-Peri Wings": "https://images.unsplash.com/photo-1527477396000-e27163b481c2?w=800",
    "Grilled Chicken Quarter": "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=800",
    "Chicken Wings (6 pcs)": "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=800",
    
    # Sides
    "Cheesy Garlic Breadsticks": "https://images.unsplash.com/photo-1619535860434-ba1d7fa86466?w=800",
    "French Fries (Large)": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=800",
    "Coleslaw": "https://images.unsplash.com/photo-1623428187969-5da2dcea5ebf?w=800",
    "Extra Fried Plantain": "https://images.unsplash.com/photo-1528739313424-66d8c0356602?w=800",
    
    # Desserts
    "Double Choco Brownie": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=800",
    "Vanilla Ice Cream": "https://images.unsplash.com/photo-1567206563064-6f60f40a2b57?w=800",
    "Fruit Salad": "https://images.unsplash.com/photo-1564093497595-593b96d80571?w=800",
    
    # Beverages
    "Fresh Ginger Beer": "https://images.unsplash.com/photo-1544145945-f90425340c7e?w=800",
    "Hibiscus Juice (Bissap)": "https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=800",
    "Fresh Lemonade": "https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=800",
    "Coca-Cola (500ml)": "https://images.unsplash.com/photo-1554866585-908004945a94?w=800",
    "Mineral Water": "https://images.unsplash.com/photo-1564419320461-6870880221ad?w=800",
}

def download_and_assign_image(item, image_url):
    """Download image from URL and assign to menu item"""
    try:
        print(f"  📥 Downloading: {item.name}...")
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Get filename from URL or create one
        filename = f"{item.name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.jpg"
        
        # Save to Django ImageField
        item.image.save(filename, ContentFile(response.content), save=True)
        print(f"  ✅ Saved: {filename}")
        return True
    except Exception as e:
        print(f"  ❌ Error downloading {item.name}: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("🖼️  ADD IMAGES TO MENU ITEMS")
    print("=" * 70)
    print()
    
    # Get all menu items
    menu_items = MenuItem.objects.all()
    total_items = menu_items.count()
    
    print(f"Found {total_items} menu items")
    print()
    
    # Track progress
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for item in menu_items:
        print(f"\nProcessing: {item.name}")
        
        # Skip if already has image
        if item.image:
            print(f"  ⏭️  Skipped (already has image)")
            skip_count += 1
            continue
        
        # Check if we have a mapping for this item
        if item.name in ITEM_IMAGES:
            image_url = ITEM_IMAGES[item.name]
            if download_and_assign_image(item, image_url):
                success_count += 1
            else:
                error_count += 1
        else:
            print(f"  ⚠️  No image mapping found for '{item.name}'")
            error_count += 1
    
    # Summary
    print()
    print("=" * 70)
    print("✅ IMAGE ASSIGNMENT COMPLETE!")
    print("=" * 70)
    print()
    print(f"Results:")
    print(f"  • Total Items: {total_items}")
    print(f"  • ✅ Successfully Added: {success_count}")
    print(f"  • ⏭️  Skipped (had images): {skip_count}")
    print(f"  • ❌ Errors: {error_count}")
    print()
    print(f"Images saved to: media/menu_items/")
    print()
    print("Next steps:")
    print("  1. Visit Django Admin: http://127.0.0.1:8000/admin/")
    print("  2. Go to Core > Menu Items")
    print("  3. You'll see image previews in the list")
    print("  4. Click on any item to edit/upload new images")
    print()

if __name__ == "__main__":
    main()
