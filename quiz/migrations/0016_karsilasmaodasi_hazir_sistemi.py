from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0015_karsilasmaodasi_bitis_zamani'),
    ]

    operations = [
        migrations.AddField(
            model_name='karsilasmaodasi',
            name='oyuncu1_hazir',
            field=models.BooleanField(default=False, verbose_name='Oyuncu 1 Hazır'),
        ),
        migrations.AddField(
            model_name='karsilasmaodasi',
            name='oyuncu2_hazir',
            field=models.BooleanField(default=False, verbose_name='Oyuncu 2 Hazır'),
        ),
    ]
