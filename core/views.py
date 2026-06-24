from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import transaction
from django.db import models
from .models import Customer, Restaurant, MenuItem, Cart, CartItem, Order, OrderItem, Branch, Table, Category, ChatMessage, Payment, Address
from django.http import JsonResponse


# Helper function to determine user role
def get_user_role(user):
    """Determine user role based on permissions or groups.

    IMPORTANT: Any user that is_staff is treated as *admin* in the old logic.
    We fix it so that:
      - admin = superuser (and optionally staff superusers)
      - waitress = member of "Waitress" group
      - customer = default
    """
    if user.is_superuser:
        return 'admin'

    if user.groups.filter(name='Waitress').exists():
        return 'waitress'

    return 'customer'


def get_or_create_customer(user):
    """Return a Customer object for the authenticated user, creating one if needed."""
    if not user.is_authenticated:
        return None
    customer = getattr(user, 'customer', None)
    if customer is None:
        customer, _ = Customer.objects.get_or_create(user=user)
    return customer


def home(request):
    restaurants = Restaurant.objects.filter(is_active=True)[:6]
    categories = Category.objects.all()[:6]
    popular_items = MenuItem.objects.filter(is_popular=True, is_available=True)[:6]
    context = {
        'restaurants': restaurants,
        'categories': categories,
        'popular_items': popular_items,
    }
    return render(request, 'core/home.html', context)


def about(request):
    """About page with company information"""
    return render(request, 'core/about.html')


def contact(request):
    """Contact page with form and information"""
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        subject = request.POST.get('subject', '')
        message_text = request.POST.get('message', '')
        
        # Here you can add logic to save contact form or send email
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
        return redirect('contact')
    
    return render(request, 'core/contact.html')


def restaurant_list(request):
    restaurants = Restaurant.objects.filter(is_active=True)
    categories = Category.objects.all()
    category_id = request.GET.get('category')
    selected_category = None
    menu_items = MenuItem.objects.filter(is_available=True)
    
    if category_id:
        selected_category = Category.objects.filter(id=category_id).first()
        restaurants = restaurants.filter(menu_items__category_id=category_id).distinct()
        menu_items = menu_items.filter(category_id=category_id)
    
    context = {
        'restaurants': restaurants,
        'categories': categories,
        'selected_category': selected_category,
        'menu_items': menu_items,
    }
    return render(request, 'core/restaurant_list.html', context)


def restaurant_detail(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id, is_active=True)
    menu_items = restaurant.menu_items.filter(is_available=True)
    category = request.GET.get('category')
    if category:
        menu_items = menu_items.filter(category=category)
    context = {
        'restaurant': restaurant,
        'menu_items': menu_items,
    }
    return render(request, 'core/restaurant_detail.html', context)


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')

        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('register')

        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
            Customer.objects.create(user=user, phone=phone, address=address)

        messages.success(request, 'Registration successful! Please login.')
        return redirect('login')

    return render(request, 'core/register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Merge any session cart into the user's DB cart
            try:
                merge_session_cart(request, user)
            except Exception:
                # Don't block login if merge fails for unexpected reasons
                pass

            # Role-based redirect (honour optional `next` param first)
            next_url = request.POST.get('next') or request.GET.get('next')
            role = get_user_role(user)

            if next_url:
                messages.success(request, 'Login successful!')
                return redirect(next_url)

            if role == 'admin':
                messages.success(request, 'Welcome back, Admin!')
                return redirect('admin_dashboard')
            elif role == 'waitress':
                messages.success(request, 'Welcome back!')
                return redirect('waitress_dashboard')
            else:
                messages.success(request, 'Login successful!')
                return redirect('customer_dashboard')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'core/login.html')


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('home')


# Dashboard routing based on role
@login_required
def dashboard(request):
    """Route user to appropriate dashboard based on role"""
    role = get_user_role(request.user)
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'waitress':
        return redirect('waitress_dashboard')
    else:
        return redirect('customer_dashboard')


