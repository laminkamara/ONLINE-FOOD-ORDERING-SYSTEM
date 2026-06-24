from django.conf import settings


def user_role(request):
    """Expose a lightweight `user_role` string to templates.

    Values: 'admin', 'waitress', 'customer'. This mirrors the view helper logic.
    """
    role = 'customer'
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'user_role': role}

    if user.is_superuser:
        role = 'admin'
    elif user.groups.filter(name='Waitress').exists():
        role = 'waitress'

    return {'user_role': role}
