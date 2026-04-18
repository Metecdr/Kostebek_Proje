import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date


# ==================== SINAV SECIMI ====================

SINAV_TIPI_SECENEKLERI = [
    ('tyt', 'TYT'),
    ('ayt', 'AYT'),
]


# ==================== KONU MODELİ ====================

class Konu(models.Model):
    """Konu Modeli"""
    isim = models.CharField(max_length=100, verbose_name='Konu İsmi')
    
    DERS_SECENEKLERI = [
        ('fizik', 'Fizik'),
        ('kimya', 'Kimya'),
        ('turkce', 'Türkçe'),
        ('tarih', 'Tarih'),
        ('cografya', 'Coğrafya'),
        ('felsefe', 'Felsefe'),
        ('biyoloji', 'Biyoloji'),
        ('edebiyat', 'Edebiyat'),
    ]
    
    ders = models.CharField(
        max_length=20, 
        choices=DERS_SECENEKLERI, 
        verbose_name='Ders', 
        default='matematik', 
        db_index=True
    )
    sira = models.PositiveIntegerField(default=0, verbose_name='Sıra', db_index=True)

    class Meta:
        ordering = ['sira']
        verbose_name = 'Konu'
        verbose_name_plural = 'Konular'
        indexes = [
            models.Index(fields=['ders', 'sira'], name='konu_ders_sira_idx'),
        ]

    def __str__(self):
        return f"{self.ders.title()} - {self.isim}"


# ==================== SORU VE CEVAP MODELLERİ ====================

class Soru(models.Model):
    """Soru modeli"""
    metin = models.TextField(verbose_name='Soru Metni')
    baslik = models.CharField(max_length=100, default="", blank=True, verbose_name='Başlık')
    bul_bakalimda_cikar = models.BooleanField(default=True, db_index=True, verbose_name='Bul Bakalımda Çıksın')
    karsilasmada_cikar = models.BooleanField(default=True, db_index=True, verbose_name='Karşılaşmada Çıksın')

    DERS_SECENEKLERI = [
        ('fizik', 'Fizik'),
        ('kimya', 'Kimya'),
        ('turkce', 'Türkçe'),
        ('tarih', 'Tarih'),
        ('cografya', 'Coğrafya'),
        ('felsefe', 'Felsefe'),
        ('biyoloji', 'Biyoloji'),
        ('edebiyat', 'Edebiyat'),
    ]
    
    ders = models.CharField(
        max_length=20, 
        choices=DERS_SECENEKLERI, 
        verbose_name='Ders', 
        default='matematik', 
        db_index=True
    )
    sinav_tipi = models.CharField(max_length=10, default="", blank=True, db_index=True, verbose_name='Sınav Tipi')
    
    konu = models.ForeignKey(
        'Konu',
        on_delete=models.CASCADE,
        verbose_name='Konu',
        default=1
    )

    detayli_aciklama = models.TextField(
        blank=True,
        default='',
        verbose_name='Detaylı Açıklama',
        help_text='Doğru cevabın detaylı açıklaması (konu anlatımı gibi)'
    )

    class Meta:
        verbose_name = "Soru"
        verbose_name_plural = "Sorular"
        indexes = [
            models.Index(fields=['ders', 'bul_bakalimda_cikar'], name='soru_ders_bb_idx'),
            models.Index(fields=['ders', 'karsilasmada_cikar'], name='soru_ders_kar_idx'),
            models.Index(fields=['bul_bakalimda_cikar', 'ders'], name='soru_bb_ders_idx'),
        ]

    def __str__(self):
        return self.metin[:50] + ('...' if len(self.metin) > 50 else '')


