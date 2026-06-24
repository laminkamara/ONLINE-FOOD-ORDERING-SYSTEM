from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, Branch, Table, Category, Restaurant, MenuItem, Cart, CartItem, Order, OrderItem, ChatMessage, Payment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'address', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'phone', 'opening_hours', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'address', 'phone']


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'branch', 'capacity', 'status', 'current_bill']
    list_filter = ['status', 'branch']
    search_fields = ['table_number', 'branch__name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description', 'address']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'category', 'price', 'image_preview', 'is_available', 'is_popular', 'is_new', 'rating']
    list_filter = ['category', 'is_available', 'is_popular', 'is_new', 'restaurant']
    search_fields = ['name', 'description']
    list_editable = ['is_popular', 'is_new', 'is_available']
    readonly_fields = ['image_preview', 'created_at']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('restaurant', 'name', 'description', 'category')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'is_available')
        }),
        ('Image', {
            'fields': ('image', 'image_preview'),
            'description': 'Upload a high-quality image for this menu item. Recommended size: 800x600 pixels.'
        }),
        ('Marketing', {
            'fields': ('is_popular', 'is_new', 'rating', 'review_count')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px; border-radius: 10px; object-fit: cover;" />',
                obj.image.url
            )
        return format_html('<span style="color: #999;">No Image</span>')
    
    image_preview.short_description = 'Image Preview'
    image_preview.allow_tags = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'created_at', 'updated_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'cart', 'quantity', 'get_subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'restaurant', 'branch', 'table', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'restaurant', 'branch', 'created_at']
    search_fields = ['order_number', 'customer__user__username', 'restaurant__name']
    list_editable = ['status']
    readonly_fields = ['order_number']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'quantity', 'price', 'get_subtotal']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'message_preview', 'is_read', 'timestamp']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['sender__username', 'receiver__username', 'message']
    readonly_fields = ['timestamp']
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    
    message_preview.short_description = 'Message'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'payment_method', 'transaction_id', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order__order_number', 'transaction_id']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at', 'receipt_image']
    fieldsets = (
        (None, {
            'fields': ('order', 'amount', 'payment_method', 'transaction_id', 'receipt_image', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
