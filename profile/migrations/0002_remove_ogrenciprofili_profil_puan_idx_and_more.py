import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profile', '0001_initial'),
    ]

    operations = [
        # ESKİ INDEX'LERİ SİL (varsa)
        migrations.RunSQL(
            "DROP INDEX IF EXISTS profil_puan_idx;",
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS profil_alan_puan_idx;",
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS profil_toplam_idx;",
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS profil_haftalik_idx;",
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS profil_aylik_idx;",
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS profil_gunluk_idx;",
            migrations.RunSQL.noop,
        ),
        
        # YENİ FIELD'LARI EKLE
        migrations.AddField(
            model_name='ogrenciprofili',
            name='aktif_mi',
            field=models.BooleanField(default=True, verbose_name='Aktif Mi'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='gunluk_puan',
            field=models.IntegerField(db_index=True, default=0, verbose_name='Günlük Puan'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='haftalik_puan',
            field=models.IntegerField(db_index=True, default=0, verbose_name='Haftalık Puan'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='aylik_puan',
            field=models.IntegerField(db_index=True, default=0, verbose_name='Aylık Puan'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='gunluk_cozulen',
            field=models.IntegerField(default=0, verbose_name='Günlük Çözülen'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='gunluk_dogru',
            field=models.IntegerField(default=0, verbose_name='Günlük Doğru'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='gunluk_yanlis',
            field=models.IntegerField(default=0, verbose_name='Günlük Yanlış'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='haftalik_cozulen',
            field=models.IntegerField(default=0, verbose_name='Haftalık Çözülen'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='haftalik_dogru',
            field=models.IntegerField(default=0, verbose_name='Haftalık Doğru'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='haftalik_yanlis',
            field=models.IntegerField(default=0, verbose_name='Haftalık Yanlış'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='aylik_cozulen',
            field=models.IntegerField(default=0, verbose_name='Aylık Çözülen'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='aylik_dogru',
            field=models.IntegerField(default=0, verbose_name='Aylık Doğru'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='aylik_yanlis',
            field=models.IntegerField(default=0, verbose_name='Aylık Yanlış'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='son_gunluk_reset',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Son Günlük Reset'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='son_haftalik_reset',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Son Haftalık Reset'),
        ),
        migrations.AddField(
            model_name='ogrenciprofili',
            name='son_aylik_reset',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Son Aylık Reset'),
        ),
        
        # YENİ INDEX'LERİ EKLE (IF NOT EXISTS mantığıyla)
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS profil_toplam_idx ON profile_ogrenciprofili (toplam_puan DESC);",
            "DROP INDEX IF EXISTS profil_toplam_idx;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS profil_haftalik_idx ON profile_ogrenciprofili (haftalik_puan DESC);",
            "DROP INDEX IF EXISTS profil_haftalik_idx;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS profil_aylik_idx ON profile_ogrenciprofili (aylik_puan DESC);",
            "DROP INDEX IF EXISTS profil_aylik_idx;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS profil_gunluk_idx ON profile_ogrenciprofili (gunluk_puan DESC);",
            "DROP INDEX IF EXISTS profil_gunluk_idx;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS profil_alan_puan_idx ON profile_ogrenciprofili (alan, toplam_puan DESC);",
            "DROP INDEX IF EXISTS profil_alan_puan_idx;",
        ),
    ]