from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profile', '0002_remove_ogrenciprofili_profil_puan_idx_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            "DROP INDEX IF EXISTS profil_puan_idx;",
            migrations.RunSQL.noop,
        ),
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
    ]