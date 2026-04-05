from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0017_karsilasmaodasi_hazir_sistemi'),
    ]

    operations = [
        migrations.AddField(
            model_name='soru',
            name='detayli_aciklama',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Doğru cevabın detaylı açıklaması (konu anlatımı gibi)',
                verbose_name='Detaylı Açıklama',
            ),
        ),
        migrations.AlterField(
            model_name='kullanicicevap',
            name='verilen_cevap',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='quiz.cevap',
            ),
        ),
    ]