class Cevap(models.Model):
    """Sorulara ait cevaplar"""
    soru = models.ForeignKey(Soru, on_delete=models.CASCADE, related_name='cevaplar')
    metin = models.CharField(max_length=500, verbose_name="Cevap Metni")
    dogru_mu = models.BooleanField(default=False, verbose_name="Doğru mu?", db_index=True)

    class Meta:
        verbose_name = "Cevap"
        verbose_name_plural = "Cevaplar"
        indexes = [
            models.Index(fields=['soru', 'dogru_mu'], name='cevap_soru_dogru_idx'),
        ]

    def __str__(self):
        dogru_text = "✅" if self.dogru_mu else "❌"
        return f"{dogru_text} {self.metin[:30]}"


# ==================== TABU OYUNU MODELLERİ ====================

class TabuKelime(models.Model):
    """Tabu kelimeler"""
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
            ('felsefe', 'Felsefe'),
        ],
        verbose_name="Kategori",
        db_index=True
    )

    class Meta:
        verbose_name = "Tabu Kelime"
        verbose_name_plural = "Tabu Kelimeler"

    def __str__(self):
        return f"{self.kelime} ({self.kategori})"


class YasakliKelime(models.Model):
    """Tabu kelimelerine ait yasaklı kelimeler"""
    tabu_kelime = models.ForeignKey(
        TabuKelime, 
        on_delete=models.CASCADE, 
        related_name='yasakli_kelimeler'
    )
    yasakli_kelime = models.CharField(max_length=100, verbose_name="Yasaklı Kelime")

    class Meta:
        verbose_name = "Yasaklı Kelime"
        verbose_name_plural = "Yasaklı Kelimeler"

    def __str__(self):
        return f"{self.tabu_kelime.kelime} → {self.yasakli_kelime}"


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
        db_index=True
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
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Tabu Oyunu"
        verbose_name_plural = "Tabu Oyunları"
        ordering = ['-olusturma_tarihi']

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


# ==================== KARŞILAŞMA MODELİ ====================

