from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import profile.rozet_aciklama as rozet_aciklama


class OgrenciProfili(models.Model):
    """Öğrenci Profil Modeli - Temel kullanıcı bilgileri ve istatistikleri"""
    
    ALAN_SECENEKLERI = [
        ('sayisal', 'Sayısal'),
        ('sozel', 'Sözel'),
        ('esit_agirlik', 'Eşit Ağırlık'),
        ('dil', 'Dil'),
    ]
    
    # TEMEL BİLGİLER
    kullanici = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profil',
        verbose_name='Kullanıcı'
    )
    alan = models.CharField(
        max_length=20, 
        choices=ALAN_SECENEKLERI, 
        default='sayisal',
        verbose_name='Alan'
    )
    profil_fotografi = models.ImageField(
        upload_to='profil_fotograflari/', 
        null=True, 
        blank=True,
        verbose_name='Profil Fotoğrafı'
    )
    
    # TOPLAM İSTATİSTİKLER
    toplam_puan = models.IntegerField(
        default=0, 
        db_index=True,
        verbose_name='Toplam Puan'
    )
    cozulen_soru_sayisi = models.IntegerField(
        default=0, 
        db_index=True,
        verbose_name='Çözülen Soru Sayısı'
    )
    toplam_dogru = models.IntegerField(
        default=0,
        verbose_name='Toplam Doğru'
    )
    toplam_yanlis = models.IntegerField(
        default=0,
        verbose_name='Toplam Yanlış'
    )
    
    # PERİYODİK PUANLAR
    gunluk_puan = models.IntegerField(
        default=0, 
        db_index=True,
        verbose_name='Günlük Puan'
    )
    haftalik_puan = models.IntegerField(
        default=0, 
        db_index=True,
        verbose_name='Haftalık Puan'
    )
    aylik_puan = models.IntegerField(
        default=0, 
        db_index=True,
        verbose_name='Aylık Puan'
    )
    
    # PERİYODİK İSTATİSTİKLER
    gunluk_cozulen = models.IntegerField(default=0, verbose_name='Günlük Çözülen')
    gunluk_dogru = models.IntegerField(default=0, verbose_name='Günlük Doğru')
    gunluk_yanlis = models.IntegerField(default=0, verbose_name='Günlük Yanlış')
    
    haftalik_cozulen = models.IntegerField(default=0, verbose_name='Haftalık Çözülen')
    haftalik_dogru = models.IntegerField(default=0, verbose_name='Haftalık Doğru')
    haftalik_yanlis = models.IntegerField(default=0, verbose_name='Haftalık Yanlış')
    
    aylik_cozulen = models.IntegerField(default=0, verbose_name='Aylık Çözülen')
    aylik_dogru = models.IntegerField(default=0, verbose_name='Aylık Doğru')
    aylik_yanlis = models.IntegerField(default=0, verbose_name='Aylık Yanlış')
    
    # RESET TARİHLERİ
    son_gunluk_reset = models.DateField(
        default=timezone.now,
        verbose_name='Son Günlük Reset'
    )
    son_haftalik_reset = models.DateField(
        default=timezone.now,
        verbose_name='Son Haftalık Reset'
    )
    son_aylik_reset = models.DateField(
        default=timezone.now,
        verbose_name='Son Aylık Reset'
    )
    hafta_baslangic = models.DateTimeField(
        default=timezone.now,
        verbose_name='Hafta Başlangıç'
    )
    
    # ROZET SİSTEMİ
    unvanlar = models.CharField(
        max_length=255, 
        default='Çaylak',
        verbose_name='Unvanlar'
    )
    
    # TARİH BİLGİLERİ
    kayit_tarihi = models.DateTimeField(
        auto_now_add=True, 
        db_index=True,
        verbose_name='Kayıt Tarihi'
    )
    son_giris = models.DateTimeField(
        auto_now=True,
        verbose_name='Son Giriş'
    )
    aktif_mi = models.BooleanField(
        default=True,
        verbose_name='Aktif Mi'
    )
    
    class Meta:
        verbose_name = 'Öğrenci Profili'
        verbose_name_plural = 'Öğrenci Profilleri'
        ordering = ['-toplam_puan']
        indexes = [
            models.Index(fields=['-toplam_puan'], name='profil_toplam_idx'),
            models.Index(fields=['-haftalik_puan'], name='profil_haftalik_idx'),
            models.Index(fields=['-aylik_puan'], name='profil_aylik_idx'),
            models.Index(fields=['-gunluk_puan'], name='profil_gunluk_idx'),
            models.Index(fields=['alan', '-toplam_puan'], name='profil_alan_puan_idx'),
        ]
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.toplam_puan} puan"
    
    def puan_ekle(self, puan):
        """Puan ekleme ve otomatik reset kontrolleri"""
        self.reset_kontrolu()
        self.toplam_puan += puan
        self.gunluk_puan += puan
        self.haftalik_puan += puan
        self.aylik_puan += puan
        self.save()
    
    def reset_kontrolu(self):
        """Otomatik reset kontrolleri"""
        bugun = timezone.now().date()
        degisti = False
        
        if self.son_gunluk_reset < bugun:
            self.gunluk_puan = 0
            self.gunluk_cozulen = 0
            self.gunluk_dogru = 0
            self.gunluk_yanlis = 0
            self.son_gunluk_reset = bugun
            degisti = True
        
        haftanin_basi = bugun - timedelta(days=bugun.weekday())
        if self.son_haftalik_reset < haftanin_basi:
            self.haftalik_puan = 0
            self.haftalik_cozulen = 0
            self.haftalik_dogru = 0
            self.haftalik_yanlis = 0
            self.son_haftalik_reset = haftanin_basi
            self.hafta_baslangic = timezone.now()
            degisti = True
        
        ayin_basi = bugun.replace(day=1)
        if self.son_aylik_reset < ayin_basi: 
            self.aylik_puan = 0
            self.aylik_cozulen = 0
            self.aylik_dogru = 0
            self.aylik_yanlis = 0
            self.son_aylik_reset = ayin_basi
            degisti = True
        
        if degisti:
            self.save()
    
    @property
    def gunluk_siralama(self):
        """Günlük sıralamayı getir"""
        return OgrenciProfili.objects.filter(
            aktif_mi=True,
            gunluk_puan__gt=self.gunluk_puan
        ).count() + 1
    
    @property
    def haftalik_siralama(self):
        """Haftalık sıralamayı getir"""
        return OgrenciProfili.objects.filter(
            aktif_mi=True,
            haftalik_puan__gt=self.haftalik_puan
        ).count() + 1
    
    @property
    def aylik_siralama(self):
        """Aylık sıralamayı getir"""
        return OgrenciProfili.objects.filter(
            aktif_mi=True,
            aylik_puan__gt=self.aylik_puan
        ).count() + 1
    
    @property
    def genel_siralama(self):
        """Genel sıralamayı getir"""
        return OgrenciProfili.objects.filter(
            aktif_mi=True,
            toplam_puan__gt=self.toplam_puan
        ).count() + 1
    
    @property
    def genel_basari_orani(self):
        """Genel başarı oranını hesapla"""
        if self.cozulen_soru_sayisi > 0:
            return round((self.toplam_dogru / self.cozulen_soru_sayisi) * 100, 2)
        return 0
    
    @property
    def gunluk_basari_orani(self):
        """Günlük başarı oranını hesapla"""
        if self.gunluk_cozulen > 0:
            return round((self.gunluk_dogru / self.gunluk_cozulen) * 100, 2)
        return 0
    
    @property
    def haftalik_basari_orani(self):
        """Haftalık başarı oranını hesapla"""
        if self.haftalik_cozulen > 0:
            return round((self.haftalik_dogru / self.haftalik_cozulen) * 100, 2)
        return 0
    
    @property
    def aylik_basari_orani(self):
        """Aylık başarı oranını hesapla"""
        if self.aylik_cozulen > 0:
            return round((self.aylik_dogru / self.aylik_cozulen) * 100, 2)
        return 0
    
    def haftalik_sifirla(self):
        """ESKİ METOD - Artık reset_kontrolu() kullanılıyor"""
        self.reset_kontrolu()


