from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import profile.rozet_aciklama as rozet_aciklama

class OgrenciProfili(models.Model):
    ALAN_SECENEKLERI = [
        ('sayisal', 'Sayısal'),
        ('sozel', 'Sözel'),
        ('esit_agirlik', 'Eşit Ağırlık'),
        ('dil', 'Dil'),
    ]
    
    # TEMEL BİLGİLER
    kullanici = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    alan = models.CharField(max_length=20, choices=ALAN_SECENEKLERI, default='sayisal')
    profil_fotografi = models.ImageField(upload_to='profil_fotograflari/', null=True, blank=True)
    
    # GENEL İSTATİSTİKLER
    toplam_puan = models.IntegerField(default=0)
    cozulen_soru_sayisi = models.IntegerField(default=0)
    toplam_dogru = models.IntegerField(default=0)
    toplam_yanlis = models.IntegerField(default=0)
    
    # HAFTALIK İSTATİSTİKLER
    haftalik_puan = models.IntegerField(default=0)
    haftalik_cozulen = models.IntegerField(default=0)
    haftalik_dogru = models.IntegerField(default=0)
    haftalik_yanlis = models.IntegerField(default=0)
    hafta_baslangic = models.DateTimeField(default=timezone.now)
    
    # ROZET SİSTEMİ
    unvanlar = models.CharField(max_length=255, default='Çaylak')
    
    # TARİH BİLGİLERİ
    kayit_tarihi = models.DateTimeField(auto_now_add=True)
    son_giris = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.kullanici.username
    
    @property
    def genel_basari_orani(self):
        if self.cozulen_soru_sayisi > 0:
            return round((self.toplam_dogru / self.cozulen_soru_sayisi) * 100, 2)
        return 0
    
    @property
    def haftalik_basari_orani(self):
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
        self.save()
    
    class Meta:
        verbose_name = 'Öğrenci Profili'
        verbose_name_plural = 'Öğrenci Profilleri'
        ordering = ['-toplam_puan']


