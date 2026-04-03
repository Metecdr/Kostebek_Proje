from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profile', '0013_bildirim_link_bildirim_silindi_mi_alter_bildirim_tip'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ogrenciprofili',
            name='profil_fotografi',
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='avatar',
            field=models.CharField(default='🦔', max_length=10, verbose_name='Avatar'),
        ),
    ]