class OyunModuIstatistik(models.Model):
    """Oyun Modu Bazlı İstatistikler (Karşılaşma, Bul Bakalım)"""
    
    OYUN_MODLARI = [
        ('karsilasma', 'Karşılaşma'),
        ('bul_bakalim', 'Bul Bakalım'),
    ]
    
    profil = models.ForeignKey(
        OgrenciProfili, 
        on_delete=models.CASCADE, 
        related_name='oyun_istatistikleri',
        verbose_name='Profil'
    )
    oyun_modu = models.CharField(
        max_length=20, 
        choices=OYUN_MODLARI, 
        db_index=True,
        verbose_name='Oyun Modu'
    )
    
    # İSTATİSTİKLER
    toplam_puan = models.IntegerField(
        default=0, 
        db_index=True,
        verbose_name='Toplam Puan'
    )
    oynanan_oyun_sayisi = models.IntegerField(
        default=0,
        verbose_name='Oynanan Oyun Sayısı'
    )
    kazanilan_oyun = models.IntegerField(
        default=0,
        verbose_name='Kazanılan Oyun'
    )
    kaybedilen_oyun = models.IntegerField(
        default=0,
        verbose_name='Kaybedilen Oyun'
    )
    cozulen_soru = models.IntegerField(
        default=0,
        verbose_name='Çözülen Soru'
    )
    dogru_sayisi = models.IntegerField(
        default=0,
        verbose_name='Doğru Sayısı'
    )
    yanlis_sayisi = models.IntegerField(
        default=0,
        verbose_name='Yanlış Sayısı'
    )
    
    # HAFTALIK
    haftalik_puan = models.IntegerField(
        default=0, 
        db_index=True,
        verbose_name='Haftalık Puan'
    )
    haftalik_oyun_sayisi = models.IntegerField(
        default=0,
        verbose_name='Haftalık Oyun Sayısı'
    )
    haftalik_dogru = models.IntegerField(
        default=0,
        verbose_name='Haftalık Doğru'
    )
    haftalik_yanlis = models.IntegerField(
        default=0,
        verbose_name='Haftalık Yanlış'
    )
    hafta_baslangic = models.DateTimeField(
        default=timezone.now,
        verbose_name='Hafta Başlangıç'
    )
    
    class Meta:
        verbose_name = 'Oyun Modu İstatistiği'
        verbose_name_plural = 'Oyun Modu İstatistikleri'
        unique_together = ['profil', 'oyun_modu']
        indexes = [
            models.Index(fields=['oyun_modu', '-toplam_puan'], name='oyun_mod_puan_idx'),
            models.Index(fields=['oyun_modu', '-haftalik_puan'], name='oyun_mod_haft_idx'),
        ]
    
    def __str__(self):
        return f"{self.profil.kullanici.username} - {self.get_oyun_modu_display()}"
    
    @property
    def basari_orani(self):
        """Başarı oranını hesapla"""
        if self.cozulen_soru > 0:
            return round((self.dogru_sayisi / self.cozulen_soru) * 100, 2)
        return 0
    
    @property
    def galibiyet_orani(self):
        """Galibiyet oranını hesapla"""
        if self.oynanan_oyun_sayisi > 0:
            return round((self.kazanilan_oyun / self.oynanan_oyun_sayisi) * 100, 2)
        return 0
    
    def haftalik_sifirla(self):
        """Haftalık istatistikleri sıfırla"""
        self.haftalik_puan = 0
        self.haftalik_oyun_sayisi = 0
        self.haftalik_dogru = 0
        self.haftalik_yanlis = 0
        self.hafta_baslangic = timezone.now()
        self.save(update_fields=[
            'haftalik_puan', 'haftalik_oyun_sayisi',
            'haftalik_dogru', 'haftalik_yanlis', 'hafta_baslangic'
        ])


