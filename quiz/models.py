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
    ders = models.CharField(max_length=20, choices=DERS_SECENEKLERI, verbose_name='Ders', default='matematik', db_index=True)  # ✅ INDEX
    sira = models.PositiveIntegerField(default=0, verbose_name='Sıra', db_index=True)  # ✅ INDEX

    class Meta:
        ordering = ['sira']  # Varsayılan sıralama 'sira' alanına göre yapılacak
        # ✅ COMPOSITE INDEX
        indexes = [
            models.Index(fields=['ders', 'sira'], name='konu_ders_sira_idx'),
        ]

    def __str__(self):
        return self.isim


# ==================== SORU VE CEVAP MODELLERİ ====================

class Soru(models.Model):
    metin = models.TextField()
    baslik = models.CharField(max_length=100, default="", blank=True)
    bul_bakalimda_cikar = models.BooleanField(default=True, db_index=True)  # ✅ INDEX
    karsilasmada_cikar = models.BooleanField(default=True, db_index=True)  # ✅ INDEX

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
    ders = models.CharField(max_length=20, choices=DERS_SECENEKLERI, verbose_name='Ders', default='matematik', db_index=True)  # ✅ INDEX

    sinav_tipi = models.CharField(max_length=10, default="", blank=True, db_index=True)  # ✅ INDEX
    
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
        # ✅ COMPOSITE INDEX'LER - SORU MODELİNDE
        indexes = [
            models.Index(fields=['ders', 'bul_bakalimda_cikar'], name='soru_ders_bb_idx'),
            models.Index(fields=['ders', 'karsilasmada_cikar'], name='soru_ders_kar_idx'),
            models.Index(fields=['bul_bakalimda_cikar', 'ders'], name='soru_bb_ders_idx'),
        ]


class Cevap(models.Model):
    """Sorulara ait cevaplar"""
    soru = models.ForeignKey(Soru, on_delete=models.CASCADE, related_name='cevaplar')
    metin = models.CharField(max_length=500, verbose_name="Cevap Metni")
    dogru_mu = models.BooleanField(default=False, verbose_name="Doğru mu?", db_index=True)  # ✅ INDEX

    def __str__(self):
        dogru_text = "✅" if self.dogru_mu else "❌"
        return f"{dogru_text} {self.metin[:30]}"

    class Meta:
        verbose_name = "Cevap"
        verbose_name_plural = "Cevaplar"
        # ✅ COMPOSITE INDEX'LER (Sık kullanılan sorgular için)
        indexes = [
            models.Index(fields=['soru', 'dogru_mu'], name='cevap_soru_dogru_idx'),
        ]



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
        verbose_name="Kategori",
        db_index=True  # ✅ INDEX

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
        ],
        db_index=True  # ✅ INDEX
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
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)  # ✅ INDEX

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
        related_name='karsilasma_oyuncu1',
        db_index=True  # ✅ INDEX
    )
    oyuncu2 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='karsilasma_oyuncu2',
        db_index=True  # ✅ INDEX
    )
    

    # ✅ ROUND SİSTEMİ
    aktif_round = models.IntegerField(default=1)
    toplam_round = models.IntegerField(default=5)  # 5 soru = 5 round
    
    # ✅ ROUND ARASI MOLA
    round_bitti = models.BooleanField(default=False)
    round_bitis_zamani = models.DateTimeField(null=True, blank=True)

    # Skorlar
    oyuncu1_skor = models.IntegerField(default=0, verbose_name="Oyuncu 1 Skoru")
    oyuncu2_skor = models.IntegerField(default=0, verbose_name="Oyuncu 2 Skoru")

    # ✅ COMBO SİSTEMİ
    oyuncu1_combo = models.IntegerField(default=0, verbose_name="Oyuncu 1 Combo")
    oyuncu2_combo = models.IntegerField(default=0, verbose_name="Oyuncu 2 Combo")
    
    # ✅ HIZLI CEVAP BONUSU
    oyuncu1_hizli_cevap = models.IntegerField(default=0)
    oyuncu2_hizli_cevap = models.IntegerField(default=0)

    # ✅ HIZ BONUSU İÇİN ZAMAN KAYDI
    oyuncu1_cevap_zamani = models.DateTimeField(null=True, blank=True)
    oyuncu2_cevap_zamani = models.DateTimeField(null=True, blank=True)
    soru_baslangic_zamani = models.DateTimeField(null=True, blank=True)
    
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)
    
    def calculate_score(self, oyuncu, dogru_mu, sure):
        """Gelişmiş skor hesaplama"""
        is_oyuncu1 = (self.oyuncu1 == oyuncu)
        
        if dogru_mu:
            base_puan = 10
            
            # ✅ COMBO BONUSU
            if is_oyuncu1:
                self.oyuncu1_combo += 1
                combo_bonus = min(self.oyuncu1_combo * 2, 20)  # Max 20 bonus
            else:
                self.oyuncu2_combo += 1
                combo_bonus = min(self.oyuncu2_combo * 2, 20)
            
            # ✅ HIZLI CEVAP BONUSU (5 saniye içinde)
            hiz_bonus = 5 if sure < 5 else 0
            
            # ✅ İLK DOĞRU BONUSU
            ilk_bonus = 3 if self.ilk_dogru_cevaplayan is None else 0
            
            toplam_puan = base_puan + combo_bonus + hiz_bonus + ilk_bonus
            
            if is_oyuncu1:
                self.oyuncu1_skor += toplam_puan
            else:
                self.oyuncu2_skor += toplam_puan
            
            return toplam_puan
        else:
            # ✅ YANLIŞ CEVAP - COMBO SIFIRLA
            if is_oyuncu1:
                self.oyuncu1_combo = 0
            else:
                self.oyuncu2_combo = 0
            
            return 0

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
        ],
        db_index=True  # ✅ INDEX
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
    
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)  # ✅ INDEX

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
        # ✅ COMPOSITE INDEX'LER (Kritik sorgular için)
        indexes = [
            models.Index(fields=['oyun_durumu', '-olusturma_tarihi'], name='oda_durum_tarih_idx'),
            models.Index(fields=['oyuncu1', 'oyun_durumu'], name='oda_oyuncu1_durum_idx'),
            models.Index(fields=['oyuncu2', 'oyun_durumu'], name='oda_oyuncu2_durum_idx'),
        ]


