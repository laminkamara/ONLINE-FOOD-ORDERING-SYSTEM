import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import transaction
from django.db import models
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Avg
from django.db.models import Prefetch
from django.urls import reverse
from .models import Customer, Restaurant, MenuItem, Cart, CartItem, Order, OrderItem, Branch, Table, Category, ChatMessage, Payment, Address, DeliveryPerson, Notification
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count
from django.utils.dateparse import parse_date


# Helper function to determine user role
def get_user_role(user):
    """Determine user role based on permissions or groups.

    Values:
      - admin = superuser
      - delivery = member of "Delivery" group
      - waitress = member of "Waitress" group
      - customer = default
    """
    if user.is_superuser:
        return 'admin'
    if user.groups.filter(name='Delivery').exists():
        return 'delivery'
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


def get_or_create_delivery_person(user):
    """Return a DeliveryPerson object for the authenticated delivery user."""
    if not user.is_authenticated:
        return None
    delivery_person = getattr(user, 'delivery_person', None)
    if delivery_person is None:
        delivery_person, _ = DeliveryPerson.objects.get_or_create(user=user)
    return delivery_person


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
            elif role == 'delivery':
                messages.success(request, 'Welcome back, Delivery Partner!')
                return redirect('delivery_dashboard')
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
    elif role == 'delivery':
        return redirect('delivery_dashboard')
    else:
        return redirect('customer_dashboard')


@login_required
def delivery_dashboard(request):
    """Delivery partner dashboard for active delivery tasks and live location."""
    if not request.user.groups.filter(name='Delivery').exists():
        return redirect('dashboard')

    delivery_profile, _ = DeliveryPerson.objects.get_or_create(user=request.user)
    assigned_orders_base = Order.objects.filter(delivery_person=request.user).order_by('-created_at')
    assigned_orders = assigned_orders_base
    status_filter = request.GET.get('status_filter', '').strip().lower()

    if status_filter == 'pending':
        assigned_orders = assigned_orders_base.filter(status__in=['received', 'preparing'])
    elif status_filter == 'on_the_way':
        assigned_orders = assigned_orders_base.filter(status='on_the_way')
    elif status_filter == 'completed':
        assigned_orders = assigned_orders_base.filter(status='delivered')

    available_orders = Order.objects.filter(delivery_person__isnull=True, status__in=['received', 'preparing', 'ready', 'on_the_way']).order_by('-created_at')[:10]
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'delivery_profile': delivery_profile,
        'assigned_orders': assigned_orders,
        'available_orders': available_orders,
        'unread_notifications': unread_notifications,
        'status_filter': status_filter,
        # Task summary counts for dashboard
        'assigned_total_count': assigned_orders_base.count(),
        'assigned_pending_count': assigned_orders_base.filter(status__in=['received','preparing']).count(),
        'assigned_on_the_way_count': assigned_orders_base.filter(status='on_the_way').count(),
        'assigned_completed_count': assigned_orders_base.filter(status='delivered').count(),
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/delivery_dashboard.html', context)