class KarsilasmaOdasi(models.Model):
    """1v1 Karşılaşma odaları"""
    oda_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oda_kodu = models.CharField(max_length=8, null=True, blank=True, unique=True, verbose_name="Oda Kodu")

    oyuncu1 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='karsilasma_oyuncu1',
        db_index=True
    )
    oyuncu2 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='karsilasma_oyuncu2',
        db_index=True
    )
    
    DERS_SECENEKLERI = [
        ('fizik', 'Fizik'),
        ('kimya', 'Kimya'),
        ('turkce', 'Türkçe'),
        ('tarih', 'Tarih'),
        ('cografya', 'Coğrafya'),
        ('felsefe', 'Felsefe'),
        ('biyoloji', 'Biyoloji'),
        ('edebiyat', 'Edebiyat'),
        ('karisik', 'Karışık'),
        ('karisik_sayisal', 'Karışık Sayısal'),
        ('karisik_sozel', 'Karışık Sözel'),
        ('karisik_ea', 'Karışık EA'),
        ('karisik_sozel_ayt', 'Karışık Sözel AYT'),
    ]

    secilen_ders = models.CharField(
        max_length=20,
        choices=DERS_SECENEKLERI,
        default='karisik',
        verbose_name='Seçilen Ders',
        db_index=True
    )
    
    sinav_tipi = models.CharField(
        max_length=10,
        choices=[('tyt', 'TYT'), ('ayt', 'AYT')],
        default='ayt',
        verbose_name='Sınav Tipi',
        db_index=True
    )
    
    aktif_round = models.IntegerField(default=1)
    toplam_round = models.IntegerField(default=5)
    
    round_bekleme_durumu = models.BooleanField(default=False)
    round_bitis_zamani = models.DateTimeField(null=True, blank=True)
    
    oyuncu1_skor = models.IntegerField(default=0, verbose_name="Oyuncu 1 Skoru")
    oyuncu2_skor = models.IntegerField(default=0, verbose_name="Oyuncu 2 Skoru")
    
    oyuncu1_combo = models.IntegerField(default=0, verbose_name="Oyuncu 1 Combo")
    oyuncu2_combo = models.IntegerField(default=0, verbose_name="Oyuncu 2 Combo")
    
    oyuncu1_hizli_cevap = models.IntegerField(default=0)
    oyuncu2_hizli_cevap = models.IntegerField(default=0)
    
    oyuncu1_cevap_zamani = models.DateTimeField(null=True, blank=True)
    oyuncu2_cevap_zamani = models.DateTimeField(null=True, blank=True)
    soru_baslangic_zamani = models.DateTimeField(null=True, blank=True)
    
    oyuncu1_dogru = models.IntegerField(default=0, verbose_name="Oyuncu 1 Doğru Sayısı")
    oyuncu1_yanlis = models.IntegerField(default=0, verbose_name="Oyuncu 1 Yanlış Sayısı")
    oyuncu2_dogru = models.IntegerField(default=0, verbose_name="Oyuncu 2 Doğru Sayısı")
    oyuncu2_yanlis = models.IntegerField(default=0, verbose_name="Oyuncu 2 Yanlış Sayısı")
    
    oyun_durumu = models.CharField(
        max_length=20, 
        default='bekleniyor',
        choices=[
            ('bekleniyor', 'Bekleniyor'),
            ('oynaniyor', 'Oynanıyor'),
            ('bitti', 'Bitti'),
        ],
        db_index=True
    )
    
    aktif_soru = models.ForeignKey(
        Soru, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Aktif Soru"
    )
    aktif_soru_no = models.IntegerField(default=1, verbose_name="Aktif Soru Numarası")
    toplam_soru = models.IntegerField(default=10, verbose_name="Toplam Soru Sayısı")
    
    oyuncu1_cevapladi = models.BooleanField(default=False)
    oyuncu2_cevapladi = models.BooleanField(default=False)
    
    ilk_dogru_cevaplayan = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='ilk_cevaplayan'
    )
    
    oyuncu1_hazir = models.BooleanField(default=False, verbose_name="Oyuncu 1 Hazır")
    oyuncu2_hazir = models.BooleanField(default=False, verbose_name="Oyuncu 2 Hazır")

    ara_ekran_bekleniyor = models.BooleanField(default=False, verbose_name="Ara Ekran Bekleniyor")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)
    # ✅ EKLE (views_karsilasma.py zaten set ediyor)
    bitis_zamani = models.DateTimeField(null=True, blank=True, db_index=True)

    # ✅ DISCONNECT DETECTION — her polling GET'te güncellenir
    oyuncu1_son_ping = models.DateTimeField(null=True, blank=True, verbose_name="Oyuncu1 Son Ping")
    oyuncu2_son_ping = models.DateTimeField(null=True, blank=True, verbose_name="Oyuncu2 Son Ping")

    class Meta:
        verbose_name = "Karşılaşma Odası"
        verbose_name_plural = "Karşılaşma Odaları"
        ordering = ['-olusturma_tarihi']
        indexes = [
            models.Index(fields=['oyun_durumu', '-olusturma_tarihi'], name='oda_durum_tarih_idx'),
            models.Index(fields=['oyuncu1', 'oyun_durumu'], name='oda_oyuncu1_durum_idx'),
            models.Index(fields=['oyuncu2', 'oyun_durumu'], name='oda_oyuncu2_durum_idx'),
        ]

    def calculate_score(self, oyuncu, dogru_mu, sure):
        """Gelişmiş skor hesaplama"""
        is_oyuncu1 = (self.oyuncu1 == oyuncu)
        
        if dogru_mu:
            base_puan = 10
            
            if is_oyuncu1:
                self.oyuncu1_combo += 1
                combo_bonus = min(self.oyuncu1_combo * 2, 20)
            else:
                self.oyuncu2_combo += 1
                combo_bonus = min(self.oyuncu2_combo * 2, 20)
            
            hiz_bonus = 5 if sure < 5 else 0
            ilk_bonus = 3 if self.ilk_dogru_cevaplayan is None else 0
            
            toplam_puan = base_puan + combo_bonus + hiz_bonus + ilk_bonus
            
            if is_oyuncu1:
                self.oyuncu1_skor += toplam_puan
            else:
                self.oyuncu2_skor += toplam_puan
            
            return toplam_puan
        else:
            if is_oyuncu1:
                self.oyuncu1_combo = 0
            else:
                self.oyuncu2_combo = 0
            
            return 0

    def yeni_soru_getir(self):
        """Rastgele yeni soru getir"""
        return Soru.objects.order_by('?').first()

    def __str__(self):
        oyuncu2_adi = self.oyuncu2.username if self.oyuncu2 else 'Bekleniyor'
        return f"{self.oyuncu1.username} vs {oyuncu2_adi} - {self.oyun_durumu}"