# Admin Dashboard
@login_required
def admin_dashboard(request):
    """Admin dashboard for branch and table management"""
    # Admin-only.
    if not request.user.is_superuser:
        return redirect('dashboard')



    
    branches = Branch.objects.all()
    selected_branch_id = request.GET.get('branch')
    
    if selected_branch_id:
        selected_branch = get_object_or_404(Branch, id=selected_branch_id)
        tables = selected_branch.tables.all()
    else:
        selected_branch = branches.first()
        tables = selected_branch.tables.all() if selected_branch else []
    
    all_tables = Table.objects.all()
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()
    
    context = {
        'branches': branches,
        'selected_branch': selected_branch,
        'tables': tables,
        'all_tables': all_tables,
        'total_users': total_users,
        'active_users': active_users,
        'total_orders': total_orders,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/admin_dashboard.html', context)


# Waitress Dashboard
@login_required
def waitress_dashboard(request):
    """Waitress dashboard for table and order management"""
    if not request.user.groups.filter(name='Waitress').exists():
        return redirect('dashboard')


    
    branches = Branch.objects.all()
    selected_branch_id = request.GET.get('branch')
    
    if selected_branch_id:
        selected_branch = get_object_or_404(Branch, id=selected_branch_id)
        tables = selected_branch.tables.all()
    else:
        selected_branch = branches.first()
        tables = selected_branch.tables.all() if selected_branch else []
    
    # Get active orders
    active_orders = Order.objects.filter(status__in=['received', 'preparing', 'ready']).order_by('-created_at')
    
    context = {
        'branches': branches,
        'selected_branch': selected_branch,
        'tables': tables,
        'active_orders': active_orders,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/waitress_dashboard.html', context)


# Customer Dashboard
@login_required
def customer_dashboard(request):
    """Customer dashboard with order history and quick actions"""
    if not hasattr(request.user, 'customer'):
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('home')
    
    customer = request.user.customer
    recent_orders = Order.objects.filter(customer=customer).order_by('-created_at')[:5]
    total_orders = Order.objects.filter(customer=customer).count()
    total_spent = sum(order.total_amount for order in Order.objects.filter(customer=customer))
    
    context = {
        'customer': customer,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/customer_dashboard.html', context)


# Branch Management (Admin Only)
@login_required
def branch_management(request):
    """Create and manage branches"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('home')

    
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        opening_hours = request.POST.get('opening_hours')
        
        Branch.objects.create(
            name=name,
            address=address,
            phone=phone,
            opening_hours=opening_hours
        )
        messages.success(request, f'Branch "{name}" created successfully!')
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')


# Table Management (Admin Only)
@login_required
def table_management(request):
    """Create and manage tables"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('home')

    
    if request.method == 'POST':
        branch_id = request.POST.get('branch_id')
        table_number = request.POST.get('table_number')
        capacity = request.POST.get('capacity')
        
        branch = get_object_or_404(Branch, id=branch_id)
        Table.objects.create(
            branch=branch,
            table_number=table_number,
            capacity=int(capacity)
        )
        messages.success(request, f'Table {table_number} created successfully!')
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')


def add_to_cart(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_available=True)

    # If user is authenticated, use DB-backed cart as before
    if request.user.is_authenticated:
        customer = get_or_create_customer(request.user)
        cart, created = Cart.objects.get_or_create(customer=customer)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, menu_item=menu_item)
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        messages.success(request, f'{menu_item.name} added to cart')
        return redirect('cart')

    # Anonymous user: store cart in session and ask them to login
    session_cart = request.session.get('cart', {})
    item_id_str = str(menu_item_id)
    session_cart[item_id_str] = session_cart.get(item_id_str, 0) + 1
    request.session['cart'] = session_cart
    request.session.modified = True

    messages.info(request, f'{menu_item.name} added to cart. Please login or register to save your cart.')
    # Redirect to login page so user can complete authentication; preserve next to show cart after login
    return redirect(f"/login/?next=cart")


def merge_session_cart(request, user):
    """Merge items stored in session['cart'] into the authenticated user's DB cart.

    Session cart format: {"<menu_item_id>": quantity, ...}
    After merging, the session['cart'] key is removed.
    """
    customer = get_or_create_customer(user)
    if not customer:
        return

    session_cart = request.session.get('cart')
    if not session_cart:
        return

    customer = user.customer
    cart, created = Cart.objects.get_or_create(customer=customer)

    for item_id_str, qty in session_cart.items():
        try:
            menu_item = MenuItem.objects.get(id=int(item_id_str), is_available=True)
        except MenuItem.DoesNotExist:
            continue

        cart_item, created = CartItem.objects.get_or_create(cart=cart, menu_item=menu_item)
        if created:
            cart_item.quantity = int(qty)
        else:
            cart_item.quantity += int(qty)
        cart_item.save()

    # Remove session cart after successful merge
    try:
        del request.session['cart']
        request.session.modified = True
    except KeyError:
        pass


@login_required
def cart(request):
    customer = get_or_create_customer(request.user)
    cart, created = Cart.objects.get_or_create(customer=customer)
    context = {
        'cart': cart,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/cart.html', context)


@login_required
def update_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__customer=request.user.customer)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, 'Item removed from cart')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated')

    return redirect('cart')


@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__customer=request.user.customer)
    cart_item.delete()
    messages.success(request, 'Item removed from cart')
    return redirect('cart')


