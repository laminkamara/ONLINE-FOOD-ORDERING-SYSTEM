import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering_system.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from core.models import Customer, Address


def ensure_user(username, password, is_staff=False, is_superuser=False):
    u, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@example.com'})
    if created:
        u.set_password(password)
        u.is_staff = is_staff
        u.is_superuser = is_superuser
        u.save()
    else:
        if not u.check_password(password):
            u.set_password(password)
            u.save()
    return u


print('Setting up test users...')
sender = ensure_user('test_sender', 'testpass123')
receiver = ensure_user('test_receiver', 'testpass123')

# Ensure Customer profiles exist
for u in (sender, receiver):
    Customer.objects.get_or_create(user=u)

client = Client()
print('Logging in as sender...')
login_ok = client.login(username='test_sender', password='testpass123')
print('Login success:', login_ok)

print('Sending chat message via /chat/send/ ...')
resp = client.post('/chat/send/', {'receiver_id': receiver.id, 'message': 'Hello from test script'})
print('Status code:', resp.status_code)
try:
    print('JSON response:', resp.json())
except Exception:
    print('Response body:', resp.content[:500])

# Test address add/edit/delete
print('\nTesting address CRUD via client...')
add_resp = client.post('/dashboard/customer/addresses/add/', {'label': 'Home', 'address': '123 Test St', 'is_default': 'on'})
print('Add address status:', add_resp.status_code)
addresses = Address.objects.filter(customer__user=sender)
print('Address count after add:', addresses.count())
if addresses.exists():
    a = addresses.first()
    print('Editing address id', a.id)
    edit_resp = client.post(f'/dashboard/customer/addresses/{a.id}/edit/', {'label': 'Home Edited', 'address': '456 Edited St', 'is_default': 'on'})
    print('Edit status:', edit_resp.status_code)
    a.refresh_from_db()
    print('New address value:', a.address)

    del_resp = client.post(f'/dashboard/customer/addresses/{a.id}/delete/')
    print('Delete status:', del_resp.status_code)
    print('Address count after delete:', Address.objects.filter(customer__user=sender).count())

print('\nTest script finished.')