# ==================== KULLANICI CEVAP MODELİ ====================

class KullaniciCevap(models.Model):
    """Kullanıcının verdiği cevapları kaydeder"""
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    oda = models.ForeignKey(KarsilasmaOdasi, on_delete=models.CASCADE)
    soru = models.ForeignKey(Soru, on_delete=models.CASCADE)
    verilen_cevap = models.ForeignKey(Cevap, on_delete=models.CASCADE, null=True, blank=True)
    dogru_mu = models.BooleanField(db_index=True)
    tarih = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Kullanıcı Cevabı"
        verbose_name_plural = "Kullanıcı Cevapları"
        ordering = ['-tarih']
        # ✅ DB-level duplicate engeli — race condition'a karşı son savunma hattı
        unique_together = [['kullanici', 'oda', 'soru']]
        indexes = [
            models.Index(fields=['kullanici', '-tarih'], name='cevap_kullanici_idx'),
            models.Index(fields=['kullanici', 'dogru_mu'], name='cevap_kullanici_dogru_idx'),
        ]

    def __str__(self):
        durum = "✅ Doğru" if self.dogru_mu else "❌ Yanlış"
        return f"{self.kullanici.username} - {self.soru.metin[:30]}... - {durum}"


# ==================== BUL BAKALIM ====================

class BulBakalimOyun(models.Model):
    """Bul Bakalım oyun oturumu"""
    OYUN_DURUMU_SECENEKLERI = [
        ('devam_ediyor', 'Devam Ediyor'),
        ('bitti', 'Bitti'),
    ]

    DERS_SECENEKLERI = [
        ('fizik', 'Fizik'),
        ('kimya', 'Kimya'),
        ('turkce', 'Türkçe'),
        ('tarih', 'Tarih'),
        ('cografya', 'Coğrafya'),
        ('felsefe', 'Felsefe'),
        ('biyoloji', 'Biyoloji'),
        ('edebiyat', 'Edebiyat'),
        ('karisik', 'Karışık'),
        ('karisik_sayisal', 'Karışık Sayısal'),
        ('karisik_sozel', 'Karışık Sözel'),
        ('karisik_ea', 'Karışık EA'),
        ('karisik_sozel_ayt', 'Karışık Sözel AYT'),
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
    oyuncu = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bul_bakalim_oyunlari', db_index=True)
    oyun_durumu = models.CharField(max_length=20, choices=OYUN_DURUMU_SECENEKLERI, default='devam_ediyor', db_index=True)
    
    dogru_sayisi = models.IntegerField(default=0)
    yanlis_sayisi = models.IntegerField(default=0)
    toplam_puan = models.IntegerField(default=0)
    
    sorular = models.JSONField(default=list)
    cevaplar = models.JSONField(default=dict)
    
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)
    bitirme_tarihi = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'bul_bakalim_oyun'
        verbose_name = 'Bul Bakalım Oyunu'
        verbose_name_plural = 'Bul Bakalım Oyunları'
        ordering = ['-olusturulma_tarihi']
        indexes = [
            models.Index(fields=['oyuncu', '-olusturulma_tarihi'], name='bb_oyuncu_tarih_idx'),
            models.Index(fields=['oyuncu', 'oyun_durumu'], name='bb_oyuncu_durum_idx'),
        ]
    
    def oyun_bitir(self):
        """Oyunu bitir ve puanları hesapla"""
        self.oyun_durumu = 'bitti'
        self.bitirme_tarihi = timezone.now()
        
        if self.dogru_sayisi >= 6:
            self.toplam_puan = 10
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

    def __str__(self):
        return f"{self.oyuncu.username} - {self.dogru_sayisi}/10 - {self.oyun_durumu}"