class OyunModuIstatistik(models.Model):
    """Oyun Modu Bazlı İstatistikler (Karşılaşma, Bul Bakalım)"""
    
    OYUN_MODLARI = [
        ('karsilasma', 'Karşılaşma'),
        ('bul_bakalim', 'Bul Bakalım'),
    ]
    
    profil = models.ForeignKey(OgrenciProfili, on_delete=models.CASCADE, related_name='oyun_istatistikleri')
    oyun_modu = models.CharField(max_length=20, choices=OYUN_MODLARI)
    
    # İSTATİSTİKLER
    toplam_puan = models.IntegerField(default=0)
    oynanan_oyun_sayisi = models.IntegerField(default=0)
    kazanilan_oyun = models.IntegerField(default=0)
    kaybedilen_oyun = models.IntegerField(default=0)
    cozulen_soru = models.IntegerField(default=0)
    dogru_sayisi = models.IntegerField(default=0)
    yanlis_sayisi = models.IntegerField(default=0)
    
    # HAFTALIK
    haftalik_puan = models.IntegerField(default=0)
    haftalik_oyun_sayisi = models.IntegerField(default=0)
    haftalik_dogru = models.IntegerField(default=0)
    haftalik_yanlis = models.IntegerField(default=0)
    hafta_baslangic = models.DateTimeField(default=timezone.now)
    
    @property
    def basari_orani(self):
        if self.cozulen_soru > 0:
            return round((self.dogru_sayisi / self.cozulen_soru) * 100, 2)
        return 0
    
    @property
    def galibiyet_orani(self):
        if self.oynanan_oyun_sayisi > 0:
            return round((self.kazanilan_oyun / self.oynanan_oyun_sayisi) * 100, 2)
        return 0
    
    def haftalik_sifirla(self):
        self.haftalik_puan = 0
        self.haftalik_oyun_sayisi = 0
        self.haftalik_dogru = 0
        self.haftalik_yanlis = 0
        self.hafta_baslangic = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = 'Oyun Modu İstatistiği'
        verbose_name_plural = 'Oyun Modu İstatistikleri'
        unique_together = ['profil', 'oyun_modu']
    
    def __str__(self):
        return f"{self.profil.kullanici.username} - {self.get_oyun_modu_display()}"


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
    
    profil = models.ForeignKey(OgrenciProfili, on_delete=models.CASCADE, related_name='ders_istatistikleri')
    ders = models.CharField(max_length=20, choices=DERSLER)
    
    # GENEL İSTATİSTİKLER
    toplam_puan = models.IntegerField(default=0)
    cozulen_soru = models.IntegerField(default=0)
    dogru_sayisi = models.IntegerField(default=0)
    yanlis_sayisi = models.IntegerField(default=0)
    bos_sayisi = models.IntegerField(default=0)
    
    # HAFTALIK
    haftalik_puan = models.IntegerField(default=0)
    haftalik_cozulen = models.IntegerField(default=0)
    haftalik_dogru = models.IntegerField(default=0)
    haftalik_yanlis = models.IntegerField(default=0)
    hafta_baslangic = models.DateTimeField(default=timezone.now)
    
    # NET HESAPLAMA
    @property
    def net(self):
        return self.dogru_sayisi - (self.yanlis_sayisi / 4)
    
    @property
    def basari_orani(self):
        if self.cozulen_soru > 0:
            return round((self.dogru_sayisi / self.cozulen_soru) * 100, 2)
        return 0
    
    @property
    def haftalik_basari_orani(self):
        if self.haftalik_cozulen > 0:
            return round((self.haftalik_dogru / self.haftalik_cozulen) * 100, 2)
        return 0
    
    def haftalik_sifirla(self):
        self.haftalik_puan = 0
        self.haftalik_cozulen = 0
        self.haftalik_dogru = 0
        self.haftalik_yanlis = 0
        self.hafta_baslangic = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = 'Ders İstatistiği'
        verbose_name_plural = 'Ders İstatistikleri'
        unique_together = ['profil', 'ders']
    
    def __str__(self):
        return f"{self.profil.kullanici.username} - {self.get_ders_display()}"

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
    
    @property
    def aciklama(self):
        """Rozet açıklamasını getir"""
        return rozet_aciklama.ROZET_ACIKLAMALARI.get(self.kategori, {}).get(self.seviye, "Açıklama bulunamadı.")

    profil = models.ForeignKey(OgrenciProfili, on_delete=models.CASCADE, related_name='rozetler')
    kategori = models.CharField(max_length=50, choices=KATEGORI_SECENEKLERI)
    seviye = models.CharField(max_length=20, choices=SEVIYE_SECENEKLERI, default='caylak')
    kazanilma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Rozet'
        verbose_name_plural = 'Rozetler'
        unique_together = ['profil', 'kategori', 'seviye']
        ordering = ['-kazanilma_tarihi']
    
    def __str__(self):
        return f"{self.profil.kullanici.username} - {self.get_kategori_display()} ({self.get_seviye_display()})"
    
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


class RozetKosul(models.Model):
    """Rozet Kazanma Koşulları"""
    
    kategori = models.CharField(max_length=50, unique=True)
    seviye = models.CharField(max_length=20)
    
    # KOŞULLAR
    gerekli_soru_sayisi = models.IntegerField(default=0, help_text="Çözülmesi gereken soru sayısı")
    gerekli_dogru_sayisi = models.IntegerField(default=0, help_text="Yapılması gereken doğru sayısı")
    gerekli_puan = models.IntegerField(default=0, help_text="Kazanılması gereken puan")
    gerekli_oyun_sayisi = models.IntegerField(default=0, help_text="Oynanması gereken oyun sayısı")
    gerekli_galibiyet = models.IntegerField(default=0, help_text="Kazanılması gereken oyun sayısı")
    gerekli_gun_sayisi = models.IntegerField(default=0, help_text="Aktif olunması gereken gün sayısı")
    gerekli_basari_orani = models.FloatField(default=0, help_text="Başarı oranı (0-100)")
    
    # ÖZEL KOŞULLAR
    ozel_kosul = models.TextField(blank=True, help_text="Özel koşul açıklaması")
    
    aciklama = models.TextField(help_text="Rozet açıklaması")
    
    class Meta:
        verbose_name = 'Rozet Koşulu'
        verbose_name_plural = 'Rozet Koşulları'
    
    def __str__(self):
        return f"{self.kategori} ({self.seviye})"

