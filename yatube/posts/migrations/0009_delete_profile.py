# Generated by Django 2.2.9 on 2022-07-10 19:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_profile'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Profile',
        ),
    ]