# ==================== ROZET SİSTEMİ ====================

class Rozet(models.Model):
    """Rozet tanımları"""
    adi = models.CharField(max_length=100, unique=True, verbose_name="Rozet Adı")
    aciklama = models.TextField(verbose_name="Açıklama")
    ikon = models.CharField(max_length=50, default='🏆', verbose_name="İkon (Emoji)")
    
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
    sira = models.IntegerField(default=0, verbose_name="Sıra", db_index=True)

    class Meta:
        verbose_name = "Rozet"
        verbose_name_plural = "Rozetler"
        ordering = ['sira', 'kosul_degeri']

    def __str__(self):
        return f"{self.ikon} {self.adi}"


class KullaniciRozet(models.Model):
    """Kullanıcıların kazandığı rozetler"""
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rozetler', db_index=True)
    rozet = models.ForeignKey(Rozet, on_delete=models.CASCADE)
    kazanma_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Kullanıcı Rozeti"
        verbose_name_plural = "Kullanıcı Rozetleri"
        unique_together = ['kullanici', 'rozet']
        ordering = ['-kazanma_tarihi']
        indexes = [
            models.Index(fields=['kullanici', '-kazanma_tarihi'], name='kulrozet_kullanici_idx'),
        ]

    def __str__(self):
        return f"{self.kullanici.username} - {self.rozet.adi}"


# ==================== OYUN MESAJ ====================

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

    def __str__(self):
        return f"{self.gonderen.username} - {self.icerik}"


# ==================== 🏆 TURNUVA SİSTEMİ ====================

class Turnuva(models.Model):
    """Turnuva modeli"""
    DURUM_SECENEKLERI = [
        ('beklemede', 'Beklemede'),
        ('kayit_acik', 'Kayıt Açık'),
        ('basladi', 'Başladı'),
        ('devam_ediyor', 'Devam Ediyor'),
        ('bitti', 'Bitti'),
    ]
    
    TUR_SECENEKLERI = [
        ('TYT', 'TYT'),
        ('AYT', 'AYT'),
    ]
    
    turnuva_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    isim = models.CharField(max_length=200, verbose_name='Turnuva İsmi')
    aciklama = models.TextField(verbose_name='Açıklama', blank=True)
    
    # Tarih ve saat
    kayit_baslangic = models.DateTimeField(verbose_name='Kayıt Başlangıç', db_index=True)
    kayit_bitis = models.DateTimeField(verbose_name='Kayıt Bitiş', db_index=True)
    baslangic = models.DateTimeField(verbose_name='Turnuva Başlangıç', db_index=True)
    bitis = models.DateTimeField(verbose_name='Turnuva Bitiş', null=True, blank=True)
    
    # Turnuva bilgileri
    sinav_tipi = models.CharField(max_length=10, choices=TUR_SECENEKLERI, default='AYT')
    ders = models.CharField(max_length=50, default='karisik')
    toplam_soru = models.IntegerField(default=10, verbose_name='Toplam Soru Sayısı')
    max_katilimci = models.IntegerField(default=32, verbose_name='Maksimum Katılımcı')
    
    # Ödüller
    odul_xp_1 = models.IntegerField(default=1000, verbose_name='1. Ödül XP')
    odul_xp_2 = models.IntegerField(default=500, verbose_name='2. Ödül XP')
    odul_xp_3 = models.IntegerField(default=250, verbose_name='3. Ödül XP')
    
    # Durum
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='beklemede', db_index=True)
    katilimcilar = models.ManyToManyField(User, related_name='turnuvalar', blank=True)
    
    # Kazananlar
    birinci = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='birinci_turnuvalar')
    ikinci = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ikinci_turnuvalar')
    ucuncu = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ucuncu_turnuvalar')
    
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Turnuva'
        verbose_name_plural = 'Turnuvalar'
        ordering = ['-baslangic']
        indexes = [
            models.Index(fields=['durum', '-baslangic'], name='turnuva_durum_idx'),
            models.Index(fields=['kayit_baslangic', 'kayit_bitis'], name='turnuva_kayit_idx'),
        ]
    
    def __str__(self):
        return f"{self.isim} ({self.get_durum_display()})"
    
    @property
    def katilimci_sayisi(self):
        return self.katilimcilar.count()
    
    @property
    def dolu_mu(self):
        return self.katilimci_sayisi >= self.max_katilimci
    
    @property
    def kayit_acik_mi(self):
        now = timezone.now()
        return (self.durum == 'kayit_acik' and 
                self.kayit_baslangic <= now <= self.kayit_bitis and 
                not self.dolu_mu)


