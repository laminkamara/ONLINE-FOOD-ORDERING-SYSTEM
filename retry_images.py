"""
Retry failed image downloads with alternative URLs
"""

import os
import requests
from django.core.files.base import ContentFile
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering_system.settings')
django.setup()

from core.models import MenuItem

# Alternative image URLs for failed downloads
RETRY_IMAGES = {
    "BBQ Chicken Pizza": "https://images.unsplash.com/photo-1565299543923-37dd37887442?w=800",
    "Classic Jollof with Grilled Chicken": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",
    "Beef Fried Rice": "https://images.unsplash.com/photo-1569056679459-0c2dba73ab5e?w=800",
    "Crispy Peri-Peri Wings": "https://images.unsplash.com/photo-1608039829572-78cc2d4a1e80?w=800",
    "Cheesy Garlic Breadsticks": "https://images.unsplash.com/photo-1573140247632-f8fd74997d0c?w=800",
    "Extra Fried Plantain": "https://images.unsplash.com/photo-1565958011703-44f9829ba18b?w=800",
    "Fruit Salad": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=800",
    "Coca-Cola (500ml)": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=800",
}

def download_and_assign_image(item, image_url):
    """Download image from URL and assign to menu item"""
    try:
        print(f"  📥 Retrying: {item.name}...")
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()
        
        filename = f"{item.name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.jpg"
        item.image.save(filename, ContentFile(response.content), save=True)
        print(f"  ✅ Saved: {filename}")
        return True
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("🔄 RETRY FAILED IMAGE DOWNLOADS")
    print("=" * 70)
    print()
    
    success_count = 0
    
    for name, url in RETRY_IMAGES.items():
        try:
            item = MenuItem.objects.get(name=name)
            if not item.image:
                if download_and_assign_image(item, url):
                    success_count += 1
            else:
                print(f"  ⏭️  {name} already has an image")
        except MenuItem.DoesNotExist:
            print(f"  ⚠️  {name} not found")
    
    print()
    print("=" * 70)
    print(f"✅ RETRY COMPLETE: {success_count}/{len(RETRY_IMAGES)} successful")
    print("=" * 70)

if __name__ == "__main__":
    main()
