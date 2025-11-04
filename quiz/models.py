import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



# ==================== SINAV SECIMI ====================

SINAV_TIPI_SECENEKLERI = [
    ('tyt', 'TYT'),
    ('ayt', 'AYT'),
]

sinav_tipi = models.CharField(
    max_length=10,
    choices=SINAV_TIPI_SECENEKLERI,
    null=True,
    blank=True,
    verbose_name='Sınav Tipi'
)


# ==================== KONU MODELİ ====================

class Konu(models.Model):
    """Konu Modeli"""

    isim = models.CharField(max_length=100, verbose_name='Konu İsmi')
    DERS_SECENEKLERI = [
        ('matematik', 'Matematik'),
        ('fizik', 'Fizik'),
        ('kimya', 'Kimya'),
        ('turkce', 'Türkçe'),
        ('tarih', 'Tarih'),
        ('cografya', 'Coğrafya'),
        ('felsefe', 'Felsefe'),
        ('biyoloji','Biyoloji'),

    ]
    ders = models.CharField(max_length=20, choices=DERS_SECENEKLERI, verbose_name='Ders', default='matematik')
    sira = models.PositiveIntegerField(default=0, verbose_name='Sıra')  # Sıra alanı eklendi

    class Meta:
        ordering = ['sira']  # Varsayılan sıralama 'sira' alanına göre yapılacak

    def __str__(self):
        return self.isim


# ==================== SORU VE CEVAP MODELLERİ ====================

class Soru(models.Model):
    metin = models.TextField()
    baslik = models.CharField(max_length=100, default="", blank=True)
    bul_bakalimda_cikar = models.BooleanField(default=True)
    karsilasmada_cikar = models.BooleanField(default=True)

    # Tek bir ders alanı!
    DERS_SECENEKLERI = [
        ('matematik', 'Matematik'),
        ('fizik', 'Fizik'),
        ('kimya', 'Kimya'),
        ('turkce', 'Türkçe'),
        ('tarih', 'Tarih'),
        ('cografya', 'Coğrafya'),
        ('felsefe', 'Felsefe'),
        ('biyoloji','Biyoloji'),
    ]
    ders = models.CharField(max_length=20, choices=DERS_SECENEKLERI, verbose_name='Ders', default='matematik')

    sinav_tipi = models.CharField(max_length=10, default="", blank=True)
    
    konu = models.ForeignKey(
        'Konu', 
        on_delete=models.CASCADE, 
        verbose_name='Konu',
        default=1  # ID=1 varsa!
    )

    def __str__(self):
        return self.metin

    class Meta:
        verbose_name = "Soru"
        verbose_name_plural = "Sorular"


class Cevap(models.Model):
    """Sorulara ait cevaplar"""
    soru = models.ForeignKey(Soru, on_delete=models.CASCADE, related_name='cevaplar')
    metin = models.CharField(max_length=500, verbose_name="Cevap Metni")
    dogru_mu = models.BooleanField(default=False, verbose_name="Doğru mu?")

    def __str__(self):
        dogru_text = "✅" if self.dogru_mu else "❌"
        return f"{dogru_text} {self.metin[:30]}"

    class Meta:
        verbose_name = "Cevap"
        verbose_name_plural = "Cevaplar"


# ==================== TABU OYUNU MODELLERİ ====================

class TabuKelime(models.Model):
    kelime = models.CharField(max_length=100, unique=True, verbose_name="Tabu Kelime")
    kategori = models.CharField(
        max_length=30,
        choices=[
            ('biyoloji', 'Biyoloji'),
            ('kimya', 'Kimya'),
            ('fizik', 'Fizik'),
            ('cografya', 'Coğrafya'),
            ('tarih', 'Tarih'),
            ('edebiyat', 'Edebiyat'),
            # ileride dil için eklenebilir
        ],
        verbose_name="Kategori"
    )
    def __str__(self):
        return self.kelime

    class Meta:
        verbose_name = "Tabu Kelime"
        verbose_name_plural = "Tabu Kelimeler"

class YasakliKelime(models.Model):
    """Tabu kelimelerine ait yasaklı kelimeler"""
    tabu_kelime = models.ForeignKey(
        TabuKelime, 
        on_delete=models.CASCADE, 
        related_name='yasakli_kelimeler'
    )
    yasakli_kelime = models.CharField(max_length=100, verbose_name="Yasaklı Kelime")

    def __str__(self):
        return f"{self.tabu_kelime.kelime} → {self.yasakli_kelime}"

    class Meta:
        verbose_name = "Yasaklı Kelime"
        verbose_name_plural = "Yasaklı Kelimeler"


