from django.core.management.base import BaseCommand
from profile.models import OgrenciProfili
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Liderlik puanlarını otomatik resetler'

    def handle(self, *args, **options):
        bugun = timezone.now().date()
        guncellenecek_profiller = []
        
        for profil in OgrenciProfili.objects.all():
            degisti = False
            
            # Günlük reset
            if profil.son_gunluk_reset < bugun:
                profil.gunluk_puan = 0
                profil.gunluk_cozulen = 0
                profil.gunluk_dogru = 0
                profil.gunluk_yanlis = 0
                profil.son_gunluk_reset = bugun
                degisti = True
            
            # Haftalık reset
            haftanin_basi = bugun - timedelta(days=bugun.weekday())
            if profil.son_haftalik_reset < haftanin_basi:
                profil.haftalik_puan = 0
                profil.haftalik_cozulen = 0
                profil.haftalik_dogru = 0
                profil.haftalik_yanlis = 0
                profil.son_haftalik_reset = haftanin_basi
                profil.hafta_baslangic = timezone.now()
                degisti = True
            
            # Aylık reset
            ayin_basi = bugun.replace(day=1)
            if profil.son_aylik_reset < ayin_basi:
                profil.aylik_puan = 0
                profil.aylik_cozulen = 0
                profil.aylik_dogru = 0
                profil.aylik_yanlis = 0
                profil.son_aylik_reset = ayin_basi
                degisti = True
            
            if degisti:
                guncellenecek_profiller.append(profil)
        
        if guncellenecek_profiller: 
            OgrenciProfili.objects.bulk_update(
                guncellenecek_profiller,
                ['gunluk_puan', 'gunluk_cozulen', 'gunluk_dogru', 'gunluk_yanlis', 'son_gunluk_reset',
                 'haftalik_puan', 'haftalik_cozulen', 'haftalik_dogru', 'haftalik_yanlis', 'son_haftalik_reset', 'hafta_baslangic',
                 'aylik_puan', 'aylik_cozulen', 'aylik_dogru', 'aylik_yanlis', 'son_aylik_reset']
            )
            self.stdout.write(self.style.SUCCESS(f'✅ {len(guncellenecek_profiller)} profil güncellendi! '))
            logger.info(f'Liderlik reset:  {len(guncellenecek_profiller)} profil')
        else:
            self.stdout.write(self.style.WARNING('⚠️ Reset edilecek profil yok.'))
        
        # Cache temizle
        from django.core.cache import cache
        cache.clear()