class TurnuvaMaci(models.Model):
    """Turnuva maçı modeli"""
    ROUND_SECENEKLERI = [
        (1, 'Round 1'),
        (2, 'Round 2'),
        (3, 'Round 3'),
        (4, 'Round 4'),
        (5, 'Round 5'),
    ]
    
    mac_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    turnuva = models.ForeignKey(Turnuva, on_delete=models.CASCADE, related_name='maclar')
    round = models.IntegerField(choices=ROUND_SECENEKLERI, verbose_name='Tur', db_index=True)
    
    # Oyuncular
    oyuncu1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turnuva_mac_oyuncu1', null=True, blank=True)
    oyuncu2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turnuva_mac_oyuncu2', null=True, blank=True)
    
    # Skorlar
    oyuncu1_skor = models.IntegerField(default=0)
    oyuncu2_skor = models.IntegerField(default=0)
    
    # Kazanan
    kazanan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='kazanilan_turnuva_maclari')
    
    # Maç bilgisi
    karsilasma_oda = models.ForeignKey(KarsilasmaOdasi, on_delete=models.SET_NULL, null=True, blank=True)
    tamamlandi = models.BooleanField(default=False, db_index=True)
    
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    mac_tarihi = models.DateTimeField(null=True, blank=True)
    
    # ✅ YENİ ALANLAR
    mac_baslangic_zamani = models.DateTimeField(null=True, blank=True, verbose_name='Maç Başlangıç Zamanı')
    oyuncu1_hazir = models.BooleanField(default=False, verbose_name='Oyuncu 1 Hazır')
    oyuncu2_hazir = models.BooleanField(default=False, verbose_name='Oyuncu 2 Hazır')

    
    class Meta:
        verbose_name = 'Turnuva Maçı'
        verbose_name_plural = 'Turnuva Maçları'
        ordering = ['round', 'olusturma_tarihi']
        indexes = [
            models.Index(fields=['turnuva', 'round'], name='mac_turnuva_round_idx'),
            models.Index(fields=['turnuva', 'tamamlandi'], name='mac_turnuva_tamamlandi_idx'),
        ]

    @property
    def her_iki_oyuncu_hazir(self):
        """Her iki oyuncu da hazır mı?"""
        return self.oyuncu1_hazir and self.oyuncu2_hazir

    @property
    def mac_baslayabilir_mi(self):
        """Maç başlayabilir mi?"""
        from django.utils import timezone
        now = timezone.now()
        
        # Karşılaşma odası yoksa başlayamaz
        if not self.karsilasma_oda:
            return False
        
        # Zaman kontrolü
        if self.mac_baslangic_zamani:
            # 5 dakika önceden hazırlanabilir
            baslama_penceresi_baslangic = self.mac_baslangic_zamani - timedelta(minutes=5)
            # 5 dakika geç giriş
            baslama_penceresi_bitis = self.mac_baslangic_zamani + timedelta(minutes=5)
            
            if baslama_penceresi_baslangic <= now <= baslama_penceresi_bitis:
                return self.her_iki_oyuncu_hazir
        
        # Zaman belirtilmemişse sadece hazır olma kontrolü
        return self.her_iki_oyuncu_hazir
    
    def __str__(self):
        oyuncu1_str = self.oyuncu1.username if self.oyuncu1 else 'BYE'
        oyuncu2_str = self.oyuncu2.username if self.oyuncu2 else 'BYE'
        return f"{self.turnuva.isim} - {self.get_round_display()}: {oyuncu1_str} vs {oyuncu2_str}"