# ==================== KULLANICI CEVAP MODELİ ====================

class KullaniciCevap(models.Model):
    """Kullanıcının verdiği cevapları kaydeder (yanlış analizi için)"""
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)  # ✅ INDEX
    oda = models.ForeignKey(KarsilasmaOdasi, on_delete=models.CASCADE)
    soru = models.ForeignKey(Soru, on_delete=models.CASCADE)
    verilen_cevap = models.ForeignKey(Cevap, on_delete=models.CASCADE)
    dogru_mu = models.BooleanField(db_index=True)  # ✅ INDEX
    tarih = models.DateTimeField(auto_now_add=True, db_index=True)  # ✅ INDEX

    def __str__(self):
        durum = "✅ Doğru" if self.dogru_mu else "❌ Yanlış"
        return f"{self.kullanici.username} - {self.soru.metin[:30]}... - {durum}"

    class Meta:
        verbose_name = "Kullanıcı Cevabı"
        verbose_name_plural = "Kullanıcı Cevapları"
        ordering = ['-tarih']
        # ✅ COMPOSITE INDEX
        indexes = [
            models.Index(fields=['kullanici', '-tarih'], name='cevap_kullanici_idx'),
            models.Index(fields=['kullanici', 'dogru_mu'], name='cevap_kullanici_dogru_idx'),
        ]


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
        verbose_name='Seçilen Ders',
        db_index=True
    )

    sinav_tipi = models.CharField(
        max_length=10,
        choices=[('tyt', 'TYT'), ('ayt', 'AYT')],
        null=True,
        blank=True,
        verbose_name='Sınav Tipi',
        db_index=True
    )
    
    oyun_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oyuncu = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bul_bakalim_oyunlari', db_index=True)  # ✅ INDEX
    oyun_durumu = models.CharField(max_length=20, choices=OYUN_DURUMU_SECENEKLERI, default='devam_ediyor', db_index=True)  # ✅ INDEX
    
    # Skorlar
    dogru_sayisi = models.IntegerField(default=0)
    yanlis_sayisi = models.IntegerField(default=0)
    toplam_puan = models.IntegerField(default=0)
    
    # Sorular ve cevaplar (JSON olarak sakla)
    sorular = models.JSONField(default=list)  # [soru_id1, soru_id2, ...]
    cevaplar = models.JSONField(default=dict)  # {soru_id: cevap_id, ...}
    
    # Tarihler
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)  # ✅ INDEX
    bitirme_tarihi = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'bul_bakalim_oyun'
        verbose_name = 'Bul Bakalım Oyunu'
        verbose_name_plural = 'Bul Bakalım Oyunları'
        ordering = ['-olusturulma_tarihi']
        # ✅ COMPOSITE INDEX'LER
        indexes = [
            models.Index(fields=['oyuncu', '-olusturulma_tarihi'], name='bb_oyuncu_tarih_idx'),
            models.Index(fields=['oyuncu', 'oyun_durumu'], name='bb_oyuncu_durum_idx'),
        ]
    
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
        verbose_name="Koşul Türü",
        db_index=True
    )
    kosul_degeri = models.IntegerField(verbose_name="Koşul Değeri")
    sira = models.IntegerField(default=0, verbose_name="Sıra", db_index=True)  # ✅ INDEX

    def __str__(self):
        return f"{self.ikon} {self.adi}"

    class Meta:
        verbose_name = "Rozet"
        verbose_name_plural = "Rozetler"
        ordering = ['sira', 'kosul_degeri']


class KullaniciRozet(models.Model):
    """Kullanıcıların kazandığı rozetler"""
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rozetler', db_index=True)  # ✅ INDEX
    rozet = models.ForeignKey(Rozet, on_delete=models.CASCADE)  # ✅ ForeignKey eklendi
    kazanma_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)  # ✅ INDEX

    def __str__(self):
        return f"{self.kullanici.username} - {self.rozet.adi}"

    class Meta:
        verbose_name = "Kullanıcı Rozeti"
        verbose_name_plural = "Kullanıcı Rozetleri"
        unique_together = ['kullanici', 'rozet']  # ✅ Aynı rozet tekrar kazanılmasın
        ordering = ['-kazanma_tarihi']
        # ✅ COMPOSITE INDEX
        indexes = [
            models.Index(fields=['kullanici', '-kazanma_tarihi'], name='kulrozet_kullanici_idx'),
        ]


class OyunMesaj(models.Model):
    """Oyun içi emoji/mesaj sistemi"""
    oda = models.ForeignKey(KarsilasmaOdasi, on_delete=models.CASCADE, related_name='mesajlar')
    gonderen = models.ForeignKey(User, on_delete=models.CASCADE)
    mesaj_tipi = models.CharField(max_length=20, choices=[
        ('emoji', 'Emoji'),
        ('hizli_mesaj', 'Hızlı Mesaj'),
    ])
    icerik = models.CharField(max_length=100)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-olusturma_tarihi']
        indexes = [
            models.Index(fields=['oda', '-olusturma_tarihi']),
        ]