class OgrenciProfili(models.Model):
    ALAN_SECENEKLERI = [
        ('sayisal', 'Sayısal'),
        ('sozel', 'Sözel'),
        ('esit_agirlik', 'Eşit Ağırlık'),
        ('dil', 'Dil'),
    ]
    
    # TEMEL BİLGİLER
    kullanici = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    alan = models.CharField(max_length=20, choices=ALAN_SECENEKLERI, default='sayisal')
    profil_fotografi = models.ImageField(upload_to='profil_fotograflari/', null=True, blank=True)
    
    # GENEL İSTATİSTİKLER
    toplam_puan = models.IntegerField(default=0)
    cozulen_soru_sayisi = models.IntegerField(default=0)
    toplam_dogru = models.IntegerField(default=0)
    toplam_yanlis = models.IntegerField(default=0)
    
    # HAFTALIK İSTATİSTİKLER
    haftalik_puan = models.IntegerField(default=0)
    haftalik_cozulen = models.IntegerField(default=0)
    haftalik_dogru = models.IntegerField(default=0)
    haftalik_yanlis = models.IntegerField(default=0)
    hafta_baslangic = models.DateTimeField(default=timezone.now)
    
    # ROZET SİSTEMİ
    unvanlar = models.CharField(max_length=255, default='Çaylak')
    
    # TARİH BİLGİLERİ
    kayit_tarihi = models.DateTimeField(auto_now_add=True)
    son_giris = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.kullanici.username
    
    @property
    def genel_basari_orani(self):
        if self.cozulen_soru_sayisi > 0:
            return round((self.toplam_dogru / self.cozulen_soru_sayisi) * 100, 2)
        return 0
    
    @property
    def haftalik_basari_orani(self):
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
        self.save()
    
    class Meta:
        verbose_name = 'Öğrenci Profili'
        verbose_name_plural = 'Öğrenci Profilleri'
        ordering = ['-toplam_puan']


class OyunModuIstatistik(models.Model):
    """Oyun Modu Bazlı İstatistikler (Karşılaşma, Bul Bakalım)"""
    
    OYUN_MODLARI = [
        ('karsilasma', 'Karşılaşma'),
        ('bul_bakalim', 'Bul Bakalım'),
    ]
    
    profil = models.ForeignKey(OgrenciProfili, on_delete=models.CASCADE, related_name='oyun_istatistikleri')
    oyun_modu = models.CharField(max_length=20, choices=OYUN_MODLARI)
    
    # İSTATİSTİKLER
    toplam_puan = models.IntegerField(default=0)
    oynanan_oyun_sayisi = models.IntegerField(default=0)
    kazanilan_oyun = models.IntegerField(default=0)
    kaybedilen_oyun = models.IntegerField(default=0)
    cozulen_soru = models.IntegerField(default=0)
    dogru_sayisi = models.IntegerField(default=0)
    yanlis_sayisi = models.IntegerField(default=0)
    
    # HAFTALIK
    haftalik_puan = models.IntegerField(default=0)
    haftalik_oyun_sayisi = models.IntegerField(default=0)
    haftalik_dogru = models.IntegerField(default=0)
    haftalik_yanlis = models.IntegerField(default=0)
    hafta_baslangic = models.DateTimeField(default=timezone.now)
    
    @property
    def basari_orani(self):
        if self.cozulen_soru > 0:
            return round((self.dogru_sayisi / self.cozulen_soru) * 100, 2)
        return 0
    
    @property
    def galibiyet_orani(self):
        if self.oynanan_oyun_sayisi > 0:
            return round((self.kazanilan_oyun / self.oynanan_oyun_sayisi) * 100, 2)
        return 0
    
    def haftalik_sifirla(self):
        self.haftalik_puan = 0
        self.haftalik_oyun_sayisi = 0
        self.haftalik_dogru = 0
        self.haftalik_yanlis = 0
        self.hafta_baslangic = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = 'Oyun Modu İstatistiği'
        verbose_name_plural = 'Oyun Modu İstatistikleri'
        unique_together = ['profil', 'oyun_modu']
    
    def __str__(self):
        return f"{self.profil.kullanici.username} - {self.get_oyun_modu_display()}"


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
    
    profil = models.ForeignKey(OgrenciProfili, on_delete=models.CASCADE, related_name='ders_istatistikleri')
    ders = models.CharField(max_length=20, choices=DERSLER)
    
    # GENEL İSTATİSTİKLER
    toplam_puan = models.IntegerField(default=0)
    cozulen_soru = models.IntegerField(default=0)
    dogru_sayisi = models.IntegerField(default=0)
    yanlis_sayisi = models.IntegerField(default=0)
    bos_sayisi = models.IntegerField(default=0)
    
    # HAFTALIK
    haftalik_puan = models.IntegerField(default=0)
    haftalik_cozulen = models.IntegerField(default=0)
    haftalik_dogru = models.IntegerField(default=0)
    haftalik_yanlis = models.IntegerField(default=0)
    hafta_baslangic = models.DateTimeField(default=timezone.now)
    
    # NET HESAPLAMA
    @property
    def net(self):
        return self.dogru_sayisi - (self.yanlis_sayisi / 4)
    
    @property
    def basari_orani(self):
        if self.cozulen_soru > 0:
            return round((self.dogru_sayisi / self.cozulen_soru) * 100, 2)
        return 0
    
    @property
    def haftalik_basari_orani(self):
        if self.haftalik_cozulen > 0:
            return round((self.haftalik_dogru / self.haftalik_cozulen) * 100, 2)
        return 0
    
    def haftalik_sifirla(self):
        self.haftalik_puan = 0
        self.haftalik_cozulen = 0
        self.haftalik_dogru = 0
        self.haftalik_yanlis = 0
        self.hafta_baslangic = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = 'Ders İstatistiği'
        verbose_name_plural = 'Ders İstatistikleri'
        unique_together = ['profil', 'ders']
    
    def __str__(self):
        return f"{self.profil.kullanici.username} - {self.get_ders_display()}"

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
    
    profil = models.ForeignKey(OgrenciProfili, on_delete=models.CASCADE, related_name='rozetler')
    kategori = models.CharField(max_length=50, choices=KATEGORI_SECENEKLERI)
    seviye = models.CharField(max_length=20, choices=SEVIYE_SECENEKLERI, default='caylak')
    kazanilma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Rozet'
        verbose_name_plural = 'Rozetler'
        unique_together = ['profil', 'kategori', 'seviye']
        ordering = ['-kazanilma_tarihi']
    
    def __str__(self):
        return f"{self.profil.kullanici.username} - {self.get_kategori_display()} ({self.get_seviye_display()})"
    
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


