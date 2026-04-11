from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profile', '0015_remove_ogrenciprofili_profil_puan_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Duyuru',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('baslik', models.CharField(max_length=120, verbose_name='Başlık')),
                ('mesaj', models.TextField(verbose_name='Mesaj')),
                ('icon', models.CharField(default='📢', max_length=10, verbose_name='İkon (emoji)')),
                ('renk', models.CharField(
                    choices=[
                        ('mavi', 'Mavi (Bilgi)'),
                        ('yesil', 'Yeşil (Başarı/Yeni)'),
                        ('sari', 'Sarı (Uyarı)'),
                        ('kirmizi', 'Kırmızı (Önemli)'),
                        ('mor', 'Mor (Özel)'),
                    ],
                    default='mavi',
                    max_length=10,
                    verbose_name='Renk',
                )),
                ('aktif', models.BooleanField(default=True, verbose_name='Aktif mi?')),
                ('olusturma_tarihi', models.DateTimeField(auto_now_add=True, verbose_name='Oluşturma Tarihi')),
                ('bitis_tarihi', models.DateTimeField(blank=True, null=True, verbose_name='Bitiş Tarihi (boş = süresiz)')),
                ('olusturan', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Oluşturan',
                )),
            ],
            options={
                'verbose_name': 'Duyuru',
                'verbose_name_plural': 'Duyurular',
                'ordering': ['-olusturma_tarihi'],
            },
        ),
    ]
