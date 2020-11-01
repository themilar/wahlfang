# Generated by Django 3.1.2 on 2020-10-25 20:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('vote', '0017_election_send_emails_on_start'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='remind_text',
            field=models.TextField(blank=True, max_length=1000),
        ),
        migrations.AddField(
            model_name='session',
            name='invite_text',
            field=models.TextField(blank=True, max_length=1000),
        ),
    ]
