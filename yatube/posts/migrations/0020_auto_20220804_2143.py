# Generated by Django 2.2.16 on 2022-08-04 18:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0019_auto_20220803_2220'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='user_to_author_follow',
        ),
        migrations.AlterField(
            model_name='follow',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='following', to=settings.AUTH_USER_MODEL, verbose_name='Автор'),
        ),
        migrations.AlterField(
            model_name='follow',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='follower', to=settings.AUTH_USER_MODEL, verbose_name='Подписчик'),
        ),
    ]
