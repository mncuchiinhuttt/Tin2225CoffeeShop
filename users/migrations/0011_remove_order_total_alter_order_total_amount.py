# Generated by Django 5.1.6 on 2025-02-28 02:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_voucher_order_discount_order_subtotal_order_total_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='total',
        ),
        migrations.AlterField(
            model_name='order',
            name='total_amount',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=10),
        ),
    ]