@login_required
def assign_order(request, order_id):
    """Assign an order to a delivery person (admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        delivery_user_id = request.POST.get('delivery_person')
        set_on_the_way = request.POST.get('set_on_the_way') == 'on'

        if delivery_user_id:
            try:
                user = User.objects.get(id=int(delivery_user_id))
                order.delivery_person = user
                if set_on_the_way:
                    order.status = 'on_the_way'
                order.save()
                create_notification(user, f'You have been assigned order #{order.order_number}.', reverse('delivery_dashboard'))
                messages.success(request, f'Order #{order.order_number} assigned to {user.get_full_name() or user.username}.')
            except User.DoesNotExist:
                messages.error(request, 'Selected delivery person not found.')
        else:
            messages.error(request, 'No delivery person selected.')

    return redirect('manage_orders')


@login_required
def delivery_update_location(request):
    if not request.user.groups.filter(name='Delivery').exists():
        return redirect('dashboard')

    if request.method == 'POST':
        delivery_profile, _ = DeliveryPerson.objects.get_or_create(user=request.user)

        content_type = request.META.get('CONTENT_TYPE', '')
        if content_type.startswith('application/json'):
            try:
                data = json.loads(request.body.decode('utf-8') or '{}')
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        else:
            data = request.POST

        latitude = data.get('latitude')
        longitude = data.get('longitude')
        status = data.get('status')

        if latitude:
            delivery_profile.current_latitude = float(latitude)
        if longitude:
            delivery_profile.current_longitude = float(longitude)
        if status in dict(DeliveryPerson.STATUS_CHOICES):
            delivery_profile.status = status

        delivery_profile.save()

        if request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Delivery location updated successfully',
                'latitude': float(delivery_profile.current_latitude) if delivery_profile.current_latitude else None,
                'longitude': float(delivery_profile.current_longitude) if delivery_profile.current_longitude else None,
                'status': delivery_profile.status,
            })

        messages.success(request, 'Delivery status updated successfully.')

    return redirect('delivery_dashboard')


@login_required
@require_http_methods(['POST'])
def upload_delivery_proof(request, order_number):
    if not request.user.groups.filter(name='Delivery').exists():
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

    order = get_object_or_404(Order, order_number=order_number, delivery_person=request.user)

    proof_image = request.FILES.get('proof_image')
    if not proof_image:
        return JsonResponse({'success': False, 'message': 'No proof image uploaded'}, status=400)

    order.delivery_proof = proof_image
    order.save()

    return JsonResponse({'success': True, 'message': 'Proof uploaded successfully'})


@login_required
def notifications(request):
    notifications_list = Notification.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'notifications': notifications_list,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/notifications.html', context)


@login_required
def notifications_unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    if notification.url:
        return redirect(notification.url)
    return redirect('notifications')


def create_notification(user, message, url=''):
    Notification.objects.create(user=user, message=message, url=url)


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
        gps_latitude = request.POST.get('gps_latitude', '').strip()
        gps_longitude = request.POST.get('gps_longitude', '').strip()

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
                customer_latitude=Decimal(gps_latitude) if gps_latitude else None,
                customer_longitude=Decimal(gps_longitude) if gps_longitude else None,
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

    # Handle rating submission
    if request.method == 'POST' and order.status == 'delivered' and not request.user.groups.filter(name='Waitress').exists():
        rating = request.POST.get('rating')
        feedback = request.POST.get('feedback', '').strip()

        if rating:
            try:
                order.customer_rating = Decimal(rating)
                order.customer_feedback = feedback
                order.save()

                # Propagate order-level rating to menu items in the order
                try:
                    new_rating = Decimal(rating)
                    for oi in order.items.select_related('menu_item').all():
                        mi = oi.menu_item
                        current_total = (mi.rating or Decimal('0')) * mi.review_count
                        updated_count = mi.review_count + 1
                        updated_total = current_total + new_rating
                        # update rating to one decimal place
                        mi.rating = (updated_total / updated_count).quantize(Decimal('0.1'))
                        mi.review_count = updated_count
                        mi.save()
                except Exception:
                    pass
                messages.success(request, 'Thank you for rating your order!')
                return redirect('order_detail', order_id=order_id)
            except Exception:
                messages.error(request, 'Unable to submit rating. Please try again.')
        else:
            messages.error(request, 'Please select a rating before submitting.')

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
    if request.user.groups.filter(name='Delivery').exists():
        delivery_profile = get_or_create_delivery_person(request.user)
        if request.method == 'POST':
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            phone = request.POST.get('phone', '')
            status = request.POST.get('status', delivery_profile.status)
            profile_photo = request.FILES.get('profile_photo')

            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()

            delivery_profile.phone = phone
            delivery_profile.status = status if status in dict(DeliveryPerson.STATUS_CHOICES) else delivery_profile.status
            if profile_photo:
                delivery_profile.profile_photo = profile_photo
            delivery_profile.save()

            messages.success(request, 'Profile updated successfully')
            return redirect('profile')

        context = {
            'delivery_profile': delivery_profile,
            'user_role': get_user_role(request.user),
        }
        return render(request, 'core/delivery_profile.html', context)

    customer = get_or_create_customer(request.user)
    if customer is None:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('home')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        profile_photo = request.FILES.get('profile_photo')

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()

        customer.phone = phone
        customer.address = address
        if profile_photo:
            customer.profile_photo = profile_photo
        customer.save()

        messages.success(request, 'Profile updated successfully')
        return redirect('profile')

    context = {'customer': customer, 'user_role': get_user_role(request.user)}
    return render(request, 'core/profile.html', context)


# Live Chat Views
@login_required
def live_chat(request):
    """Live chat interface for customers and staff"""
    user = request.user
    partner_id = request.GET.get('partner_id')
    user_role = get_user_role(user)

    if user_role == 'customer':
        # Customer - show list of staff to chat with (admins + waitresses + delivery staff)
        chat_partners = User.objects.filter(
            models.Q(is_superuser=True) |
            models.Q(groups__name__in=['Waitress', 'Delivery']) |
            models.Q(sent_messages__receiver=user) |
            models.Q(received_messages__sender=user)
        ).exclude(id=user.id).distinct()
    elif user_role == 'delivery':
        # Delivery users should see assigned order customers plus any existing chat partners
        chat_partners = User.objects.filter(
            models.Q(sent_messages__receiver=user) |
            models.Q(received_messages__sender=user) |
            models.Q(customer__orders__delivery_person=user)
        ).exclude(id=user.id).distinct()
    else:
        # Admin and waitress users should chat with all customers that have orders or existing chats
        chat_partners = User.objects.filter(
            models.Q(sent_messages__receiver=user) |
            models.Q(received_messages__sender=user) |
            models.Q(customer__orders__isnull=False)
        ).exclude(id=user.id).distinct()

    if partner_id:
        selected_partner = User.objects.filter(id=partner_id).first()
        if selected_partner and not chat_partners.filter(id=selected_partner.id).exists():
            chat_partners = list(chat_partners) + [selected_partner]

    context = {
        'chat_partners': chat_partners,
        'user_role': user_role,
        'initial_partner_id': partner_id,
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
    delivery_group, _ = Group.objects.get_or_create(name='Delivery')
    for u in users:
        if u.is_superuser:
            role = 'superuser'
        elif delivery_group in u.groups.all():
            role = 'delivery'
        elif waitress_group in u.groups.all():
            role = 'waitress'
        elif u.is_staff:
            role = 'staff'
        else:
            role = 'customer'
        users_with_role.append({'user': u, 'role': role})

    context = {
        'users': users,
        'users_with_role': users_with_role,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'core/manage_users.html', context)


@login_required
def manage_menu(request):
    """Manage menu items (admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')

    
    # Prefetch recent customer reviews (orders with a customer rating) for each menu item
    review_qs = OrderItem.objects.select_related('order', 'order__customer__user').filter(order__customer_rating__gt=0).order_by('-order__created_at')
    menu_items = MenuItem.objects.all().order_by('category', 'name').prefetch_related(Prefetch('orderitem_set', queryset=review_qs, to_attr='reviews'))
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
    
    # Delivery persons for assign modal
    delivery_persons = DeliveryPerson.objects.select_related('user').all()

    context = {
        'orders': orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'completed_orders': completed_orders,
        'delivery_persons': delivery_persons,
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
    total_revenue = Order.objects.filter(status='delivered').aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    total_customers = Customer.objects.count()
    total_menu_items = MenuItem.objects.count()
    # Average order value (delivered orders)
    avg_order_value = Order.objects.filter(status='delivered').aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0')

    # Top selling items (by quantity ordered) and revenue
    revenue_expr = ExpressionWrapper(F('orderitem__quantity') * F('orderitem__price'), output_field=DecimalField(max_digits=14, decimal_places=2))
    top_items_qs = MenuItem.objects.annotate(
        times_ordered=Sum('orderitem__quantity'),
        revenue=Sum(revenue_expr)
    ).filter(times_ordered__isnull=False).order_by('-times_ordered')[:10]

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'total_menu_items': total_menu_items,
        'avg_order_value': avg_order_value,
        'top_items': top_items_qs,
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
    customer = get_or_create_customer(request.user)
    if customer is None:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('home')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        profile_photo = request.FILES.get('profile_photo')
        
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()
        
        customer.phone = phone
        if profile_photo:
            customer.profile_photo = profile_photo
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
            delivery_group, _ = Group.objects.get_or_create(name='Delivery')
            if role == 'superuser':
                user.is_superuser = True
                user.is_staff = True
                user.groups.remove(waitress_group, delivery_group)
                user.save()
            elif role == 'waitress':
                user.is_superuser = False
                user.is_staff = False
                user.groups.add(waitress_group)
                user.groups.remove(delivery_group)
                user.save()
            elif role == 'delivery':
                user.is_superuser = False
                user.is_staff = False
                user.groups.add(delivery_group)
                user.groups.remove(waitress_group)
                user.save()
                DeliveryPerson.objects.get_or_create(user=user)
            else:  # customer
                user.is_superuser = False
                user.is_staff = False
                user.groups.remove(waitress_group, delivery_group)
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
            delivery_group, _ = Group.objects.get_or_create(name='Delivery')
            if role == 'superuser':
                user.is_superuser = True
                user.is_staff = True
                user.groups.remove(waitress_group, delivery_group)
            elif role == 'waitress':
                user.is_superuser = False
                user.is_staff = False
                user.groups.add(waitress_group)
                user.groups.remove(delivery_group)
            elif role == 'delivery':
                user.is_superuser = False
                user.is_staff = False
                user.groups.add(delivery_group)
                user.groups.remove(waitress_group)
                DeliveryPerson.objects.get_or_create(user=user)
            else:  # customer
                user.is_superuser = False
                user.is_staff = False
                user.groups.remove(waitress_group, delivery_group)
                Customer.objects.get_or_create(user=user)

            user.save()
            messages.success(request, f'User {user.username} updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    return redirect('manage_users')


@login_required
def delivery_claim_order(request, order_id):
    if not request.user.groups.filter(name='Delivery').exists():
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id)
    if order.delivery_person is None and order.status in ['received', 'preparing', 'ready', 'on_the_way']:
        order.delivery_person = request.user
        order.status = 'on_the_way'
        order.save()
        create_notification(request.user, f'You have claimed order #{order.order_number}.', reverse('delivery_dashboard'))
        create_notification(order.customer.user, f'Your order #{order.order_number} is now on the way.', reverse('order_tracking', kwargs={'order_number': order.order_number}))
    return redirect('delivery_dashboard')


@login_required
def delivery_order_update_status(request, order_id):
    if not request.user.groups.filter(name='Delivery').exists():
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id, delivery_person=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['on_the_way', 'delivered']:
            order.status = new_status
            order.save()
            create_notification(order.customer.user, f'Your order #{order.order_number} status has been updated to {order.get_status_display()}.', reverse('order_tracking', kwargs={'order_number': order.order_number}))
            create_notification(request.user, f'Order #{order.order_number} status updated to {order.get_status_display()}.', reverse('delivery_dashboard'))
    return redirect('delivery_dashboard')


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
            # handle uploaded icon image
            icon_img = request.FILES.get('icon_image')
            if icon_img:
                category.icon_image = icon_img
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
            # handle uploaded icon image
            icon_img = request.FILES.get('icon_image')
            if icon_img:
                category.icon_image = icon_img
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


@login_required
def manage_reviews(request):
    """Admin page: list and filter customer reviews with pagination"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')

    qs = OrderItem.objects.select_related('menu_item', 'order', 'order__customer__user').filter(order__customer_rating__gt=0).order_by('-order__created_at')

    menu_item = request.GET.get('menu_item')
    min_rating = request.GET.get('min_rating')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if menu_item:
        qs = qs.filter(menu_item__id=menu_item)
    if min_rating:
        try:
            qs = qs.filter(order__customer_rating__gte=Decimal(min_rating))
        except Exception:
            pass
    if start_date:
        d = parse_date(start_date)
        if d:
            qs = qs.filter(order__created_at__date__gte=d)
    if end_date:
        d = parse_date(end_date)
        if d:
            qs = qs.filter(order__created_at__date__lte=d)

    paginator = Paginator(qs, 15)
    page = request.GET.get('page')
    reviews_page = paginator.get_page(page)

    menu_items_all = MenuItem.objects.all().order_by('name')

    context = {
        'reviews': reviews_page,
        'menu_items_all': menu_items_all,
        'user_role': get_user_role(request.user),
        'request': request,
    }
    return render(request, 'core/manage_reviews.html', context)


@login_required
def manage_review_edit(request, orderitem_id):
    """Edit a review (update order.customer_rating and customer_feedback) and recalc menu item aggregates"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')

    oi = get_object_or_404(OrderItem, id=orderitem_id)
    if request.method == 'POST':
        try:
            rating = request.POST.get('rating')
            feedback = request.POST.get('feedback', '')
            if rating is not None:
                oi.order.customer_rating = Decimal(rating)
            oi.order.customer_feedback = feedback
            oi.order.save()

            # Recalculate menu item aggregates
            mi = oi.menu_item
            agg = OrderItem.objects.filter(menu_item=mi, order__customer_rating__gt=0).aggregate(avg_rating=Avg('order__customer_rating'), cnt=Count('order__customer_rating'))
            if agg and agg['cnt']:
                mi.rating = Decimal(agg['avg_rating'] or 0).quantize(Decimal('0.1'))
                mi.review_count = agg['cnt']
            else:
                mi.rating = Decimal('0')
                mi.review_count = 0
            mi.save()
            messages.success(request, 'Review updated')
        except Exception as e:
            messages.error(request, f'Error updating review: {e}')
    return redirect('manage_reviews')


@login_required
def manage_review_delete(request, orderitem_id):
    """Remove rating/feedback from the order (soft delete) and recalc menu item aggregates"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('admin_dashboard')

    oi = get_object_or_404(OrderItem, id=orderitem_id)
    if request.method == 'POST':
        try:
            oi.order.customer_rating = Decimal('0')
            oi.order.customer_feedback = ''
            oi.order.save()

            mi = oi.menu_item
            agg = OrderItem.objects.filter(menu_item=mi, order__customer_rating__gt=0).aggregate(avg_rating=Avg('order__customer_rating'), cnt=Count('order__customer_rating'))
            if agg and agg['cnt']:
                mi.rating = Decimal(agg['avg_rating'] or 0).quantize(Decimal('0.1'))
                mi.review_count = agg['cnt']
            else:
                mi.rating = Decimal('0')
                mi.review_count = 0
            mi.save()
            messages.success(request, 'Review deleted')
        except Exception as e:
            messages.error(request, f'Error deleting review: {e}')
    return redirect('manage_reviews')


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


# LIVE LOCATION TRACKING API VIEWS
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def get_delivery_location(request, order_id):
    """Get delivery person's current location (JSON API)"""
    try:
        order = get_object_or_404(Order, id=order_id)
        
        if not order.delivery_person:
            return JsonResponse({'error': 'No delivery person assigned'}, status=404)
        
        delivery_profile = DeliveryPerson.objects.get(user=order.delivery_person)
        
        return JsonResponse({
            'success': True,
            'delivery': {
                'name': order.delivery_person.get_full_name() or order.delivery_person.username,
                'phone': delivery_profile.phone,
                'latitude': float(delivery_profile.current_latitude) if delivery_profile.current_latitude else None,
                'longitude': float(delivery_profile.current_longitude) if delivery_profile.current_longitude else None,
                'status': delivery_profile.status,
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_customer_location(request, order_number):
    """Get customer's current location during delivery (JSON API)"""
    try:
        order = get_object_or_404(Order, order_number=order_number)
        
        # Only delivery person assigned to this order can view customer location
        if request.user != order.delivery_person:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        return JsonResponse({
            'success': True,
            'customer': {
                'name': order.customer.user.get_full_name() or order.customer.user.username,
                'phone': order.phone,
                'latitude': float(order.customer_latitude) if order.customer_latitude else None,
                'longitude': float(order.customer_longitude) if order.customer_longitude else None,
                'address': order.delivery_address,
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def update_order_location(request, order_number):
    """Update customer's current location (from customer's device during ordering)"""
    try:
        data = json.loads(request.body)
        order = get_object_or_404(Order, order_number=order_number, customer__user=request.user)
        
        if 'latitude' in data and data['latitude']:
            order.customer_latitude = float(data['latitude'])
        if 'longitude' in data and data['longitude']:
            order.customer_longitude = float(data['longitude'])
        
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Location updated successfully',
            'latitude': float(order.customer_latitude) if order.customer_latitude else None,
            'longitude': float(order.customer_longitude) if order.customer_longitude else None,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@ensure_csrf_cookie
def order_live_map(request, order_number):
    """Display live map with delivery person and customer locations"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Verify user has access to this order
    is_customer = request.user == order.customer.user
    is_delivery = request.user == order.delivery_person
    is_admin = request.user.is_superuser
    
    if not (is_customer or is_delivery or is_admin):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    delivery_profile = None
    if order.delivery_person:
        delivery_profile = getattr(order.delivery_person, 'delivery_person', None)

    context = {
        'order': order,
        'delivery_profile': delivery_profile,
        'is_customer': is_customer,
        'is_delivery': is_delivery,
        'user_role': 'customer' if is_customer else 'delivery' if is_delivery else 'admin',
    }
    
    return render(request, 'core/order_live_map.html', context)
