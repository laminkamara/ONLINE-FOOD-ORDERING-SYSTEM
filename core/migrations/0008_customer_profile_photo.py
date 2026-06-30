from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_payment_receipt_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='profile_photo',
            field=models.ImageField(blank=True, null=True, upload_to='profile_photos/'),
        ),
    ]
