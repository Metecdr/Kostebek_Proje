from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from profile.models import OgrenciProfili, Rozet
from quiz.models import Soru, KarsilasmaOdasi
import time

class Command(BaseCommand):
    help = 'Performans testleri yapar'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Performans testleri başlıyor...\n')
        
        # Test 1: Liderlik sorgusu
        start = time.time()
        liderler = list(OgrenciProfili.objects.select_related('kullanici').order_by('-toplam_puan')[:50])
        end = time.time()
        self.stdout.write(f'✅ Liderlik sorgusu: {(end-start)*1000:.2f}ms ({len(liderler)} kayıt)')
        
        # Test 2: Random soru
        start = time.time()
        soru = Soru.objects.filter(bul_bakalimda_cikar=True).order_by('?').first()
        end = time.time()
        self.stdout.write(f'✅ Random soru: {(end-start)*1000:.2f}ms')
        
        # Test 3: Kullanıcı rozetleri
        start = time.time()
        if User.objects.exists():
            user = User.objects.first()
            rozetler = list(Rozet.objects.filter(profil__kullanici=user).select_related('profil'))
        end = time.time()
        self.stdout.write(f'✅ Kullanıcı rozetleri: {(end-start)*1000:.2f}ms')
        
        # Test 4: Aktif oda arama
        start = time.time()
        bekleyen_oda = KarsilasmaOdasi.objects.filter(
            oyun_durumu='bekleniyor',
            oyuncu2=None
        ).select_related('oyuncu1').first()
        end = time.time()
        self.stdout.write(f'✅ Aktif oda arama: {(end-start)*1000:.2f}ms')
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Tüm testler tamamlandı!'))