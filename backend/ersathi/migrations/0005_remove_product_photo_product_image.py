# Generated by Django 5.1.4 on 2025-01-26 04:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ersathi', '0004_product_discount_percentage_product_per_day_rent_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='photo',
        ),
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='product_images/'),
        ),
    ]
