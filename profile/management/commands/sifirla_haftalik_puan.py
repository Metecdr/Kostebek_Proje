from django.core.management.base import BaseCommand
from profile.models import OgrenciProfili
from django.db.models import F

class Command(BaseCommand):
    help = 'Tüm kullanıcıların haftalık puanlarını sıfırlar.'

    def handle(self, *args, **options):
        # Toplam puanı sıfırlayacak sorguyu oluştur
        guncellenen_sayi = OgrenciProfili.objects.all().update(haftalik_puan=0)
        
        self.stdout.write(
            self.style.SUCCESS(f'{guncellenen_sayi} öğrencinin haftalık puanı başarıyla sıfırlandı.')
        )