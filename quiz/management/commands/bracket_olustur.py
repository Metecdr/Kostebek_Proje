from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quiz.models import Turnuva, TurnuvaMaci, TurnuvaKatilim
import random
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Turnuva için otomatik bracket oluşturur'

    def add_arguments(self, parser):
        parser.add_argument('turnuva_id', type=str, help='Turnuva UUID')

    def handle(self, *args, **options):
        turnuva_id = options['turnuva_id']
        
        try:
            turnuva = Turnuva.objects.get(turnuva_id=turnuva_id)
        except Turnuva.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Turnuva bulunamadı: {turnuva_id}'))
            return
        
        if turnuva.durum != 'kayit_acik':
            self.stdout.write(self.style.ERROR('❌ Sadece kayıt açık turnuvalarda bracket oluşturulabilir!'))
            return
        
        katilimci_sayisi = turnuva.katilimci_sayisi
        
        if katilimci_sayisi < 2:
            self.stdout.write(self.style.ERROR('❌ En az 2 katılımcı gerekli!'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'🏆 Turnuva: {turnuva.isim}'))
        self.stdout.write(self.style.SUCCESS(f'👥 Katılımcı: {katilimci_sayisi}'))
        
        # Katılımcıları al ve karıştır
        katilimcilar = list(turnuva.katilimcilar.all())
        random.shuffle(katilimcilar)
        
        # Round sayısını hesapla
        import math
        round_sayisi = math.ceil(math.log2(katilimci_sayisi))
        self.stdout.write(self.style.SUCCESS(f'📊 Round Sayısı: {round_sayisi}'))
        
        # İlk round'u oluştur
        self.olustur_ilk_round(turnuva, katilimcilar, round_sayisi)
        
        # Turnuva durumunu güncelle
        turnuva.durum = 'basladi'
        turnuva.save()
        
        self.stdout.write(self.style.SUCCESS('✅ Bracket başarıyla oluşturuldu!'))
    
    def olustur_ilk_round(self, turnuva, katilimcilar, toplam_round):
        """İlk round'u oluştur"""
        
        # 2'nin kuvveti değilse, BYE ekle
        import math
        hedef_sayi = 2 ** toplam_round
        bye_sayisi = hedef_sayi - len(katilimcilar)
        
        self.stdout.write(self.style.WARNING(f'🔄 BYE Sayısı: {bye_sayisi}'))
        
        # Maçları oluştur
        mac_sayisi = 0
        oyuncu_index = 0
        
        # Önce BYE'lı maçları oluştur
        for i in range(bye_sayisi):
            if oyuncu_index < len(katilimcilar):
                mac = TurnuvaMaci.objects.create(
                    turnuva=turnuva,
                    round=1,
                    oyuncu1=katilimcilar[oyuncu_index],
                    oyuncu2=None,  # BYE
                    kazanan=katilimcilar[oyuncu_index],
                    tamamlandi=True
                )
                self.stdout.write(f'  ✅ Maç {mac_sayisi + 1}: {katilimcilar[oyuncu_index].username} (BYE)')
                oyuncu_index += 1
                mac_sayisi += 1
        
        # Normal maçları oluştur
        while oyuncu_index < len(katilimcilar) - 1:
            oyuncu1 = katilimcilar[oyuncu_index]
            oyuncu2 = katilimcilar[oyuncu_index + 1]
            
            mac = TurnuvaMaci.objects.create(
                turnuva=turnuva,
                round=1,
                oyuncu1=oyuncu1,
                oyuncu2=oyuncu2,
                tamamlandi=False
            )
            
            self.stdout.write(f'  ⚔️ Maç {mac_sayisi + 1}: {oyuncu1.username} vs {oyuncu2.username}')
            oyuncu_index += 2
            mac_sayisi += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ {mac_sayisi} maç oluşturuldu!'))