class TabuOyun(models.Model):
    """Tabu oyun seansları"""
    takim_a_adi = models.CharField(max_length=100, default='Takım A')
    takim_b_adi = models.CharField(max_length=100, default='Takım B')
    takim_a_skor = models.IntegerField(default=0)
    takim_b_skor = models.IntegerField(default=0)
    aktif_takim = models.CharField(
        max_length=1, 
        default='A',
        choices=[('A', 'Takım A'), ('B', 'Takım B')]
    )
    oyun_durumu = models.CharField(
        max_length=20, 
        default='devam_ediyor',
        choices=[
            ('devam_ediyor', 'Devam Ediyor'),
            ('bitti', 'Bitti'),
        ]
    )
    oyun_modu = models.CharField(
        max_length=20, 
        default='normal',
        choices=[
            ('normal', 'Normal'),
            ('uzatma', 'Uzatma'),
        ]
    )
    tur_sayisi = models.IntegerField(default=1)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    def get_kazanan(self):
        """Kazanan takımı döndürür"""
        if self.takim_a_skor > self.takim_b_skor:
            return self.takim_a_adi
        elif self.takim_b_skor > self.takim_a_skor:
            return self.takim_b_adi
        else:
            return "Berabere"

    def __str__(self):
        return f"{self.takim_a_adi} ({self.takim_a_skor}) vs {self.takim_b_adi} ({self.takim_b_skor})"

    class Meta:
        verbose_name = "Tabu Oyunu"
        verbose_name_plural = "Tabu Oyunları"
        ordering = ['-olusturma_tarihi']


# ==================== KARŞILAŞMA MODELİ ====================

class KarsilasmaOdasi(models.Model):
    """1v1 Karşılaşma odaları"""
    oda_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Oyuncular
    oyuncu1 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='karsilasma_oyuncu1'
    )
    oyuncu2 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='karsilasma_oyuncu2'
    )
    
    # Skorlar
    oyuncu1_skor = models.IntegerField(default=0, verbose_name="Oyuncu 1 Skoru")
    oyuncu2_skor = models.IntegerField(default=0, verbose_name="Oyuncu 2 Skoru")
    
    # ✅ OYUN İÇİ DOĞRU/YANLIŞ İSTATİSTİKLERİ
    oyuncu1_dogru = models.IntegerField(default=0, verbose_name="Oyuncu 1 Doğru Sayısı")
    oyuncu1_yanlis = models.IntegerField(default=0, verbose_name="Oyuncu 1 Yanlış Sayısı")
    oyuncu2_dogru = models.IntegerField(default=0, verbose_name="Oyuncu 2 Doğru Sayısı")
    oyuncu2_yanlis = models.IntegerField(default=0, verbose_name="Oyuncu 2 Yanlış Sayısı")
    
    # Oyun durumu
    oyun_durumu = models.CharField(
        max_length=20, 
        default='bekleniyor',
        choices=[
            ('bekleniyor', 'Bekleniyor'),
            ('oynaniyor', 'Oynanıyor'),
            ('bitti', 'Bitti'),
        ]
    )
    aktif_soru = models.ForeignKey(
        Soru, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Aktif Soru"
    )
    aktif_soru_no = models.IntegerField(default=1, verbose_name="Aktif Soru Numarası")
    toplam_soru = models.IntegerField(default=5, verbose_name="Toplam Soru Sayısı")
    
    # Cevap durumları
    oyuncu1_cevapladi = models.BooleanField(default=False)
    oyuncu2_cevapladi = models.BooleanField(default=False)
    ilk_dogru_cevaplayan = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='ilk_cevaplayan'
    )
    
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    def yeni_soru_getir(self):
        """Rastgele yeni soru getir"""
        return Soru.objects.order_by('?').first()

    def __str__(self):
        oyuncu2_adi = self.oyuncu2.username if self.oyuncu2 else 'Bekleniyor'
        return f"{self.oyuncu1.username} vs {oyuncu2_adi} - {self.oyun_durumu}"

    class Meta:
        verbose_name = "Karşılaşma Odası"
        verbose_name_plural = "Karşılaşma Odaları"
        ordering = ['-olusturma_tarihi']


# ==================== KULLANICI CEVAP MODELİ ====================

class KullaniciCevap(models.Model):
    """Kullanıcının verdiği cevapları kaydeder (yanlış analizi için)"""
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    oda = models.ForeignKey(KarsilasmaOdasi, on_delete=models.CASCADE)
    soru = models.ForeignKey(Soru, on_delete=models.CASCADE)
    verilen_cevap = models.ForeignKey(Cevap, on_delete=models.CASCADE)
    dogru_mu = models.BooleanField()
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        durum = "✅ Doğru" if self.dogru_mu else "❌ Yanlış"
        return f"{self.kullanici.username} - {self.soru.metin[:30]}... - {durum}"

    class Meta:
        verbose_name = "Kullanıcı Cevabı"
        verbose_name_plural = "Kullanıcı Cevapları"
        ordering = ['-tarih']

