"""
Live Location Tracking API Views
For delivery person tracking and customer location sharing during order
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Order, DeliveryPerson
import json
import os


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
def order_live_map(request, order_number):
    """Display live map with delivery person and customer locations"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Verify user has access to this order
    is_customer = request.user == order.customer.user
    is_delivery = request.user == order.delivery_person
    is_admin = request.user.is_superuser
    
    if not (is_customer or is_delivery or is_admin):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    context = {
        'order': order,
        'is_customer': is_customer,
        'is_delivery': is_delivery,
        'user_role': 'customer' if is_customer else 'delivery' if is_delivery else 'admin',
    }
    
    return render(request, 'core/order_live_map.html', context)
