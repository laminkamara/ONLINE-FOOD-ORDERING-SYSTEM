# 📸 Menu Item Image Management Guide

## For Administrators

This guide explains how to manage menu item images in the yoni Fast Food Restaurant admin panel.

---

## 🎯 Accessing the Admin Panel

1. **Login to Admin Panel**
   - URL: http://127.0.0.1:8000/admin/
   - Username: `admin`
   - Password: `admin123`

2. **Navigate to Menu Items**
   - Click on **"Menu Items"** under the **CORE** section
   - You'll see a list of all menu items with image previews

---

## 📷 Adding Images to Menu Items

### Method 1: Upload via Admin Panel (Recommended)

1. **Click on a Menu Item**
   - Find the item you want to edit
   - Click on the item name to open the edit form

2. **Upload Image**
   - Scroll to the **"Image"** section
   - Click **"Choose file"** or drag-and-drop an image
   - Recommended specifications:
     - **Size**: 800x600 pixels
     - **Format**: JPG or PNG
     - **File Size**: Under 500KB
     - **Quality**: High-resolution, well-lit food photos

3. **Preview the Image**
   - After selecting an image, you'll see a preview below the upload field
   - If satisfied, click **"Save"** at the bottom

4. **Save Changes**
   - Click **"Save"** to update the menu item
   - The image will now appear on the website

### Method 2: Bulk Upload via Script

For initial setup, use the provided script:

```bash
python add_images_to_menu.py
```

This script downloads high-quality images from Unsplash and assigns them to all menu items automatically.

**Note**: Some images may fail to download. You can manually upload those via the admin panel.

---

## 🔄 Updating Existing Images

1. **Go to Admin Panel** → Core → Menu Items
2. **Click on the item** you want to update
3. **In the Image section**:
   - Check the **"Clear"** box to remove the current image
   - Click **"Choose file"** to select a new image
4. **Click "Save"**

---

## 🖼️ Image Best Practices

### ✅ DO:
- Use high-quality, professional food photography
- Maintain consistent lighting across all images
- Use 800x600 pixel dimensions for optimal display
- Compress images to under 500KB for faster loading
- Show the actual dish being served
- Use natural, appetizing styling

### ❌ DON'T:
- Use blurry or pixelated images
- Use images with watermarks
- Use inconsistent image sizes
- Upload images larger than 2MB
- Use stock photos that don't match your actual food

---

## 🎨 Category-Specific Guidelines

### 🍔 Burgers
- Show the burger from a 45-degree angle
- Include visible ingredients (lettuce, tomato, cheese)
- Use a clean background

### 🍕 Pizza
- Top-down or slight angle view
- Show toppings clearly
- Include a slice being lifted (optional)

### 🍛 Local Dishes
- Show in traditional serving dishes
- Include garnishes and side items
- Highlight vibrant colors

### 🍗 Chicken
- Show crispy texture clearly
- Include dipping sauces if applicable
- Use warm lighting

### 🍰 Desserts
- Use bright, clean backgrounds
- Show texture (e.g., ice cream scoops, cake layers)
- Include garnishes (mint, berries)

### 🥤 Beverages
- Show in clear glass/cup
- Include ice or garnish (lemon slice, mint)
- Capture condensation for cold drinks

---

## 🔧 Troubleshooting

### Image Not Showing on Website?

1. **Check if image uploaded successfully**
   - Go to Admin → Menu Items → Click on item
   - Verify image preview appears

2. **Clear browser cache**
   - Press `Ctrl + Shift + Delete`
   - Clear cached images

3. **Check file format**
   - Ensure image is JPG or PNG
   - Avoid WebP or other formats

4. **Verify media folder permissions**
   - Images should be in: `media/menu_items/`
   - Folder should be writable

### Image Looks Blurry?

- Original image may be too small
- Upload higher resolution (at least 800x600)
- Avoid stretching small images

### Image Upload Fails?

- Check file size (should be under 2MB)
- Verify image format (JPG/PNG)
- Check internet connection
- Try a different browser

---

## 📊 Image Statistics

As of the latest update:
- ✅ **25 out of 29** menu items have images
- ⚠️ **4 items** need manual image upload:
  - Beef Fried Rice
  - Crispy Peri-Peri Wings
  - Cheesy Garlic Breadsticks
  - Extra Fried Plantain

**To add images for these items:**
1. Go to Admin Panel → Menu Items
2. Find each item in the list
3. Click to edit
4. Upload an appropriate image
5. Save

---

## 🎯 Quick Reference

### Admin URL
```
http://127.0.0.1:8000/admin/
```

### Media Folder Location
```
c:\Users\Young Enginner\Desktop\ONLINE FOOD ORDERING SYSTEM\media\menu_items\
```

### Image Requirements
- **Dimensions**: 800x600 pixels (recommended)
- **Format**: JPG or PNG
- **Size**: Under 500KB
- **Quality**: High-resolution, professional

### Helpful Scripts
- `add_images_to_menu.py` - Bulk download images
- `retry_images.py` - Retry failed downloads

---

## 📞 Support

For technical issues with image uploads:
1. Check this guide first
2. Clear browser cache
3. Try a different image format
4. Contact technical support

---

**Last Updated**: June 9, 2026  
**Version**: 1.0