class DersIstatistik(models.Model):
    """Ders Bazlı İstatistikler"""
    
    DERSLER = [
        ('matematik', 'Matematik'),
        ('fizik', 'Fizik'),
        ('kimya', 'Kimya'),
        ('biyoloji', 'Biyoloji'),
        ('turkce', 'Türkçe'),
        ('tarih', 'Tarih'),
        ('cografya', 'Coğrafya'),
        ('felsefe', 'Felsefe'),
        ('din', 'Din Kültürü'),
        ('ingilizce', 'İngilizce'),
    ]
    
    profil = models.ForeignKey(
        OgrenciProfili, 
        on_delete=models.CASCADE, 
        related_name='ders_istatistikleri',
        verbose_name='Profil'
    )
    ders = models.CharField(
        max_length=20, 
        choices=DERSLER, 
        db_index=True,
        verbose_name='Ders'
    )
    
    # GENEL İSTATİSTİKLER
    toplam_puan = models.IntegerField(
        default=0, 
        db_index=True,
        verbose_name='Toplam Puan'
    )
    cozulen_soru = models.IntegerField(
        default=0,
        verbose_name='Çözülen Soru'
    )
    dogru_sayisi = models.IntegerField(
        default=0, 
        db_index=True,
        verbose_name='Doğru Sayısı'
    )
    yanlis_sayisi = models.IntegerField(
        default=0,
        verbose_name='Yanlış Sayısı'
    )
    bos_sayisi = models.IntegerField(
        default=0,
        verbose_name='Boş Sayısı'
    )
    
    # HAFTALIK
    haftalik_puan = models.IntegerField(
        default=0,
        verbose_name='Haftalık Puan'
    )
    haftalik_cozulen = models.IntegerField(
        default=0,
        verbose_name='Haftalık Çözülen'
    )
    haftalik_dogru = models.IntegerField(
        default=0,
        verbose_name='Haftalık Doğru'
    )
    haftalik_yanlis = models.IntegerField(
        default=0,
        verbose_name='Haftalık Yanlış'
    )
    hafta_baslangic = models.DateTimeField(
        default=timezone.now,
        verbose_name='Hafta Başlangıç'
    )
    
    class Meta:
        verbose_name = 'Ders İstatistiği'
        verbose_name_plural = 'Ders İstatistikleri'
        unique_together = ['profil', 'ders']
        indexes = [
            models.Index(fields=['ders', '-dogru_sayisi'], name='ders_dogru_idx'),
            models.Index(fields=['ders', '-toplam_puan'], name='ders_puan_idx'),
        ]
    
    def __str__(self):
        return f"{self.profil.kullanici.username} - {self.get_ders_display()}"
    
    @property
    def net(self):
        """Net hesapla (Doğru - Yanlış/4)"""
        return round(self.dogru_sayisi - (self.yanlis_sayisi / 4), 2)
    
    @property
    def basari_orani(self):
        """Başarı oranını hesapla"""
        if self.cozulen_soru > 0:
            return round((self.dogru_sayisi / self.cozulen_soru) * 100, 2)
        return 0
    
    @property
    def haftalik_basari_orani(self):
        """Haftalık başarı oranını hesapla"""
        if self.haftalik_cozulen > 0:
            return round((self.haftalik_dogru / self.haftalik_cozulen) * 100, 2)
        return 0
    
    def haftalik_sifirla(self):
        """Haftalık istatistikleri sıfırla"""
        self.haftalik_puan = 0
        self.haftalik_cozulen = 0
        self.haftalik_dogru = 0
        self.haftalik_yanlis = 0
        self.hafta_baslangic = timezone.now()
        self.save(update_fields=[
            'haftalik_puan', 'haftalik_cozulen',
            'haftalik_dogru', 'haftalik_yanlis', 'hafta_baslangic'
        ])