class TurnuvaKatilim(models.Model):
    """Turnuva katılım kaydı"""
    turnuva = models.ForeignKey(Turnuva, on_delete=models.CASCADE, related_name='katilimlar')
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turnuva_katilimlari')
    katilim_tarihi = models.DateTimeField(auto_now_add=True, db_index=True)
    sira = models.IntegerField(default=0)
    elendi = models.BooleanField(default=False, db_index=True)
    elenme_turu = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Turnuva Katılım'
        verbose_name_plural = 'Turnuva Katılımları'
        unique_together = ['turnuva', 'kullanici']
        ordering = ['sira']
        indexes = [
            models.Index(fields=['turnuva', 'sira'], name='katilim_turnuva_sira_idx'),
            models.Index(fields=['kullanici', '-katilim_tarihi'], name='katilim_kullanici_idx'),
        ]
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.turnuva.isim}"


class TurnuvaSiralama(models.Model):
    """Turnuva sıralama tablosu"""
    turnuva = models.ForeignKey(Turnuva, on_delete=models.CASCADE, related_name='siralama')
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Sıralama bilgileri
    sira = models.IntegerField(default=0, verbose_name='Sıra')
    elesme_round = models.IntegerField(default=0, verbose_name='Eleme Round')  # Hangi roundda elendi
    
    # Maç istatistikleri
    oynanan_mac = models.IntegerField(default=0, verbose_name='Oynanan Maç')
    kazanilan_mac = models.IntegerField(default=0, verbose_name='Kazanılan Maç')
    kaybedilen_mac = models.IntegerField(default=0, verbose_name='Kaybedilen Maç')
    
    # Skor istatistikleri
    toplam_skor = models.IntegerField(default=0, verbose_name='Toplam Skor')
    ortalama_skor = models.FloatField(default=0.0, verbose_name='Ortalama Skor')
    en_yuksek_skor = models.IntegerField(default=0, verbose_name='En Yüksek Skor')
    
    # Soru istatistikleri
    toplam_dogru = models.IntegerField(default=0, verbose_name='Toplam Doğru')
    toplam_yanlis = models.IntegerField(default=0, verbose_name='Toplam Yanlış')
    dogru_yuzdesi = models.FloatField(default=0.0, verbose_name='Doğruluk Yüzdesi')
    
    # Ödül
    kazanilan_xp = models.IntegerField(default=0, verbose_name='Kazanılan XP')
    
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Turnuva Sıralaması'
        verbose_name_plural = 'Turnuva Sıralamaları'
        ordering = ['sira']
        unique_together = ['turnuva', 'kullanici']
        indexes = [
            models.Index(fields=['turnuva', 'sira'], name='siralama_turnuva_sira_idx'),
        ]
    
    def __str__(self):
        return f"{self.turnuva.isim} - {self.sira}. {self.kullanici.username}"


