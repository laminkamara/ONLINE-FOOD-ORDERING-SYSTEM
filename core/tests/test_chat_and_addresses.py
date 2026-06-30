from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from core.models import Customer, Address, ChatMessage, Order, OrderItem, Restaurant, MenuItem, Cart, CartItem, Notification, DeliveryPerson
from decimal import Decimal


class ChatAndAddressTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username='tc_sender', password='testpass')
        self.receiver = User.objects.create_user(username='tc_receiver', password='testpass')
        Customer.objects.get_or_create(user=self.sender)
        Customer.objects.get_or_create(user=self.receiver)
        self.client = Client()

    def test_live_chat_accepts_partner_id_without_query_combination_error(self):
        delivery_group, _ = Group.objects.get_or_create(name='Delivery')
        delivery_user = User.objects.create_user(username='tc_delivery', password='testpass')
        delivery_user.groups.add(delivery_group)
        delivery_user.save()

        self.client.login(username='tc_delivery', password='testpass')
        response = self.client.get('/chat/', {'partner_id': self.receiver.id})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select a conversation')

    def test_delivery_user_sees_assigned_customer_in_chat_list(self):
        delivery_group, _ = Group.objects.get_or_create(name='Delivery')
        delivery_user = User.objects.create_user(username='tc_delivery3', password='testpass')
        delivery_user.groups.add(delivery_group)
        delivery_user.save()
        DeliveryPerson.objects.get_or_create(user=delivery_user)

        restaurant = Restaurant.objects.create(name='Test Restaurant', address='1 Main', phone='123', is_active=True)
        customer = Customer.objects.get(user=self.sender)
        order = Order.objects.create(
            customer=customer,
            restaurant=restaurant,
            delivery_person=delivery_user,
            delivery_address='Test address',
            phone='+23212345678',
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.00'),
            status='received',
        )

        self.client.login(username='tc_delivery3', password='testpass')
        response = self.client.get('/chat/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sender.get_full_name() or self.sender.username)

    def test_customer_sees_delivery_partner_after_message(self):
        delivery_group, _ = Group.objects.get_or_create(name='Delivery')
        delivery_user = User.objects.create_user(username='tc_delivery4', password='testpass')
        delivery_user.groups.add(delivery_group)
        delivery_user.save()
        DeliveryPerson.objects.get_or_create(user=delivery_user)

        # delivery user sends a message to the customer
        ChatMessage.objects.create(sender=delivery_user, receiver=self.sender, message='Hello customer')

        self.client.login(username='tc_sender', password='testpass')
        response = self.client.get('/chat/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, delivery_user.username)

    def test_delivery_dashboard_status_filter_cards(self):
        delivery_group, _ = Group.objects.get_or_create(name='Delivery')
        delivery_user = User.objects.create_user(username='tc_delivery5', password='testpass')
        delivery_user.groups.add(delivery_group)
        delivery_user.save()
        DeliveryPerson.objects.get_or_create(user=delivery_user)

        restaurant = Restaurant.objects.create(name='Test Restaurant', address='1 Main', phone='123', is_active=True)
        customer = Customer.objects.get(user=self.sender)
        pending_order = Order.objects.create(
            customer=customer,
            restaurant=restaurant,
            delivery_person=delivery_user,
            delivery_address='Pending address',
            phone='+23212345678',
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.00'),
            status='received',
        )
        on_the_way_order = Order.objects.create(
            customer=customer,
            restaurant=restaurant,
            delivery_person=delivery_user,
            delivery_address='On the way address',
            phone='+23212345678',
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.00'),
            status='on_the_way',
        )
        delivered_order = Order.objects.create(
            customer=customer,
            restaurant=restaurant,
            delivery_person=delivery_user,
            delivery_address='Delivered address',
            phone='+23212345678',
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.00'),
            status='delivered',
        )

        self.client.login(username='tc_delivery5', password='testpass')
        response = self.client.get('/dashboard/delivery/', {'status_filter': 'pending'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual({order.id for order in response.context['assigned_orders']}, {pending_order.id})
        self.assertEqual(response.context['assigned_pending_count'], 1)
        self.assertEqual(response.context['assigned_on_the_way_count'], 1)
        self.assertEqual(response.context['assigned_completed_count'], 1)
        self.assertEqual(response.context['assigned_total_count'], 3)

    def test_checkout_persists_customer_gps_location(self):
        restaurant = Restaurant.objects.create(name='Test Restaurant', address='1 Main', phone='123', is_active=True)
        menu_item = MenuItem.objects.create(restaurant=restaurant, name='Pizza', description='Test', price=Decimal('10.00'))
        customer = Customer.objects.get(user=self.sender)
        cart = Cart.objects.create(customer=customer)
        CartItem.objects.create(cart=cart, menu_item=menu_item, quantity=1)

        self.client.login(username='tc_sender', password='testpass')
        response = self.client.post('/checkout/', {
            'delivery_address': 'Test address',
            'phone': '+23212345678',
            'payment_method': 'cash',
            'notes': 'Please arrive fast',
            'gps_latitude': '8.460600',
            'gps_longitude': '-13.231700',
        })

        self.assertEqual(response.status_code, 302)
        order = Order.objects.filter(customer=customer).latest('created_at')
        self.assertEqual(order.customer_latitude, Decimal('8.460600'))
        self.assertEqual(order.customer_longitude, Decimal(' -13.231700'.strip()))

    def test_assign_order_to_delivery_person_and_dashboard_counts(self):
        admin_user = User.objects.create_user(username='tc_admin', password='testpass', is_superuser=True, is_staff=True)
        delivery_group, _ = Group.objects.get_or_create(name='Delivery')
        delivery_user = User.objects.create_user(username='tc_delivery2', password='testpass')
        delivery_user.groups.add(delivery_group)
        delivery_user.save()

        restaurant = Restaurant.objects.create(name='Test Restaurant', address='1 Main', phone='123', is_active=True)
        customer = Customer.objects.get(user=self.sender)
        order = Order.objects.create(
            customer=customer,
            restaurant=restaurant,
            delivery_address='Test address',
            phone='+23212345678',
            status='received',
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.00'),
        )

        self.client.login(username='tc_admin', password='testpass')
        response = self.client.post(f'/order/{order.id}/assign/', {
            'delivery_person': delivery_user.id,
            'set_on_the_way': 'on',
        })

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.delivery_person, delivery_user)
        self.assertEqual(order.status, 'on_the_way')
        self.assertTrue(Notification.objects.filter(user=delivery_user).exists())

        self.client.logout()
        self.client.login(username='tc_delivery2', password='testpass')
        dashboard_response = self.client.get('/dashboard/delivery/')
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(dashboard_response.context['assigned_on_the_way_count'], 1)
        self.assertEqual(dashboard_response.context['assigned_pending_count'], 0)
        self.assertEqual(dashboard_response.context['assigned_completed_count'], 0)

    def test_send_chat_and_address_crud(self):
        # login
        login = self.client.login(username='tc_sender', password='testpass')
        self.assertTrue(login)

        # send chat
        resp = self.client.post('/chat/send/', {'receiver_id': self.receiver.id, 'message': 'hi test'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))

        # check ChatMessage created
        msgs = ChatMessage.objects.filter(sender=self.sender, receiver=self.receiver)
        self.assertTrue(msgs.exists())

        # add address
        add = self.client.post('/dashboard/customer/addresses/add/', {'label': 'Home', 'address': '100 Test Rd', 'is_default': 'on'})
        self.assertIn(add.status_code, (302, 200))
        self.assertTrue(Address.objects.filter(customer__user=self.sender).exists())

        # edit address
        a = Address.objects.filter(customer__user=self.sender).first()
        edit = self.client.post(f'/dashboard/customer/addresses/{a.id}/edit/', {'label': 'Home Edit', 'address': '101 Edit Rd', 'is_default': 'on'})
        self.assertIn(edit.status_code, (302, 200))
        a.refresh_from_db()
        self.assertEqual(a.address, '101 Edit Rd')

        # delete address
        delete = self.client.post(f'/dashboard/customer/addresses/{a.id}/delete/')
        self.assertIn(delete.status_code, (302, 200))
        self.assertFalse(Address.objects.filter(id=a.id).exists())