class Rozet(models.Model):
    """Rozet Sistemi - 32 Kategori x 2 Seviye"""
    
    KATEGORI_SECENEKLERI = [
        # GENEL ROZETLER
        ('yeni_uye', 'Yeni Üye'),
        ('aktif_kullanici', 'Aktif Kullanıcı'),
        ('gun_asimi', 'Gün Aşımı'),
        ('hafta_sampionu', 'Hafta Şampiyonu'),
        
        # SORU ÇÖZME ROZETLER
        ('soru_cozucu', 'Soru Çözücü'),
        ('dogru_ustasi', 'Doğru Ustası'),
        ('net_avcisi', 'Net Avcısı'),
        ('hatasiz_kusursuz', 'Hatasız Kusursuz'),
        
        # DERS BAZLI ROZETLER
        ('matematik_dehasi', 'Matematik Dehası'),
        ('fizik_profesoru', 'Fizik Profesörü'),
        ('kimya_uzman', 'Kimya Uzmanı'),
        ('biyoloji_bilgini', 'Biyoloji Bilgini'),
        ('turkce_edebiyatci', 'Türkçe Edebiyatçısı'),
        ('tarih_bilgesi', 'Tarih Bilgesi'),
        ('cografya_gezgini', 'Coğrafya Gezgini'),
        ('felsefe_dusunuru', 'Felsefe Düşünürü'),
        
        # OYUN MODU ROZETLER
        ('karsilasma_savaslisi', 'Karşılaşma Savaşçısı'),
        ('bul_bakalim_ustasi', 'Bul Bakalım Ustası'),
        ('tabu_kral', 'Tabu Kralı'),
        ('galip_aslan', 'Galip Aslan'),
        
        # LİDERLİK ROZETLER
        ('lider_zirve', 'Lider Zirve'),
        ('top_10', 'Top 10'),
        ('top_50', 'Top 50'),
        ('zirve_fatih', 'Zirve Fatihi'),
        
        # ÖZEL BAŞARILAR
        ('hizli_cevap', 'Hızlı Cevap'),
        ('gece_kusu', 'Gece Kuşu'),
        ('sabah_kusagu', 'Sabah Kuşağı'),
        ('maraton_kosucu', 'Maraton Koşucusu'),
        
        # SOSYAL ROZETLER
        ('yardimci', 'Yardımcı'),
        ('ogretmen', 'Öğretmen'),
        ('ilham_verici', 'İlham Verici'),
        ('takım_oyuncusu', 'Takım Oyuncusu'),
    ]
    
    SEVIYE_SECENEKLERI = [
        ('caylak', 'Çaylak'),
        ('usta', 'Usta'),
    ]
    
    profil = models.ForeignKey(
        OgrenciProfili, 
        on_delete=models.CASCADE, 
        related_name='rozetler',
        verbose_name='Profil'
    )
    kategori = models.CharField(
        max_length=50, 
        choices=KATEGORI_SECENEKLERI, 
        db_index=True,
        verbose_name='Kategori'
    )
    seviye = models.CharField(
        max_length=20, 
        choices=SEVIYE_SECENEKLERI, 
        default='caylak',
        verbose_name='Seviye'
    )
    kazanilma_tarihi = models.DateTimeField(
        auto_now_add=True, 
        db_index=True,
        verbose_name='Kazanılma Tarihi'
    )
    
    class Meta: 
        verbose_name = 'Rozet'
        verbose_name_plural = 'Rozetler'
        unique_together = ['profil', 'kategori', 'seviye']
        ordering = ['-kazanilma_tarihi']
        indexes = [
            models.Index(fields=['profil', '-kazanilma_tarihi'], name='rozet_profil_idx'),
        ]
    
    def __str__(self):
        return f"{self.profil.kullanici.username} - {self.get_kategori_display()} ({self.get_seviye_display()})"
    
    @property
    def aciklama(self):
        """Rozet açıklamasını getir"""
        return rozet_aciklama.ROZET_ACIKLAMALARI.get(
            self.kategori, {}
        ).get(self.seviye, "Açıklama bulunamadı.")
    
    @property
    def icon(self):
        """Rozet ikonu döndür"""
        icons = {
            'yeni_uye': '🌱',
            'aktif_kullanici': '⚡',
            'gun_asimi': '📅',
            'hafta_sampionu': '👑',
            'soru_cozucu': '📝',
            'dogru_ustasi': '✅',
            'net_avcisi': '🎯',
            'hatasiz_kusursuz': '💯',
            'matematik_dehasi': '🔢',
            'fizik_profesoru': '⚛️',
            'kimya_uzman': '🧪',
            'biyoloji_bilgini': '🧬',
            'turkce_edebiyatci': '📖',
            'tarih_bilgesi': '🏛️',
            'cografya_gezgini': '🌍',
            'felsefe_dusunuru': '💭',
            'karsilasma_savaslisi': '⚔️',
            'bul_bakalim_ustasi': '💡',
            'tabu_kral': '🎭',
            'galip_aslan': '🦁',
            'lider_zirve': '🏆',
            'top_10': '🥇',
            'top_50': '🥈',
            'zirve_fatih': '👑',
            'hizli_cevap': '⚡',
            'gece_kusu': '🦉',
            'sabah_kusagu': '🌅',
            'maraton_kosucu': '🏃',
            'yardimci': '🤝',
            'ogretmen': '👨‍🏫',
            'ilham_verici': '✨',
            'takım_oyuncusu': '👥',
        }
        return icons.get(self.kategori, '🏅')
    
    @property
    def renk(self):
        """Rozet rengini döndür"""
        if self.seviye == 'caylak': 
            return '#6c757d'  # Gri
        else:
            return '#ffd700'  # Altın


