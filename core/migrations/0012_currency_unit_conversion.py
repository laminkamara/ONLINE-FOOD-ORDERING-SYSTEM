from django.db import migrations
from decimal import Decimal, ROUND_HALF_UP, getcontext


def forwards(apps, schema_editor):
    getcontext().prec = 28
    factor = Decimal('1000')
    quant = Decimal('0.01')

    ModelFieldMap = {
        'MenuItem': ['price'],
        'Table': ['current_bill'],
        'Order': ['subtotal', 'delivery_fee', 'gst', 'total_amount'],
        'OrderItem': ['price'],
        'Payment': ['amount'],
    }

    for model_name, fields in ModelFieldMap.items():
        Model = apps.get_model('core', model_name)
        for obj in Model.objects.all():
            changed = False
            for field in fields:
                val = getattr(obj, field, None)
                if val is None:
                    continue
                try:
                    new = (Decimal(val) / factor).quantize(quant, rounding=ROUND_HALF_UP)
                except Exception:
                    # skip values that cannot be converted
                    continue
                if new != val:
                    setattr(obj, field, new)
                    changed = True
            if changed:
                obj.save()


def reverse(apps, schema_editor):
    getcontext().prec = 28
    factor = Decimal('1000')
    quant = Decimal('0.01')

    ModelFieldMap = {
        'MenuItem': ['price'],
        'Table': ['current_bill'],
        'Order': ['subtotal', 'delivery_fee', 'gst', 'total_amount'],
        'OrderItem': ['price'],
        'Payment': ['amount'],
    }

    for model_name, fields in ModelFieldMap.items():
        Model = apps.get_model('core', model_name)
        for obj in Model.objects.all():
            changed = False
            for field in fields:
                val = getattr(obj, field, None)
                if val is None:
                    continue
                try:
                    new = (Decimal(val) * factor).quantize(quant, rounding=ROUND_HALF_UP)
                except Exception:
                    continue
                if new != val:
                    setattr(obj, field, new)
                    changed = True
            if changed:
                obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_order_delivery_proof'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse),
    ]
