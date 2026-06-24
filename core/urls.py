from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurant/<int:restaurant_id>/', views.restaurant_detail, name='restaurant_detail'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Customer pages
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:menu_item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_history, name='order_history'),
    path('profile/', views.profile, name='profile'),
    
    # Dashboard pages (role-based)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/waitress/', views.waitress_dashboard, name='waitress_dashboard'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    
    # Admin sidebar pages
    path('dashboard/users/', views.manage_users, name='manage_users'),
    path('dashboard/menu/', views.manage_menu, name='manage_menu'),
    path('dashboard/orders/', views.manage_orders, name='manage_orders'),
    path('dashboard/payments/', views.manage_payments, name='manage_payments'),
    path('dashboard/reports/', views.view_reports, name='view_reports'),
    path('dashboard/settings/', views.dashboard_settings, name='dashboard_settings'),
    
    # Customer sidebar pages
    path('dashboard/customer/orders/', views.customer_orders, name='customer_orders'),
    path('dashboard/customer/profile/', views.customer_profile, name='customer_profile'),
    path('dashboard/customer/addresses/', views.customer_addresses, name='customer_addresses'),
    path('dashboard/customer/addresses/add/', views.add_address, name='add_address'),
    path('dashboard/customer/addresses/<int:address_id>/edit/', views.edit_address, name='edit_address'),
    path('dashboard/customer/addresses/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    
    # Waitress pages
    path('dashboard/waitress/floor-map/', views.floor_map, name='floor_map'),
    path('dashboard/waitress/active-orders/', views.active_orders, name='active_orders'),
    path('order-queue/', views.order_queue, name='order_queue'),
    
    # Order tracking
    path('track/<str:order_number>/', views.order_tracking, name='order_tracking'),
    
    # CRUD Operations - Users
    path('user/create/', views.user_create, name='user_create'),
    path('user/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('user/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('user/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    
    # CRUD Operations - Menu Items
    path('menu-item/create/', views.menu_item_create, name='menu_item_create'),
    path('menu-item/<int:item_id>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('menu-item/<int:item_id>/delete/', views.menu_item_delete, name='menu_item_delete'),
    
    # CRUD Operations - Branches
    path('branch/create/', views.branch_create, name='branch_create'),
    path('branch/<int:branch_id>/edit/', views.branch_edit, name='branch_edit'),
    path('branch/<int:branch_id>/delete/', views.branch_delete, name='branch_delete'),
    
    # CRUD Operations - Tables
    path('table/create/', views.table_create, name='table_create'),
    path('table/<int:table_id>/edit/', views.table_edit, name='table_edit'),
    path('table/<int:table_id>/delete/', views.table_delete, name='table_delete'),
    path('table/<int:table_id>/update-status/', views.table_update_status, name='table_update_status'),
    
    # CRUD Operations - Orders
    path('order/<int:order_id>/edit/', views.order_edit, name='order_edit'),
    path('order/<int:order_id>/delete/', views.order_delete, name='order_delete'),
    path('order/<int:order_id>/update-status/', views.order_update_status, name='order_update_status'),
    
    # CRUD Operations - Categories
    path('category/create/', views.category_create, name='category_create'),
    path('category/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('category/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    
    # CRUD Operations - Payments
    path('payment/<int:payment_id>/update-status/', views.payment_update_status, name='payment_update_status'),
    
    # Live Chat
    path('chat/', views.live_chat, name='live_chat'),
    path('chat/send/', views.send_message, name='send_message'),
    path('chat/messages/<int:user_id>/', views.get_messages, name='get_messages'),
    path('chat/unread/', views.get_unread_count, name='get_unread_count'),
]
