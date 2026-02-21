from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from quiz.models import Turnuva, TurnuvaMaci, KarsilasmaOdasi
from quiz.helpers import get_random_soru_by_ders
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Turnuva maçları için karşılaşma odaları oluşturur ve başlangıç zamanlarını ayarlar'

    def add_arguments(self, parser):
        parser.add_argument('turnuva_id', type=str, help='Turnuva UUID')
        parser.add_argument('--round', type=int, default=1, help='Round numarası (varsayılan: 1)')
        parser.add_argument('--baslangic', type=str, help='Başlangıç zamanı (YYYY-MM-DD HH:MM formatında)')

    def handle(self, *args, **options):
        turnuva_id = options['turnuva_id']
        round_no = options['round']
        baslangic_str = options.get('baslangic')
        
        try:
            turnuva = Turnuva.objects.get(turnuva_id=turnuva_id)
        except Turnuva.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Turnuva bulunamadı: {turnuva_id}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'🏆 Turnuva: {turnuva.isim}'))
        
        # Başlangıç zamanını belirle
        if baslangic_str:
            from datetime import datetime
            try:
                mac_baslangic = timezone.make_aware(
                    datetime.strptime(baslangic_str, '%Y-%m-%d %H:%M')
                )
            except ValueError:
                self.stdout.write(self.style.ERROR('❌ Geçersiz tarih formatı! YYYY-MM-DD HH:MM kullanın'))
                return
        else:
            # Varsayılan: Şu andan 10 dakika sonra
            mac_baslangic = timezone.now() + timedelta(minutes=10)
        
        self.stdout.write(f'⏰ Maç Başlangıç Zamanı: {mac_baslangic.strftime("%Y-%m-%d %H:%M")}')
        
        # Belirtilen round'un maçlarını al
        maclar = TurnuvaMaci.objects.filter(
            turnuva=turnuva,
            round=round_no,
            tamamlandi=False
        )
        
        self.stdout.write(f'🎮 Round {round_no} - {maclar.count()} maç')
        
        hazir_mac_sayisi = 0
        
        for mac in maclar:
            # BYE kontrolü
            if not mac.oyuncu2:
                self.stdout.write(f'  ⏭️ {mac.oyuncu1.username} (BYE) - Zaten geçti')
                continue
            
            # Zaten oda varsa güncelle
            if mac.karsilasma_oda:
                mac.mac_baslangic_zamani = mac_baslangic
                mac.save()
                self.stdout.write(f'  🔄 {mac.oyuncu1.username} vs {mac.oyuncu2.username} → Güncellendi')
                hazir_mac_sayisi += 1
                continue
            
            # İlk soruyu al
            ilk_soru = get_random_soru_by_ders(turnuva.ders)
            
            if not ilk_soru:
                self.stdout.write(self.style.WARNING(f'  ⚠️ {turnuva.ders} için soru bulunamadı!'))
                continue
            
            # Karşılaşma odası oluştur
            oda = KarsilasmaOdasi.objects.create(
                oyuncu1=mac.oyuncu1,
                oyuncu2=mac.oyuncu2,
                secilen_ders=turnuva.ders,
                sinav_tipi=turnuva.sinav_tipi.lower(),
                oyun_durumu='bekleniyor',  # ✅ İki oyuncu da 'Hazırım' deyince 'oynaniyor' olacak
                aktif_soru=ilk_soru,
                aktif_soru_no=1,
                toplam_soru=turnuva.toplam_soru,
            )
            
            # Odayı maca bağla ve başlangıç zamanını ayarla
            mac.karsilasma_oda = oda
            mac.mac_baslangic_zamani = mac_baslangic
            mac.mac_tarihi = timezone.now()
            mac.oyuncu1_hazir = False
            mac.oyuncu2_hazir = False
            mac.save()
            
            self.stdout.write(f'  ✅ {mac.oyuncu1.username} vs {mac.oyuncu2.username} → Oda: {oda.oda_id}')
            hazir_mac_sayisi += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ {hazir_mac_sayisi} maç hazırlandı!'))
        self.stdout.write(self.style.SUCCESS(f'⏰ Maçlar {mac_baslangic.strftime("%H:%M")} saatinde başlayacak'))
        self.stdout.write(self.style.SUCCESS(f'📅 Oyuncular {(mac_baslangic - timedelta(minutes=5)).strftime("%H:%M")} itibariyle hazırlanabilir'))