@login_required
def checkout(request):
    customer = get_or_create_customer(request.user)
    cart, created = Cart.objects.get_or_create(customer=customer)

    if not cart.items.exists():
        messages.error(request, 'Your cart is empty')
        return redirect('cart')

    user_role = get_user_role(request.user)
    branches = Branch.objects.filter(is_active=True) if user_role == 'waitress' else []
    tables = Table.objects.filter(status__in=['available', 'reserved']).order_by('branch__name', 'table_number') if user_role == 'waitress' else []

    # compute totals for display
    subtotal = cart.get_total()
    delivery_fee = Decimal(getattr(Order._meta.get_field('delivery_fee'), 'default', 0))
    try:
        delivery_fee = Decimal(delivery_fee)
    except Exception:
        delivery_fee = Decimal('0')

    gst = (subtotal * Decimal('0.05')).quantize(Decimal('1.'))
    total = subtotal + delivery_fee + gst

    if request.method == 'POST':
        delivery_address = request.POST.get('delivery_address', customer.address)
        phone = request.POST.get('phone', customer.phone)
        notes = request.POST.get('notes', '')
        table_id = request.POST.get('table')
        payment_method = request.POST.get('payment_method', 'mobile')
        transaction_id = request.POST.get('transaction_id', '').strip()
        receipt_image = request.FILES.get('receipt_image')

        first_item = cart.items.first()
        restaurant = first_item.menu_item.restaurant

        if table_id:
            table = get_object_or_404(Table, id=table_id)
            if not delivery_address:
                delivery_address = f'Table {table.table_number} at {table.branch.name}'
        else:
            table = None

        mobile_methods = ['mobile', 'orange_money', 'afrimoney']
        if payment_method in mobile_methods:
            if not transaction_id or not receipt_image:
                messages.error(request, 'Please provide your mobile money transaction code and upload the payment proof.')
                return redirect('checkout')

        with transaction.atomic():
            order = Order.objects.create(
                customer=customer,
                restaurant=restaurant,
                branch=table.branch if table else None,
                table=table,
                delivery_address=delivery_address,
                phone=phone,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                gst=gst,
                total_amount=total,
                notes=notes,
            )

            if table and table.status != 'occupied':
                table.status = 'occupied'
                table.save()

            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    menu_item=cart_item.menu_item,
                    quantity=cart_item.quantity,
                    price=cart_item.menu_item.price,
                )

            Payment.objects.create(
                order=order,
                amount=total,
                payment_method=payment_method,
                status='pending',
                transaction_id=transaction_id,
                receipt_image=receipt_image,
            )

            cart.items.all().delete()

        messages.success(request, 'Order placed successfully! Please keep your transaction code and proof for confirmation.')
        return redirect('order_detail', order_id=order.id)

    context = {
        'cart': cart,
        'customer': customer,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'gst': gst,
        'total': total,
        'branches': branches,
        'tables': tables,
        'user_role': user_role,
    }
    return render(request, 'core/checkout.html', context)


