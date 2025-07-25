# Generated by Django 5.1.7 on 2025-07-22 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('toeic', '0003_question_is_approved_question_rejection_reason_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listeningmaterial',
            name='accent',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='listeningmaterial',
            name='audio_url',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='listeningmaterial',
            name='source',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