class KonuIstatistik(models.Model):
    """Konu Bazlı İstatistikler"""
    
    profil = models.ForeignKey(
        OgrenciProfili, 
        on_delete=models.CASCADE,
        related_name='konu_istatistikleri',
        verbose_name='Profil'
    )
    ders = models.CharField(
        max_length=50, 
        db_index=True,
        verbose_name='Ders'
    )
    konu = models.CharField(
        max_length=100,
        verbose_name='Konu'
    )
    dogru_sayisi = models.IntegerField(
        default=0,
        verbose_name='Doğru Sayısı'
    )
    yanlis_sayisi = models.IntegerField(
        default=0,
        verbose_name='Yanlış Sayısı'
    )
    bos_sayisi = models.IntegerField(
        default=0,
        verbose_name='Boş Sayısı'
    )
    toplam_soru = models.IntegerField(
        default=0,
        verbose_name='Toplam Soru'
    )

    class Meta:
        verbose_name = 'Konu İstatistiği'
        verbose_name_plural = 'Konu İstatistikleri'
        unique_together = ['profil', 'ders', 'konu']
        indexes = [
            models.Index(fields=['profil', 'ders'], name='konu_ist_idx'),
        ]
    
    def __str__(self):
        return f"{self.profil.kullanici.username} - {self.ders} - {self.konu}"
    
    def basari_orani(self):
        """Başarı oranını hesapla"""
        if self.toplam_soru == 0:
            return 0
        return round(100 * self.dogru_sayisi / self.toplam_soru, 1)