@login_required
def order_detail(request, order_id):
    if request.user.groups.filter(name='Waitress').exists() or request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)
    else:
        if not hasattr(request.user, 'customer'):
            messages.error(request, 'Customer profile not found. Please contact support.')
            return redirect('dashboard')
        order = get_object_or_404(Order, id=order_id, customer=request.user.customer)

    context = {
        'order': order,
        'user_role': get_user_role(request.user),
        'placed_by_waitress': order.customer.user.groups.filter(name='Waitress').exists(),
    }
    return render(request, 'core/order_detail.html', context)


@login_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user.customer).order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'core/order_history.html', context)


# Order Queue (Staff Only)
@login_required
def order_queue(request):
    """Order queue for staff to manage incoming orders"""
    if not request.user.groups.filter(name='Waitress').exists():
        return redirect('dashboard')

    
    # Filter orders based on status

    status_filter = request.GET.get('status', 'active')
    
    if status_filter == 'active':
        orders = Order.objects.filter(status__in=['received', 'preparing', 'ready']).order_by('-created_at')
    elif status_filter == 'new':
        orders = Order.objects.filter(status='received').order_by('-created_at')
    else:
        orders = Order.objects.all().order_by('-created_at')
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'user_role': get_user_role(request.user)
    }
    return render(request, 'core/order_queue.html', context)


# Order Tracking
@login_required
def order_tracking(request, order_number):
    """Track order status for customers and staff"""
    if request.user.is_superuser or request.user.groups.filter(name='Waitress').exists():
        order = get_object_or_404(Order, order_number=order_number)
    else:
        if not hasattr(request.user, 'customer'):
            messages.error(request, 'Customer profile not found. Please contact support.')
            return redirect('home')
        order = get_object_or_404(Order, order_number=order_number, customer=request.user.customer)

    if request.method == 'POST' and order.status == 'delivered':
        rating = request.POST.get('rating')
        feedback = request.POST.get('feedback', '').strip()

        if rating:
            try:
                order.customer_rating = Decimal(rating)
                order.customer_feedback = feedback
                order.save()
                messages.success(request, 'Thank you for rating your order!')
                return redirect('order_tracking', order_number=order_number)
            except Exception:
                messages.error(request, 'Unable to submit rating. Please try again.')
        else:
            messages.error(request, 'Please select a rating before submitting.')

    context = {'order': order}
    return render(request, 'core/order_tracking.html', context)


@login_required
def profile(request):
    if not hasattr(request.user, 'customer'):
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('home')
    
    customer = request.user.customer

    if request.method == 'POST':
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')

        customer.phone = phone
        customer.address = address
        customer.save()

        messages.success(request, 'Profile updated successfully')
        return redirect('profile')

    context = {'customer': customer}
    return render(request, 'core/profile.html', context)


# Live Chat Views
@login_required
def live_chat(request):
    """Live chat interface for customers and staff"""
    user = request.user
    
    # Get staff users for customer to chat with
    if not (user.is_superuser or user.groups.filter(name='Waitress').exists()):
        # Customer - show list of staff to chat with (admins + waitresses)
        staff_users = User.objects.filter(
            models.Q(is_superuser=True) | models.Q(groups__name='Waitress')
        ).exclude(id=user.id).distinct()
        chat_partners = staff_users
    else:
        # Staff - show all customers who have sent messages
        chat_partners = User.objects.filter(
            sent_messages__isnull=False
        ).exclude(id__in=User.objects.filter(is_superuser=True).values('id')).distinct()

    
    context = {
        'chat_partners': chat_partners,
        'user_role': get_user_role(user),
    }
    return render(request, 'core/live_chat.html', context)


