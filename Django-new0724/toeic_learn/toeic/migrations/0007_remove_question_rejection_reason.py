# Generated by Django 5.1.7 on 2025-07-26 21:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('toeic', '0006_remove_question_is_approved'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='rejection_reason',
        ),
    ]
