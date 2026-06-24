import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering_system.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Address

u = User.objects.filter(username='test_sender').first()
if not u:
    print('No test_sender')
else:
    print('Addresses count for test_sender:', Address.objects.filter(customer__user=u).count())
