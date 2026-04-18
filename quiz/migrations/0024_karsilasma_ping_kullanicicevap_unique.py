# Generated manually - 2026-04-19
# Adds:
#   KarsilasmaOdasi.oyuncu1_son_ping, oyuncu2_son_ping  (disconnect detection)
#   KullaniciCevap unique_together (kullanici, oda, soru)  (race condition guard)

from django.db import migrations, models


def deduplicate_kullanici_cevap(apps, schema_editor):
    """
    unique_together eklemeden önce (kullanici, oda, soru) duplicate'leri temizle.
    Her grup için en erken kaydı tutar, gerisini siler.
    """
    KullaniciCevap = apps.get_model('quiz', 'KullaniciCevap')
    from django.db.models import Min

    # Her (kullanici, oda, soru) grubundaki en eski kaydın id'sini bul
    keep_ids = (
        KullaniciCevap.objects
        .values('kullanici_id', 'oda_id', 'soru_id')
        .annotate(min_id=Min('id'))
        .values_list('min_id', flat=True)
    )
    # Bunların dışındakileri sil
    deleted_count, _ = KullaniciCevap.objects.exclude(id__in=list(keep_ids)).delete()
    if deleted_count:
        print(f"\n  ⚠️  {deleted_count} duplicate KullaniciCevap satırı temizlendi.")


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_gununsorusu_gununsorusucevap_meydanokuma_oyunmesaj_and_more'),
    ]

    operations = [
        # Ping fields for disconnect detection
        migrations.AddField(
            model_name='karsilasmaodasi',
            name='oyuncu1_son_ping',
            field=models.DateTimeField(
                blank=True, null=True,
                verbose_name='Oyuncu1 Son Ping'
            ),
        ),
        migrations.AddField(
            model_name='karsilasmaodasi',
            name='oyuncu2_son_ping',
            field=models.DateTimeField(
                blank=True, null=True,
                verbose_name='Oyuncu2 Son Ping'
            ),
        ),
        # Önce duplicate'leri temizle, sonra constraint ekle
        migrations.RunPython(
            deduplicate_kullanici_cevap,
            reverse_code=migrations.RunPython.noop,
        ),
        # DB-level duplicate guard
        migrations.AlterUniqueTogether(
            name='kullanicicevap',
            unique_together={('kullanici', 'oda', 'soru')},
        ),
    ]
