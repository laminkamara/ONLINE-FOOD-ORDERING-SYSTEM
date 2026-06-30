from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_currency_unit_conversion'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='icon_image',
            field=models.ImageField(upload_to='category_icons/', null=True, blank=True),
        ),
    ]
