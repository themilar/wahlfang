# Generated by Django 3.0.5 on 2020-05-29 19:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voter',
            name='first_name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='voter',
            name='last_name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='voter',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='vote.Session'),
        ),
        migrations.AlterField(
            model_name='voter',
            name='voter_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterUniqueTogether(
            name='voter',
            unique_together={('session', 'email')},
        ),
    ]
