from django.test import TestCase, Client
from django.contrib.auth.models import User
from core.models import Customer, Address, ChatMessage


class ChatAndAddressTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username='tc_sender', password='testpass')
        self.receiver = User.objects.create_user(username='tc_receiver', password='testpass')
        Customer.objects.get_or_create(user=self.sender)
        Customer.objects.get_or_create(user=self.receiver)
        self.client = Client()

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
