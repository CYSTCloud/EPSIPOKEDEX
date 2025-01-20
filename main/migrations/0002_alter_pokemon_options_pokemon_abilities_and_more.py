# Generated by Django 5.1.4 on 2025-01-20 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pokemon',
            options={'ordering': ['pokemon_id']},
        ),
        migrations.AddField(
            model_name='pokemon',
            name='abilities',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='pokemon',
            name='base_experience',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='pokemon',
            name='species_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='pokemon',
            name='sprite_shiny_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]