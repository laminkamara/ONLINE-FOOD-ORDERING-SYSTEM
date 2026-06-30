import os

import django
from django.contrib.auth.models import Group, User


# Ensure Django is configured when running as a script
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "food_ordering_system.settings")
django.setup()

from core.models import Customer  # noqa: E402


def ensure_group(name: str) -> Group:
    group, _ = Group.objects.get_or_create(name=name)
    return group


def ensure_customer_profile(user: User, phone: str = "", address: str = ""):
    Customer.objects.get_or_create(user=user, defaults={"phone": phone, "address": address})


def create_users():
    # 1) Groups
    waitress_group = ensure_group("Waitress")

    # 2) Admin user (superuser)
    admin_username = "admin"
    admin_password = "admin123"

    admin_user = User.objects.filter(username=admin_username).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username=admin_username,
            email="admin@yoni.com",
            password=admin_password,
        )
    else:
        # If user existed, make sure it has superuser access
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.set_password(admin_password)
        admin_user.save()

    # 3) Waitress user (group membership ONLY)
    waitress_username = "waitress"
    waitress_password = "waitress123"

    waitress_user = User.objects.filter(username=waitress_username).first()
    if not waitress_user:
        waitress_user = User.objects.create_user(
            username=waitress_username,
            email="waitress@yoni.com",
            password=waitress_password,
        )

    # IMPORTANT: We do not rely on is_staff for waitress role anymore.
    waitress_user.is_staff = False  # optional/consistent with new RBAC
    waitress_user.set_password(waitress_password)
    waitress_user.save()
    waitress_group.user_set.add(waitress_user)

    # 4) Customer user (has Customer profile, not staff)
    customer_username = "customer"
    customer_password = "customer123"

    customer_user = User.objects.filter(username=customer_username).first()
    if not customer_user:
        customer_user = User.objects.create_user(
            username=customer_username,
            email="customer@yoni.com",
            password=customer_password,
        )

    customer_user.is_staff = False
    customer_user.set_password(customer_password)
    customer_user.save()

    ensure_customer_profile(customer_user)


if __name__ == "__main__":
    create_users()
    print("Users created/updated:")
    print(" - admin / admin123")
    print(f'  Customer : {customer_username} / {customer_password}')

