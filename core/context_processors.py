from django.conf import settings
from .models import Customer, DeliveryPerson, Notification, ChatMessage


def user_role(request):
    """Expose a lightweight `user_role` string to templates.

    Values: 'admin', 'waitress', 'delivery', 'customer'. This mirrors the view helper logic.
    """
    role = 'customer'
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'user_role': role,
            'user_profile': None,
            'notification_count': 0,
            'unread_message_count': 0,
        }

    if user.is_superuser:
        role = 'admin'
    elif user.groups.filter(name='Delivery').exists():
        role = 'delivery'
    elif user.groups.filter(name='Waitress').exists():
        role = 'waitress'

    notification_count = Notification.objects.filter(user=user, is_read=False).count()
    unread_message_count = ChatMessage.objects.filter(receiver=user, is_read=False).count()

    if role == 'delivery':
        delivery_profile, _ = DeliveryPerson.objects.get_or_create(user=user)
        return {
            'user_role': role,
            'user_profile': delivery_profile,
            'notification_count': notification_count,
            'unread_message_count': unread_message_count,
        }

    user_profile, _ = Customer.objects.get_or_create(user=user)
    return {
        'user_role': role,
        'user_profile': user_profile,
        'notification_count': notification_count,
        'unread_message_count': unread_message_count,
    }
