from django.db import models
from django.contrib.auth.models import User

# Kullanıcının alan tercihleri (DB kodu [küçük harf] ve Görünen isim [Büyük harf] eşleşmesi)
ALAN_TERCIHLERI = (
    ('sayisal', 'Sayısal'),
    ('esit_agirlik', 'Eşit Ağırlık'),
    ('sozel', 'Sözel'),
    ('dil', 'Dil'),
)

class OgrenciProfili(models.Model):
    # Kullanıcı ile birebir ilişki (related_name='profil' ile erişim sağlıyoruz)
    kullanici = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')

    # YKS KİŞİSEL BİLGİLER
    ad = models.CharField(max_length=50, blank=True, null=True)
    soyad = models.CharField(max_length=50, blank=True, null=True)
    hedef_puan = models.IntegerField(default=0)
    
    # PUANLAMA VE SIRALAMA
    toplam_puan = models.IntegerField(default=0)
    haftalik_puan = models.IntegerField(default=0)
    
    # İSTATİSTİKLER
    cozulen_soru_sayisi = models.IntegerField(default=0)
    dogru_sayisi = models.IntegerField(default=0)
    yanlis_sayisi = models.IntegerField(default=0)

    # Alan tercihi (Dropdown menü ve filtreleme için)
    # Choices, DB'ye 'sayisal' kodunu, HTML'e 'Sayısal' ismini gösterir.
    alan = models.CharField(max_length=20, choices=ALAN_TERCIHLERI, default='esit_agirlik')
    
    # Kazanılan rozetler
    unvanlar = models.TextField(default="Yeni Köstebek")

    def __str__(self):
        return self.kullanici.username

    def basari_orani(self):
        """Genel başarı yüzdesini hesaplar."""
        if self.cozulen_soru_sayisi > 0:
            return (self.dogru_sayisi / self.cozulen_soru_sayisi) * 100
        return 0.0