class RozetKosul(models.Model):
    """Rozet Kazanma Koşulları"""
    
    kategori = models.CharField(max_length=50, unique=True)
    seviye = models.CharField(max_length=20)
    
    # KOŞULLAR
    gerekli_soru_sayisi = models.IntegerField(default=0, help_text="Çözülmesi gereken soru sayısı")
    gerekli_dogru_sayisi = models.IntegerField(default=0, help_text="Yapılması gereken doğru sayısı")
    gerekli_puan = models.IntegerField(default=0, help_text="Kazanılması gereken puan")
    gerekli_oyun_sayisi = models.IntegerField(default=0, help_text="Oynanması gereken oyun sayısı")
    gerekli_galibiyet = models.IntegerField(default=0, help_text="Kazanılması gereken oyun sayısı")
    gerekli_gun_sayisi = models.IntegerField(default=0, help_text="Aktif olunması gereken gün sayısı")
    gerekli_basari_orani = models.FloatField(default=0, help_text="Başarı oranı (0-100)")
    
    # ÖZEL KOŞULLAR
    ozel_kosul = models.TextField(blank=True, help_text="Özel koşul açıklaması")
    
    aciklama = models.TextField(help_text="Rozet açıklaması")
    
    class Meta:
        verbose_name = 'Rozet Koşulu'
        verbose_name_plural = 'Rozet Koşulları'
    
    def __str__(self):
        return f"{self.kategori} ({self.seviye})"

class KonuIstatistik(models.Model):
    profil = models.ForeignKey(OgrenciProfili, on_delete=models.CASCADE)
    ders = models.CharField(max_length=50)
    konu = models.CharField(max_length=100)
    dogru_sayisi = models.IntegerField(default=0)
    yanlis_sayisi = models.IntegerField(default=0)
    bos_sayisi = models.IntegerField(default=0)
    toplam_soru = models.IntegerField(default=0)

    def basari_orani(self):
        if self.toplam_soru == 0:
            return 0
        return round(100 * self.dogru_sayisi / self.toplam_soru, 1)

    class Meta:
        unique_together = ['profil', 'ders', 'konu']