from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class CurrencyMigrationTest(TransactionTestCase):
    def setUp(self):
        self.executor = MigrationExecutor(connection)

    def test_currency_unit_conversion_forward_and_reverse(self):
        # Migrate to state before our data migration
        self.executor.migrate([('core', '0011_order_delivery_proof')])
        apps_before = self.executor.loader.project_state(('core', '0011_order_delivery_proof')).apps

        User = apps_before.get_model('auth', 'User')
        Restaurant = apps_before.get_model('core', 'Restaurant')
        Branch = apps_before.get_model('core', 'Branch')
        Table = apps_before.get_model('core', 'Table')
        MenuItem = apps_before.get_model('core', 'MenuItem')
        Customer = apps_before.get_model('core', 'Customer')
        Order = apps_before.get_model('core', 'Order')
        OrderItem = apps_before.get_model('core', 'OrderItem')
        Payment = apps_before.get_model('core', 'Payment')

        # Create minimal related objects
        user = User.objects.create(username='migrate_test_user')
        customer = Customer.objects.create(user_id=user.id)
        restaurant = Restaurant.objects.create(name='Migrate R', description='', address='', phone='000')
        branch = Branch.objects.create(name='Migrate B', address='', phone='000', opening_hours='24/7')

        # Create records with large currency values (pre-conversion)
        menu = MenuItem.objects.create(restaurant_id=restaurant.id, name='M', description='', price=Decimal('85000.00'))
        table = Table.objects.create(branch_id=branch.id, table_number='T1', capacity=4, status='occupied', current_bill=Decimal('45000.00'))
        order = Order.objects.create(
            customer_id=customer.id,
            restaurant_id=restaurant.id,
            branch_id=branch.id,
            delivery_address='Addr',
            phone='000',
            order_number='YONI-9999',
            subtotal=Decimal('200000.00'),
            delivery_fee=Decimal('15000.00'),
            gst=Decimal('0.00'),
            total_amount=Decimal('215000.00'),
        )
        OrderItem.objects.create(order_id=order.id, menu_item_id=menu.id, quantity=1, price=menu.price)
        Payment.objects.create(order_id=order.id, amount=Decimal('215000.00'), payment_method='cash', status='completed')

        # Import the migration module and run its forwards() directly
        from importlib import import_module

        mig = import_module('core.migrations.0012_currency_unit_conversion')

        # Run forwards (divide by 1000)
        mig.forwards(apps_before, None)

        MenuItemA = apps_before.get_model('core', 'MenuItem')
        TableA = apps_before.get_model('core', 'Table')
        OrderA = apps_before.get_model('core', 'Order')
        OrderItemA = apps_before.get_model('core', 'OrderItem')
        PaymentA = apps_before.get_model('core', 'Payment')

        menu_after = MenuItemA.objects.get(pk=menu.id)
        table_after = TableA.objects.get(pk=table.id)
        order_after = OrderA.objects.get(pk=order.id)
        orderitem_after = OrderItemA.objects.get(order_id=order.id)
        payment_after = PaymentA.objects.get(order_id=order.id)

        # Assert values divided by 1000
        self.assertEqual(menu_after.price, Decimal('85.00'))
        self.assertEqual(table_after.current_bill, Decimal('45.00'))
        self.assertEqual(order_after.total_amount, Decimal('215.00'))
        self.assertEqual(orderitem_after.price, Decimal('85.00'))
        self.assertEqual(payment_after.amount, Decimal('215.00'))

        # Run reverse (multiply by 1000)
        mig.reverse(apps_before, None)

        menu_rev = MenuItemA.objects.get(pk=menu.id)
        table_rev = TableA.objects.get(pk=table.id)
        order_rev = OrderA.objects.get(pk=order.id)
        orderitem_rev = OrderItemA.objects.get(order_id=order.id)
        payment_rev = PaymentA.objects.get(order_id=order.id)

        # Assert values multiplied back by 1000
        self.assertEqual(menu_rev.price, Decimal('85000.00'))
        self.assertEqual(table_rev.current_bill, Decimal('45000.00'))
        self.assertEqual(order_rev.total_amount, Decimal('215000.00'))
        self.assertEqual(orderitem_rev.price, Decimal('85000.00'))
        self.assertEqual(payment_rev.amount, Decimal('215000.00'))