class MeydanOkuma(models.Model):
    """Arkadaşa Meydan Okuma"""

    DURUM_SECENEKLERI = [
        ('beklemede', 'Beklemede'),
        ('kabul_edildi', 'Kabul Edildi'),
        ('reddedildi', 'Reddedildi'),
        ('suresi_doldu', 'Süresi Doldu'),
    ]

    gonderen = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='gonderilen_meydan_okumalar',
        verbose_name='Gönderen'
    )
    alan = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='alinan_meydan_okumalar',
        verbose_name='Alan'
    )
    oda = models.ForeignKey(
        KarsilasmaOdasi,
        on_delete=models.CASCADE,
        related_name='meydan_okuma',
        verbose_name='Karşılaşma Odası'
    )
    secilen_ders = models.CharField(
        max_length=30,
        default='karisik',
        verbose_name='Seçilen Ders'
    )
    sinav_tipi = models.CharField(
        max_length=10,
        default='AYT',
        verbose_name='Sınav Tipi'
    )
    durum = models.CharField(
        max_length=20,
        choices=DURUM_SECENEKLERI,
        default='beklemede',
        db_index=True,
        verbose_name='Durum'
    )
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Oluşturma Tarihi'
    )

    class Meta:
        verbose_name = 'Meydan Okuma'
        verbose_name_plural = 'Meydan Okumalar'
        ordering = ['-olusturma_tarihi']
        indexes = [
            models.Index(fields=['alan', 'durum'], name='meydan_alan_durum_idx'),
            models.Index(fields=['gonderen', 'durum'], name='meydan_gonderen_durum_idx'),
        ]

    def suresi_gecti_mi(self):
        """5 dakika geçti mi?"""
        from django.utils import timezone
        return (timezone.now() - self.olusturma_tarihi).total_seconds() > 300

    def __str__(self):
        return f"{self.gonderen.username} → {self.alan.username} ({self.get_durum_display()})"


# ==================== GÜNÜN SORUSU ====================

class GununSorusu(models.Model):
    """Her gün için öne çıkarılan soru"""
    soru = models.ForeignKey(Soru, on_delete=models.CASCADE, verbose_name='Soru')
    tarih = models.DateField(unique=True, default=date.today, verbose_name='Tarih', db_index=True)
    bonus_xp = models.IntegerField(default=15, verbose_name='Bonus XP')

    class Meta:
        verbose_name = 'Günün Sorusu'
        verbose_name_plural = 'Günün Soruları'
        ordering = ['-tarih']

    def __str__(self):
        return f"Günün Sorusu - {self.tarih}"


class GununSorusuCevap(models.Model):
    """Kullanıcının günün sorusuna verdiği cevap"""
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    gunun_sorusu = models.ForeignKey(GununSorusu, on_delete=models.CASCADE, related_name='cevaplar')
    secilen_cevap = models.ForeignKey('Cevap', on_delete=models.CASCADE, null=True, blank=True)
    dogru_mu = models.BooleanField()
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Günün Sorusu Cevabı'
        verbose_name_plural = 'Günün Sorusu Cevapları'
        unique_together = ['kullanici', 'gunun_sorusu']

    def __str__(self):
        return f"{self.kullanici.username} - {self.gunun_sorusu.tarih}"


# ==================== SORU BİLDİR ====================

class SoruBildir(models.Model):
    """Hatalı/yanlış soru bildirimleri"""
    SEBEP_SECENEKLERI = [
        ('yanlis_cevap', 'Yanlış cevap işaretlenmiş'),
        ('hatali_soru', 'Soru hatalı/yanlış yazılmış'),
        ('konu_yanlisi', 'Yanlış konuya atanmış'),
        ('diger', 'Diğer'),
    ]

    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    soru = models.ForeignKey(Soru, on_delete=models.CASCADE, related_name='bildirimler', db_index=True)
    sebep_kodu = models.CharField(max_length=20, choices=SEBEP_SECENEKLERI, default='diger')
    aciklama = models.CharField(max_length=300, blank=True)
    tarih = models.DateTimeField(auto_now_add=True, db_index=True)
    incelendi = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = 'Soru Bildirimi'
        verbose_name_plural = 'Soru Bildirimleri'
        ordering = ['-tarih']

    def __str__(self):
        return f"#{self.soru_id} - {self.kullanici.username} - {self.get_sebep_kodu_display()}"