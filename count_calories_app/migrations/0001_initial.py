# Generated by Django 5.1.7 on 2025-03-31 14:57

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FoodItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(help_text='Name of the food or drink', max_length=200)),
                ('calories', models.PositiveIntegerField(default=0, help_text='Calories per serving')),
                ('fat', models.DecimalField(decimal_places=2, default=0.0, help_text='Fat content in grams', max_digits=5)),
                ('carbohydrates', models.DecimalField(decimal_places=2, default=0.0, help_text='Carbohydrate content in grams', max_digits=5)),
                ('protein', models.DecimalField(decimal_places=2, default=0.0, help_text='Protein content in grams', max_digits=5)),
                ('consumed_at', models.DateTimeField(default=django.utils.timezone.now, help_text='Date and time the item was consumed')),
            ],
            options={
                'ordering': ['-consumed_at'],
            },
        ),
    ]
