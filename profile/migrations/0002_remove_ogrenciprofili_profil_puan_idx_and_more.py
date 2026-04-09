import django.utils.timezone
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profile', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL("DROP INDEX IF EXISTS profil_puan_idx;", migrations.RunSQL.noop),
        migrations.RunSQL("DROP INDEX IF EXISTS profil_alan_puan_idx;", migrations.RunSQL.noop),
        migrations.RunSQL("DROP INDEX IF EXISTS profil_toplam_idx;", migrations.RunSQL.noop),
        migrations.RunSQL("DROP INDEX IF EXISTS profil_haftalik_idx;", migrations.RunSQL.noop),
        migrations.RunSQL("DROP INDEX IF EXISTS profil_aylik_idx;", migrations.RunSQL.noop),
        migrations.RunSQL("DROP INDEX IF EXISTS profil_gunluk_idx;", migrations.RunSQL.noop),

        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS aktif_mi boolean NOT NULL DEFAULT true;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS aktif_mi;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS gunluk_puan integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS gunluk_puan;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS haftalik_puan integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS haftalik_puan;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS aylik_puan integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS aylik_puan;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS gunluk_cozulen integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS gunluk_cozulen;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS gunluk_dogru integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS gunluk_dogru;",
        ),


        # FIELD'LARI GÜVENLİ EKLE (IF NOT EXISTS)
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS aktif_mi boolean NOT NULL DEFAULT true;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS aktif_mi;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS gunluk_puan integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS gunluk_puan;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS haftalik_puan integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS haftalik_puan;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS aylik_puan integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS aylik_puan;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS gunluk_cozulen integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS gunluk_cozulen;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS gunluk_dogru integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS gunluk_dogru;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS gunluk_yanlis integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS gunluk_yanlis;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS haftalik_cozulen integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS haftalik_cozulen;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS haftalik_dogru integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS haftalik_dogru;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS haftalik_yanlis integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS haftalik_yanlis;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS aylik_cozulen integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS aylik_cozulen;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS aylik_dogru integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS aylik_dogru;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS aylik_yanlis integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS aylik_yanlis;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS son_gunluk_reset date NOT NULL DEFAULT CURRENT_DATE;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS son_gunluk_reset;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS son_haftalik_reset date NOT NULL DEFAULT CURRENT_DATE;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS son_haftalik_reset;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS son_aylik_reset date NOT NULL DEFAULT CURRENT_DATE;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS son_aylik_reset;",
        ),

        # YENİ INDEX'LER
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS gunluk_yanlis integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS gunluk_yanlis;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS haftalik_cozulen integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS haftalik_cozulen;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS haftalik_dogru integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS haftalik_dogru;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS haftalik_yanlis integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS haftalik_yanlis;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS aylik_cozulen integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS aylik_cozulen;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS aylik_dogru integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS aylik_dogru;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS aylik_yanlis integer NOT NULL DEFAULT 0;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS aylik_yanlis;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS son_gunluk_reset date NOT NULL DEFAULT CURRENT_DATE;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS son_gunluk_reset;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS son_haftalik_reset date NOT NULL DEFAULT CURRENT_DATE;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS son_haftalik_reset;",
        ),
        migrations.RunSQL(
            "ALTER TABLE profile_ogrenciprofili ADD COLUMN IF NOT EXISTS son_aylik_reset date NOT NULL DEFAULT CURRENT_DATE;",
            "ALTER TABLE profile_ogrenciprofili DROP COLUMN IF EXISTS son_aylik_reset;",
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
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS profil_alan_puan_idx ON profile_ogrenciprofili (alan, toplam_puan DESC);",
            "DROP INDEX IF EXISTS profil_alan_puan_idx;",
        ),
    ]
