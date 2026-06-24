from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Address(models.Model):
    """Multiple delivery addresses for a customer.

    Stored separately so users can add/edit/delete addresses.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=100, blank=True)
    address = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        try:
            return f"{self.customer.user.username} - {self.label or 'Address'}"
        except Exception:
            return f"Address {self.id}"


class Branch(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    opening_hours = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_table_count(self):
        return self.tables.count()


class Table(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='tables')
    table_number = models.CharField(max_length=10)
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    current_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reservation_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.branch.name} - Table {self.table_number}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    address = models.TextField()
    phone = models.CharField(max_length=15)
    image = models.ImageField(upload_to='restaurants/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='menu_items')
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True, help_text='Upload high-quality image (recommended: 800x600px)')
    is_available = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    review_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"
    
    def get_image_url(self):
        """Get image URL or placeholder based on category"""
        if self.image:
            return self.image.url
        # Return category-specific placeholder
        placeholders = {
            'Burgers': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400',
            'Pizza': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400',
            'Local Dishes': 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400',
            'Rice Dishes': 'https://images.unsplash.com/photo-1569056679459-0c2dba73ab5e?w=400',
            'Chicken': 'https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=400',
            'Sides': 'https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400',
            'Desserts': 'https://images.unsplash.com/photo-1567206563064-6f60f40a2b57?w=400',
            'Beverages': 'https://images.unsplash.com/photo-1544145945-f90425340c7e?w=400',
        }
        if self.category and self.category.name in placeholders:
            return placeholders[self.category.name]
        return 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400'  # Default


class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        try:
            return f"Cart {self.id} - {self.customer.user.username}"
        except Exception:
            return f"Cart {self.id}"

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def get_item_count(self):
        return self.items.count()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"

    def get_subtotal(self):
        return self.menu_item.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('received', 'Order Received'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('on_the_way', 'On Its Way'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_address = models.TextField()
    phone = models.CharField(max_length=15)
    order_number = models.CharField(max_length=20, unique=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=15000)
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    courier_name = models.CharField(max_length=100, blank=True)
    courier_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    customer_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    customer_feedback = models.TextField(blank=True)
    estimated_time = models.PositiveIntegerField(default=30)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        try:
            return f"Order {self.order_number} - {self.customer.user.username}"
        except Exception:
            return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            last_order = Order.objects.all().order_by('-id').first()
            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1001
            self.order_number = f"YONI-{new_num}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"

    def get_subtotal(self):
        return self.price * self.quantity


class ChatMessage(models.Model):
    """Live chat messages between customers and staff"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"


class Payment(models.Model):
    """Payment transactions for orders"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash on Delivery'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Money'),
        ('orange_money', 'Orange Money'),
        ('afrimoney', 'Afrimoney'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    receipt_image = models.ImageField(upload_to='payment_receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        try:
            return f"Payment {self.id} - Order {self.order.order_number}"
        except Exception:
            return f"Payment {self.id}"
    
    def get_payment_method_display(self):
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method)
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status)
