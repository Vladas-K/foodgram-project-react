# Generated by Django 3.2.3 on 2023-07-07 21:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0010_alter_recipe_cooking_time'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='ingredient',
            name='unique_name_measurement_unit',
        ),
    ]