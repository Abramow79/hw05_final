# Generated by Django 2.2.6 on 2022-10-08 19:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20221009_0035'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'ordering': ('title',), 'verbose_name': 'Сообщество', 'verbose_name_plural': 'Сообщества'},
        ),
    ]
