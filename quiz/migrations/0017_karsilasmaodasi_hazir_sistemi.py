from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0016_karsilasmaodasi_oda_kodu_and_more'),
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
