# Generated by Django 2.2.16 on 2022-10-25 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0015_auto_20221011_1112'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(
                blank=True,
                upload_to='posts/',
                verbose_name='Картинка'
            ),
        ),
    ]