class RozetKosul(models.Model):
    """Rozet Kazanma Koşulları"""
    
    kategori = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='Kategori'
    )
    seviye = models.CharField(
        max_length=20,
        verbose_name='Seviye'
    )
    
    # KOŞULLAR
    gerekli_soru_sayisi = models.IntegerField(
        default=0, 
        help_text="Çözülmesi gereken soru sayısı",
        verbose_name='Gerekli Soru Sayısı'
    )
    gerekli_dogru_sayisi = models.IntegerField(
        default=0, 
        help_text="Yapılması gereken doğru sayısı",
        verbose_name='Gerekli Doğru Sayısı'
    )
    gerekli_puan = models.IntegerField(
        default=0, 
        help_text="Kazanılması gereken puan",
        verbose_name='Gerekli Puan'
    )
    gerekli_oyun_sayisi = models.IntegerField(
        default=0, 
        help_text="Oynanması gereken oyun sayısı",
        verbose_name='Gerekli Oyun Sayısı'
    )
    gerekli_galibiyet = models.IntegerField(
        default=0, 
        help_text="Kazanılması gereken oyun sayısı",
        verbose_name='Gerekli Galibiyet'
    )
    gerekli_gun_sayisi = models.IntegerField(
        default=0, 
        help_text="Aktif olunması gereken gün sayısı",
        verbose_name='Gerekli Gün Sayısı'
    )
    gerekli_basari_orani = models.FloatField(
        default=0, 
        help_text="Başarı oranı (0-100)",
        verbose_name='Gerekli Başarı Oranı'
    )
    
    # ÖZEL KOŞULLAR
    ozel_kosul = models.TextField(
        blank=True, 
        help_text="Özel koşul açıklaması",
        verbose_name='Özel Koşul'
    )
    aciklama = models.TextField(
        help_text="Rozet açıklaması",
        verbose_name='Açıklama'
    )
    
    class Meta:
        verbose_name = 'Rozet Koşulu'
        verbose_name_plural = 'Rozet Koşulları'
        ordering = ['kategori', 'seviye']
    
    def __str__(self):
        return f"{self.kategori} ({self.seviye})"