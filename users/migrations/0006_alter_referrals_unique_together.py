# Generated by Django 4.2.11 on 2024-04-12 17:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_remove_user_referrals_referrals'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='referrals',
            unique_together={('user', 'author')},
        ),
    ]