@login_required
def send_message(request):
    """Send a chat message"""
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        message_text = request.POST.get('message', '').strip()
        
        if message_text and receiver_id:
            receiver = User.objects.get(id=receiver_id)
            ChatMessage.objects.create(
                sender=request.user,
                receiver=receiver,
                message=message_text
            )
            return JsonResponse({'success': True, 'message': 'Message sent'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def get_messages(request, user_id):
    """Get chat messages between current user and another user"""
    other_user = User.objects.get(id=user_id)
    
    # Get messages between the two users
    messages_list = ChatMessage.objects.filter(
        models.Q(sender=request.user, receiver=other_user) |
        models.Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')
    
    # Mark received messages as read
    messages_list.filter(sender=other_user, is_read=False).update(is_read=True)
    
    messages_data = [{
        'sender': msg.sender.username,
        'message': msg.message,
        'timestamp': msg.timestamp.strftime('%H:%M'),
        'is_mine': msg.sender == request.user,
    } for msg in messages_list]
    
    return JsonResponse({'messages': messages_data})


@login_required
def get_unread_count(request):
    """Get count of unread messages for current user"""
    count = ChatMessage.objects.filter(receiver=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})


# Admin Sidebar Pages
@login_required
def manage_users(request):
    """Manage all users (admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')

    
    users = User.objects.all().order_by('-date_joined')

    # Build list of users with computed role to simplify template logic
    users_with_role = []
    waitress_group, _ = Group.objects.get_or_create(name='Waitress')
    for u in users:
        if u.is_superuser:
            role = 'superuser'
        elif waitress_group in u.groups.all():
            role = 'waitress'
        elif u.is_staff:
            role = 'staff'
        else:
            role = 'customer'
        users_with_role.append({'user': u, 'role': role})

    context = {'users_with_role': users_with_role, 'user_role': get_user_role(request.user)}
    return render(request, 'core/manage_users.html', context)


@login_required
def manage_menu(request):
    """Manage menu items (admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')

    
    menu_items = MenuItem.objects.all().order_by('category', 'name')
    categories = Category.objects.all()
    restaurants = Restaurant.objects.all().order_by('name')
    context = {
        'menu_items': menu_items,
        'categories': categories,
        'restaurants': restaurants,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/manage_menu.html', context)


@login_required
def manage_orders(request):
    """Manage all orders (admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('home')

    
    orders = Order.objects.all().order_by('-created_at')
    pending_orders = orders.filter(status__in=['received']).count()
    processing_orders = orders.filter(status__in=['preparing', 'ready', 'on_the_way']).count()
    completed_orders = orders.filter(status='delivered').count()
    
    context = {
        'orders': orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'completed_orders': completed_orders,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/manage_orders.html', context)


@login_required
def manage_payments(request):
    """View payment history (admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')

    
    payments = Payment.objects.all().order_by('-created_at')
    total_revenue = sum(p.amount for p in payments.filter(status='completed'))
    completed_count = payments.filter(status='completed').count()
    pending_count = payments.filter(status='pending').count()
    
    context = {
        'payments': payments,
        'total_revenue': total_revenue,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/manage_payments.html', context)


@login_required
def view_reports(request):
    """View business reports (admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')

    
    # Basic stats
    total_orders = Order.objects.count()
    total_revenue = sum(order.total_amount for order in Order.objects.filter(status='delivered'))
    total_customers = Customer.objects.count()
    total_menu_items = MenuItem.objects.count()
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'total_menu_items': total_menu_items,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/view_reports.html', context)


@login_required
def dashboard_settings(request):
    """Dashboard settings (admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')

    
    context = {'user_role': get_user_role(request.user)}
    return render(request, 'core/dashboard_settings.html', context)


# Customer Pages
@login_required
def customer_orders(request):
    """View customer's order history"""
    if not hasattr(request.user, 'customer'):
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('home')
    
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    pending_count = orders.filter(status__in=['pending', 'received']).count()
    delivered_count = orders.filter(status='delivered').count()
    context = {
        'orders': orders,
        'pending_count': pending_count,
        'delivered_count': delivered_count,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/customer_orders.html', context)


@login_required
def customer_profile(request):
    """Edit customer profile"""
    if not hasattr(request.user, 'customer'):
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('home')
    
    customer = request.user.customer
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()
        
        customer.phone = phone
        customer.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('customer_profile')
    
    total_orders = Order.objects.filter(customer=customer).count()
    total_spent = sum(o.total_amount for o in Order.objects.filter(customer=customer))
    
    context = {
        'customer': customer,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/customer_profile.html', context)


@login_required
def customer_addresses(request):
    """Manage customer addresses"""
    if not hasattr(request.user, 'customer'):
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('home')
    
    customer = request.user.customer

    # Show addresses and handle add via separate endpoint; keep GET here
    addresses = list(customer.addresses.all())

    context = {
        'customer': customer,
        'addresses': addresses,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/customer_addresses.html', context)


@login_required
def add_address(request):
    if not hasattr(request.user, 'customer'):
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('home')
    
    if request.method == 'POST':
        customer = request.user.customer
        label = request.POST.get('label', '').strip()
        addr = request.POST.get('address', '').strip()
        is_default = bool(request.POST.get('is_default'))

        if not addr:
            messages.error(request, 'Address cannot be empty')
            return redirect('customer_addresses')

        if is_default:
            # unset other defaults
            customer.addresses.update(is_default=False)

        customer.addresses.create(label=label, address=addr, is_default=is_default)
        messages.success(request, 'Address added successfully!')
        return redirect('customer_addresses')

    return redirect('customer_addresses')


@login_required
def edit_address(request, address_id):
    if not hasattr(request.user, 'customer'):
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('home')
    
    address = get_object_or_404(Address, id=address_id, customer=request.user.customer)
    if request.method == 'POST':
        label = request.POST.get('label', '').strip()
        addr = request.POST.get('address', '').strip()
        is_default = bool(request.POST.get('is_default'))

        if not addr:
            messages.error(request, 'Address cannot be empty')
            return redirect('customer_addresses')

        if is_default:
            request.user.customer.addresses.update(is_default=False)

        address.label = label
        address.address = addr
        address.is_default = is_default
        address.save()
        messages.success(request, 'Address updated successfully!')
        return redirect('customer_addresses')

    # For non-POST, redirect back
    return redirect('customer_addresses')


@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, customer=request.user.customer)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted')
    return redirect('customer_addresses')


# Waitress Pages
@login_required
def floor_map(request):
    """View floor map and tables (waitress)"""
    if not request.user.groups.filter(name='Waitress').exists():
        return redirect('dashboard')

    branches = Branch.objects.filter(is_active=True)


    selected_branch_id = request.GET.get('branch')
    
    if selected_branch_id:
        selected_branch = Branch.objects.filter(id=selected_branch_id).first()
        tables = selected_branch.tables.all() if selected_branch else []
    else:
        selected_branch = branches.first()
        tables = selected_branch.tables.all() if selected_branch else []
    
    total_tables = sum(b.tables.count() for b in branches)
    available_tables = sum(b.tables.filter(status='available').count() for b in branches)
    
    context = {
        'branches': branches,
        'selected_branch': selected_branch,
        'tables': tables,
        'total_tables': total_tables,
        'available_tables': available_tables,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/floor_map.html', context)


@login_required
def active_orders(request):
    """View active orders for waitress"""
    if not request.user.groups.filter(name='Waitress').exists():
        return redirect('dashboard')

    orders = Order.objects.filter(status__in=['received', 'preparing', 'ready']).order_by('-created_at')


    pending_count = orders.filter(status__in=['received', 'pending']).count()
    preparing_count = orders.filter(status='preparing').count()
    context = {
        'orders': orders,
        'pending_count': pending_count,
        'preparing_count': preparing_count,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/active_orders.html', context)


# ============================================================================
# CRUD OPERATIONS - FULL FUNCTIONALITY
# ============================================================================

# USER CRUD OPERATIONS
@login_required
def user_create(request):
    """Create a new user (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        role = request.POST.get('role', 'customer')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            # Assign role
            waitress_group, _ = Group.objects.get_or_create(name='Waitress')
            if role == 'superuser':
                user.is_superuser = True
                user.is_staff = True
                user.save()
            elif role == 'waitress':
                user.is_superuser = False
                user.is_staff = False
                user.groups.add(waitress_group)
                user.save()
            else:  # customer
                user.is_superuser = False
                user.is_staff = False
                user.save()
                Customer.objects.create(user=user)

            messages.success(request, f'User {username} created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    return redirect('manage_users')


@login_required
def user_edit(request, user_id):
    """Edit user details (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email')
            role = request.POST.get('role', 'customer')

            waitress_group, _ = Group.objects.get_or_create(name='Waitress')
            if role == 'superuser':
                user.is_superuser = True
                user.is_staff = True
                user.groups.remove(waitress_group)
            elif role == 'waitress':
                user.is_superuser = False
                user.is_staff = False
                user.groups.add(waitress_group)
                # ensure customer profile removed if existed?
            else:  # customer
                user.is_superuser = False
                user.is_staff = False
                if waitress_group in user.groups.all():
                    user.groups.remove(waitress_group)
                # ensure Customer profile exists
                Customer.objects.get_or_create(user=user)

            user.save()
            messages.success(request, f'User {user.username} updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    return redirect('manage_users')


@login_required
def user_delete(request, user_id):
    """Delete a user (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
    
    return redirect('manage_users')


@login_required
def user_toggle_active(request, user_id):
    """Toggle user active/inactive status (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} {status} successfully!')
    
    return redirect('manage_users')


# MENU ITEM CRUD OPERATIONS
@login_required
def menu_item_create(request):
    """Create a new menu item (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        try:
            menu_item = MenuItem(
                restaurant_id=request.POST.get('restaurant'),
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                price=request.POST.get('price'),
                category_id=request.POST.get('category'),
                is_available=request.POST.get('is_available') == 'on',
                is_popular=request.POST.get('is_popular') == 'on',
                is_new=request.POST.get('is_new') == 'on',
            )
            if 'image' in request.FILES:
                menu_item.image = request.FILES['image']
            menu_item.save()
            messages.success(request, f'Menu item "{menu_item.name}" created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating menu item: {str(e)}')
    
    return redirect('manage_menu')


@login_required
def menu_item_edit(request, item_id):
    """Edit menu item (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    menu_item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        try:
            menu_item.name = request.POST.get('name')
            menu_item.description = request.POST.get('description')
            menu_item.price = request.POST.get('price')
            menu_item.restaurant_id = request.POST.get('restaurant')
            menu_item.category_id = request.POST.get('category')
            menu_item.is_available = request.POST.get('is_available') == 'on'
            menu_item.is_popular = request.POST.get('is_popular') == 'on'
            menu_item.is_new = request.POST.get('is_new') == 'on'
            if 'image' in request.FILES:
                menu_item.image = request.FILES['image']
            menu_item.save()
            messages.success(request, f'Menu item "{menu_item.name}" updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating menu item: {str(e)}')
    
    return redirect('manage_menu')


@login_required
def menu_item_delete(request, item_id):
    """Delete menu item (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    menu_item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        name = menu_item.name
        menu_item.delete()
        messages.success(request, f'Menu item "{name}" deleted successfully!')
    
    return redirect('manage_menu')


# BRANCH CRUD OPERATIONS
@login_required
def branch_create(request):
    """Create a new branch (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        try:
            opening_hours = request.POST.get('opening_hours') or request.POST.get('hours')
            branch = Branch(
                name=request.POST.get('name'),
                address=request.POST.get('address'),
                phone=request.POST.get('phone'),
                opening_hours=opening_hours,
                is_active=request.POST.get('is_active') == 'on'
            )
            branch.save()
            messages.success(request, f'Branch "{branch.name}" created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating branch: {str(e)}')
    
    return redirect('admin_dashboard')


@login_required
def branch_edit(request, branch_id):
    """Edit branch (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    branch = get_object_or_404(Branch, id=branch_id)
    
    if request.method == 'POST':
        try:
            branch.name = request.POST.get('name')
            branch.address = request.POST.get('address')
            branch.phone = request.POST.get('phone')
            branch.opening_hours = request.POST.get('opening_hours')
            branch.is_active = request.POST.get('is_active') == 'on'
            branch.save()
            messages.success(request, f'Branch "{branch.name}" updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating branch: {str(e)}')
    
    return redirect('admin_dashboard')


@login_required
def branch_delete(request, branch_id):
    """Delete branch (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    branch = get_object_or_404(Branch, id=branch_id)
    if request.method == 'POST':
        name = branch.name
        branch.delete()
        messages.success(request, f'Branch "{name}" deleted successfully!')
    
    return redirect('admin_dashboard')


# TABLE CRUD OPERATIONS
@login_required
def table_create(request):
    """Create a new table (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        try:
            branch_id = request.POST.get('branch') or request.POST.get('branch_id')
            table = Table(
                branch_id=branch_id,
                table_number=request.POST.get('table_number'),
                capacity=request.POST.get('capacity'),
                status=request.POST.get('status', 'available')
            )
            table.save()
            messages.success(request, f'Table {table.table_number} created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating table: {str(e)}')
    
    return redirect('admin_dashboard')


@login_required
def table_edit(request, table_id):
    """Edit table (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    table = get_object_or_404(Table, id=table_id)
    
    if request.method == 'POST':
        try:
            branch_id = request.POST.get('branch') or request.POST.get('branch_id')
            if branch_id:
                table.branch_id = branch_id
            table.table_number = request.POST.get('table_number')
            table.capacity = request.POST.get('capacity')
            table.status = request.POST.get('status', 'available')
            table.save()
            messages.success(request, f'Table {table.table_number} updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating table: {str(e)}')
    
    return redirect('admin_dashboard')


@login_required
def table_update_status(request, table_id):
    """Update table status for waitress staff"""
    if not (request.user.groups.filter(name='Waitress').exists() or request.user.is_superuser):
        messages.error(request, 'Permission denied')
        return redirect('dashboard')

    if request.method == 'POST':
        status = request.POST.get('status')
        if status not in ['available', 'occupied', 'reserved']:
            messages.error(request, 'Invalid table status.')
        else:
            table = get_object_or_404(Table, id=table_id)
            table.status = status
            table.save()
            messages.success(request, f'Table {table.table_number} updated to {table.get_status_display()}.')

    return redirect(request.META.get('HTTP_REFERER', 'waitress_dashboard'))


@login_required
def table_delete(request, table_id):
    """Delete table (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    table = get_object_or_404(Table, id=table_id)
    if request.method == 'POST':
        table_number = table.table_number
        table.delete()
        messages.success(request, f'Table {table_number} deleted successfully!')
    
    return redirect('admin_dashboard')


# ORDER CRUD OPERATIONS
@login_required
def order_edit(request, order_id):
    """Edit order details (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('customer_dashboard')

    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        try:
            order.delivery_address = request.POST.get('delivery_address')
            order.phone = request.POST.get('phone')
            order.notes = request.POST.get('notes', '')
            order.save()
            messages.success(request, f'Order #{order.order_number} updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating order: {str(e)}')
    
    return redirect('manage_orders')


@login_required
def order_delete(request, order_id):
    """Delete order (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'Order #{order_number} deleted successfully!')
    
    return redirect('manage_orders')


@login_required
def order_update_status(request, order_id):
    """Update order status (Admin or Waitress only)"""
    if not (request.user.is_superuser or request.user.groups.filter(name='Waitress').exists()):
        return redirect('dashboard')


    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        messages.success(request, f'Order #{order.order_number} status updated to {order.get_status_display()}!')
    
    return redirect('order_queue')


# CATEGORY CRUD OPERATIONS
@login_required
def category_create(request):
    """Create a new category (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        try:
            category = Category(
                name=request.POST.get('name'),
                icon=request.POST.get('icon', 'fas fa-utensils'),
                description=request.POST.get('description', '')
            )
            category.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating category: {str(e)}')
    
    return redirect('admin_dashboard')


@login_required
def category_edit(request, category_id):
    """Edit category (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        try:
            category.name = request.POST.get('name')
            category.icon = request.POST.get('icon', 'fas fa-utensils')
            category.description = request.POST.get('description', '')
            category.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
    
    return redirect('admin_dashboard')


@login_required
def category_delete(request, category_id):
    """Delete category (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')
    
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully!')
    
    return redirect('admin_dashboard')


# PAYMENT STATUS UPDATE
@login_required
def payment_update_status(request, payment_id):
    """Update payment status (Admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')

    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        payment.status = new_status
        payment.save()
        messages.success(request, f'Payment status updated to {payment.get_status_display()}!')
    
    return redirect('manage_payments')