class BulBakalimOyun(models.Model):
    """Bul Bakalım oyun oturumu"""
    
    OYUN_DURUMU_SECENEKLERI = [
        ('devam_ediyor', 'Devam Ediyor'),
        ('bitti', 'Bitti'),
    ]

    DERS_SECENEKLERI = [
        ('matematik', 'Matematik'),
        ('fizik', 'Fizik'),
        ('kimya', 'Kimya'),
        ('turkce', 'Türkçe'),
        ('tarih', 'Tarih'),
        ('cografya', 'Coğrafya'),
        ('felsefe', 'Felsefe'),
        ('biyoloji','Biyoloji'),
    
    ]
    
    selected_ders = models.CharField(
        max_length=20,
        choices=DERS_SECENEKLERI,
        null=True,
        blank=True,
        verbose_name='Seçilen Ders'
    )

    sinav_tipi = models.CharField(
        max_length=10,
        choices=[('tyt', 'TYT'), ('ayt', 'AYT')],
        null=True,
        blank=True,
        verbose_name='Sınav Tipi'
    )
    
    oyun_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oyuncu = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bul_bakalim_oyunlari')
    oyun_durumu = models.CharField(max_length=20, choices=OYUN_DURUMU_SECENEKLERI, default='devam_ediyor')
    
    # Skorlar
    dogru_sayisi = models.IntegerField(default=0)
    yanlis_sayisi = models.IntegerField(default=0)
    toplam_puan = models.IntegerField(default=0)
    
    # Sorular ve cevaplar (JSON olarak sakla)
    sorular = models.JSONField(default=list)  # [soru_id1, soru_id2, ...]
    cevaplar = models.JSONField(default=dict)  # {soru_id: cevap_id, ...}
    
    # Tarihler
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    bitirme_tarihi = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'bul_bakalim_oyun'
        verbose_name = 'Bul Bakalım Oyunu'
        verbose_name_plural = 'Bul Bakalım Oyunları'
        ordering = ['-olusturulma_tarihi']
    
    def __str__(self):
        return f"{self.oyuncu.username} - {self.dogru_sayisi}/5 - {self.oyun_durumu}"
    
    def oyun_bitir(self):
        """Oyunu bitir ve puanları hesapla"""
        self.oyun_durumu = 'bitti'
        self.bitirme_tarihi = timezone.now()
        
        # 3 veya daha fazla doğru = 1 puan
        if self.dogru_sayisi >= 3:
            self.toplam_puan = 1
        else:
            self.toplam_puan = 0
        
        self.save()
        return self.toplam_puan
    
    def sonuc_al(self):
        """Sonuçları detaylı olarak al"""
        sonuclar = []
        
        for soru_id in self.sorular:
            try:
                soru = Soru.objects.get(id=soru_id)
                verilen_cevap_id = self.cevaplar.get(str(soru_id))
                
                if verilen_cevap_id:
                    verilen_cevap = Cevap.objects.get(id=verilen_cevap_id)
                    dogru_cevap = Cevap.objects.get(soru=soru, dogru_mu=True)
                    
                    sonuclar.append({
                        'soru': soru,
                        'verilen_cevap': verilen_cevap,
                        'dogru_cevap': dogru_cevap,
                        'dogru_mu': verilen_cevap.dogru_mu,
                    })
                else:
                    # Cevap verilmemiş
                    dogru_cevap = Cevap.objects.get(soru=soru, dogru_mu=True)
                    sonuclar.append({
                        'soru': soru,
                        'verilen_cevap': None,
                        'dogru_cevap': dogru_cevap,
                        'dogru_mu': False,
                    })
            except:
                continue
        
        return sonuclar

# ==================== ROZET SİSTEMİ ====================

class Rozet(models.Model):
    """Rozet tanımları"""
    adi = models.CharField(max_length=100, unique=True, verbose_name="Rozet Adı")
    aciklama = models.TextField(verbose_name="Açıklama")
    ikon = models.CharField(max_length=50, default='🏆', verbose_name="İkon (Emoji)")
    
    # Koşul türü
    kosul_turu = models.CharField(
        max_length=50,
        choices=[
            ('soru_sayisi', 'Çözülen Soru Sayısı'),
            ('toplam_puan', 'Toplam Puan'),
            ('dogru_sayisi', 'Toplam Doğru Sayısı'),
            ('basari_orani', 'Başarı Oranı'),
            ('seri', 'Seri (Üst Üste Doğru)'),
        ],
        verbose_name="Koşul Türü"
    )
    kosul_degeri = models.IntegerField(verbose_name="Koşul Değeri")
    sira = models.IntegerField(default=0, verbose_name="Sıra")

    def __str__(self):
        return f"{self.ikon} {self.adi}"

    class Meta:
        verbose_name = "Rozet"
        verbose_name_plural = "Rozetler"
        ordering = ['sira', 'kosul_degeri']


class KullaniciRozet(models.Model):
    """Kullanıcıların kazandığı rozetler"""
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rozetler')
    rozet = models.ForeignKey(Rozet, on_delete=models.CASCADE)  # ✅ ForeignKey eklendi
    kazanma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kullanici.username} - {self.rozet.adi}"

    class Meta:
        verbose_name = "Kullanıcı Rozeti"
        verbose_name_plural = "Kullanıcı Rozetleri"
        unique_together = ['kullanici', 'rozet']  # ✅ Aynı rozet tekrar kazanılmasın
        ordering = ['-kazanma_tarihi']