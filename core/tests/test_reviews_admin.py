from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from core.models import MenuItem, Restaurant, Category, Customer, Order, OrderItem

class ReviewsAdminTests(TestCase):
    def setUp(self):
        # create admin user
        self.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')
        self.client = Client()
        self.client.login(username='admin', password='pass')

        # create restaurant, category, menu_item
        self.cat = Category.objects.create(name='Test Cat', icon='fas fa-utensils')
        self.rest = Restaurant.objects.create(name='R', description='d', address='a', phone='p')
        self.menu = MenuItem.objects.create(restaurant=self.rest, name='Item', description='d', price=Decimal('10.00'), category=self.cat)

        # create customer and order with rating
        user = User.objects.create_user(username='cust', password='pass')
        cust = Customer.objects.create(user=user)
        order = Order.objects.create(customer=cust, restaurant=self.rest, delivery_address='addr', phone='000', order_number='T-1', subtotal=Decimal('10.00'), delivery_fee=Decimal('0'), gst=Decimal('0'), total_amount=Decimal('10.00'), customer_rating=Decimal('4.0'), customer_feedback='Good')
        OrderItem.objects.create(order=order, menu_item=self.menu, quantity=1, price=self.menu.price)

    def test_reviews_list(self):
        resp = self.client.get('/dashboard/reviews/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Customer Reviews')
        self.assertContains(resp, 'Good')

    def test_edit_review(self):
        oi = OrderItem.objects.first()
        resp = self.client.post(f'/dashboard/reviews/{oi.id}/edit/', {'rating':'5.0','feedback':'Excellent'})
        self.assertEqual(resp.status_code, 302)
        order = oi.order
        order.refresh_from_db()
        self.assertEqual(order.customer_rating, Decimal('5.0'))
        self.assertEqual(order.customer_feedback, 'Excellent')

    def test_delete_review(self):
        oi = OrderItem.objects.first()
        resp = self.client.post(f'/dashboard/reviews/{oi.id}/delete/')
        self.assertEqual(resp.status_code, 302)
        order = oi.order
        order.refresh_from_db()
        self.assertEqual(order.customer_rating, Decimal('0'))
        self.assertEqual(order.customer_feedback, '')
