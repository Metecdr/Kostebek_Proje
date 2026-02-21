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
    
    # YENİ SEVİYE SİSTEMİ ALANLARI
    xp = models.IntegerField(
        default=0,
        verbose_name='Deneyim Puanı (XP)',
        help_text='Toplam kazanılan XP'
    )
    seviye = models.IntegerField(
        default=1,
        verbose_name='Seviye',
        help_text='Kullanıcının mevcut seviyesi'
    )

        # ==================== GÜNLÜK GİRİŞ ALANLARI ====================
    son_giris_tarihi = models.DateField(
        null=True,
        blank=True,
        verbose_name='Son Giriş Tarihi',
        help_text='Kullanıcının son giriş yaptığı tarih'
    )
    ardasik_gun_sayisi = models.IntegerField(
        default=0,
        verbose_name='Ardışık Gün Sayısı (Streak)',
        help_text='Kaç gündür üst üste giriş yapıyor'
    )
    en_uzun_streak = models.IntegerField(
        default=0,
        verbose_name='En Uzun Streak',
        help_text='Şimdiye kadarki en uzun ardışık gün sayısı'
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

    def xp_ekle(self, miktar):
        """XP ekle ve seviye kontrolü yap"""
        self.xp += miktar
        eski_seviye = self.seviye
        yeni_seviye = self.seviye_hesapla()
        
        if yeni_seviye > eski_seviye:
            self.seviye = yeni_seviye
            self.save()
            return {
                'seviye_atlandi': True,
                'eski_seviye': eski_seviye,
                'yeni_seviye': yeni_seviye,
                'unvan': self.seviye_unvani()
            }
        else:
            self.save()
            return {'seviye_atlandi': False}
    
    def seviye_hesapla(self):
        """XP'ye göre seviye hesapla"""
        if self.xp < 100:
            return 1
        elif self.xp < 250:
            return 2
        elif self.xp < 500:
            return 3
        elif self.xp < 1000:
            return 4
        elif self.xp < 1500:
            return 5
        elif self.xp < 2500:
            return 6
        elif self.xp < 4000:
            return 7
        elif self.xp < 6000:
            return 8
        elif self.xp < 8500:
            return 9
        elif self.xp < 12000:
            return 10
        elif self.xp < 16000:
            return 11
        elif self.xp < 20000:
            return 12
        elif self.xp < 25000:
            return 13
        elif self.xp < 30000:
            return 14
        elif self.xp < 40000:
            return 15
        elif self.xp < 50000:
            return 16
        elif self.xp < 65000:
            return 17
        elif self.xp < 80000:
            return 18
        elif self.xp < 100000:
            return 19
        else:
            return 20
    
    def seviye_unvani(self):
        """Seviyeye göre unvan döndür"""
        unvanlar = {
            1: '🐣 Çaylak',
            2: '🌱 Acemi',
            3: '⚡ Hızlı Başlangıç',
            4: '🔥 Ateşli',
            5: '💪 Güçlü',
            6: '🎯 Hedef Odaklı',
            7: '🚀 Roket',
            8: '⭐ Yıldız',
            9: '💎 Elmas',
            10: '🏆 Usta',
            11: '👑 Kral Adayı',
            12: '🦅 Kartal',
            13: '🔱 Gladyatör',
            14: '⚔️ Savaşçı',
            15: '👑 Kral',
            16: '🌟 Süper Yıldız',
            17: '🏅 Şampiyon',
            18: '💫 Efsane Adayı',
            19: '🌠 Efsane',
            20: '🔥 Tanrı',
        }
        return unvanlar.get(self.seviye, '🐣 Çaylak')
    
    def sonraki_seviye_xp(self):
        """Sonraki seviye için gereken XP"""
        xp_gereksinimleri = {
            1: 100, 2: 250, 3: 500, 4: 1000, 5: 1500,
            6: 2500, 7: 4000, 8: 6000, 9: 8500, 10: 12000,
            11: 16000, 12: 20000, 13: 25000, 14: 30000, 15: 40000,
            16: 50000, 17: 65000, 18: 80000, 19: 100000, 20: 999999
        }
        return xp_gereksinimleri.get(self.seviye, 999999)
    
    def xp_yuzdesi(self):
        """Mevcut seviyedeki XP yüzdesi"""
        if self.seviye == 1:
            onceki_seviye_xp = 0
        else:
            onceki_seviye_xp_dict = {
                2: 100, 3: 250, 4: 500, 5: 1000, 6: 1500,
                7: 2500, 8: 4000, 9: 6000, 10: 8500, 11: 12000,
                12: 16000, 13: 20000, 14: 25000, 15: 30000, 16: 40000,
                17: 50000, 18: 65000, 19: 80000, 20: 100000
            }
            onceki_seviye_xp = onceki_seviye_xp_dict.get(self.seviye, 0)
        
        sonraki_xp = self.sonraki_seviye_xp()
        mevcut_xp = self.xp - onceki_seviye_xp
        gereken_xp = sonraki_xp - onceki_seviye_xp
        
        if gereken_xp == 0:
            return 100
        
        yuzde = (mevcut_xp / gereken_xp) * 100
        return min(100, max(0, yuzde))

def gunluk_giris_kontrol(self):
    """
    Günlük giriş kontrolü ve bonus verme
    
    Returns:
        dict: Bonus bilgileri
    """
    from django.utils import timezone
    
    bugun = timezone.now().date()
    
    # İlk giriş
    if not self.son_giris_tarihi:
        self.son_giris_tarihi = bugun
        self.ardasik_gun_sayisi = 1
        self.save()
        return {
            'ilk_giris':  True,
            'bonus_verildi': True,
            'streak':  1,
            'bonus_xp': 20
        }
    
    # Bugün zaten giriş yapılmış
    if self.son_giris_tarihi == bugun:
        return {
            'ilk_giris': False,
            'bonus_verildi': False,
            'streak': self.ardasik_gun_sayisi,
            'bonus_xp':  0,
            'mesaj': 'Bugün zaten giriş yaptın!'
        }
    
    # Dün giriş yapılmış (streak devam ediyor)
    dun = bugun - timezone.timedelta(days=1)
    if self.son_giris_tarihi == dun:
        self.ardasik_gun_sayisi += 1
        self.son_giris_tarihi = bugun
        
        # En uzun streak güncelle
        if self.ardasik_gun_sayisi > self.en_uzun_streak: 
            self.en_uzun_streak = self.ardasik_gun_sayisi
        
        self.save()
        
        # Bonus XP hesapla (streak'e göre artan)
        bonus_xp = 20 + min(self.ardasik_gun_sayisi * 2, 50)  # Max 70 XP
        
        return {
            'ilk_giris': False,
            'bonus_verildi': True,
            'streak': self.ardasik_gun_sayisi,
            'bonus_xp': bonus_xp,
            'streak_devam': True
        }
    
    # Streak koptu
    else:
        eski_streak = self.ardasik_gun_sayisi  # ✅ ÖNCEKİ STREAK'İ KAYDET
        self.ardasik_gun_sayisi = 1
        self.son_giris_tarihi = bugun
        self.save()
        
        return {
            'ilk_giris': False,
            'bonus_verildi': True,
            'streak': 1,
            'bonus_xp': 20,
            'streak_koptu': True,
            'eski_streak': eski_streak  # ✅ DÜZELTİLDİ
        }
    
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


class Bildirim(models.Model):
    """Kullanıcı Bildirimleri"""
    
    BILDIRIM_TIPLERI = [
        ('rozet', 'Yeni Rozet'),
        ('liderlik', 'Liderlik Değişimi'),
        ('seviye', 'Seviye Atlama'),
        ('basari', 'Özel Başarı'),
        ('sistem', 'Sistem Bildirimi'),
    ]
    
    kullanici = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bildirimler',
        verbose_name='Kullanıcı'
    )
    tip = models.CharField(
        max_length=20,
        choices=BILDIRIM_TIPLERI,
        default='sistem',
        verbose_name='Bildirim Tipi'
    )
    baslik = models.CharField(
        max_length=100,
        verbose_name='Başlık'
    )
    mesaj = models.TextField(
        verbose_name='Mesaj'
    )
    icon = models.CharField(
        max_length=10,
        default='🔔',
        verbose_name='İkon'
    )
    okundu_mu = models.BooleanField(
        default=False,
        verbose_name='Okundu mu'
    )
    iliskili_rozet = models.ForeignKey(
        'Rozet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='İlişkili Rozet'
    )
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Oluşturma Tarihi'
    )
    
    class Meta:
        verbose_name = 'Bildirim'
        verbose_name_plural = 'Bildirimler'
        ordering = ['-olusturma_tarihi']
        indexes = [
            models.Index(fields=['kullanici', '-olusturma_tarihi'], name='bildirim_kullanici_idx'),
            models.Index(fields=['okundu_mu'], name='bildirim_okundu_idx'),
        ]
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.baslik}"
    
    @property
    def renk(self):
        """Bildirim tipine göre renk"""
        renkler = {
            'rozet': '#FFD700',
            'liderlik': '#FF6B6B',
            'seviye': '#4ECDC4',
            'basari':  '#95E1D3',
            'sistem': '#6C757D',
        }
        return renkler.get(self.tip, '#6C757D')

class Arkadaslik(models.Model):
    """Arkadaşlık İstekleri ve Bağlantılar"""
    
    DURUM_SECENEKLERI = [
        ('beklemede', 'Beklemede'),
        ('kabul_edildi', 'Kabul Edildi'),
        ('reddedildi', 'Reddedildi'),
    ]
    
    gonderen = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='gonderilen_arkadaslik_istekleri',
        verbose_name='Gönderen'
    )
    alan = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='alinan_arkadaslik_istekleri',
        verbose_name='Alan'
    )
    durum = models.CharField(
        max_length=20,
        choices=DURUM_SECENEKLERI,
        default='beklemede',
        verbose_name='Durum'
    )
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Oluşturma Tarihi'
    )
    guncelleme_tarihi = models.DateTimeField(
        auto_now=True,
        verbose_name='Güncellenme Tarihi'
    )
    
    class Meta:
        verbose_name = 'Arkadaşlık'
        verbose_name_plural = 'Arkadaşlıklar'
        ordering = ['-olusturma_tarihi']
        unique_together = ['gonderen', 'alan']
        indexes = [
            models.Index(fields=['gonderen', 'durum'], name='arkadaslik_gonderen_idx'),
            models.Index(fields=['alan', 'durum'], name='arkadaslik_alan_idx'),
        ]
    
    def __str__(self):
        return f"{self.gonderen.username} → {self.alan.username} ({self.get_durum_display()})"
    
    @classmethod
    def arkadaslar_mi(cls, kullanici1, kullanici2):
        """İki kullanıcı arkadaş mı?"""
        return cls.objects.filter(
            models.Q(gonderen=kullanici1, alan=kullanici2) | 
            models.Q(gonderen=kullanici2, alan=kullanici1),
            durum='kabul_edildi'
        ).exists()
    
    @classmethod
    def arkadaslari_getir(cls, kullanici):
        """Kullanıcının tüm arkadaşlarını getir"""
        gonderilen = cls.objects.filter(
            gonderen=kullanici, 
            durum='kabul_edildi'
        ).select_related('alan', 'alan__profil')
        
        alinan = cls.objects.filter(
            alan=kullanici,
            durum='kabul_edildi'
        ).select_related('gonderen', 'gonderen__profil')
        
        arkadaslar = []
        for istek in gonderilen:
            arkadaslar.append(istek.alan)
        for istek in alinan:
            arkadaslar.append(istek.gonderen)
        
        return arkadaslar
    
    @classmethod
    def bekleyen_istekler(cls, kullanici):
        """Kullanıcının bekleyen istekleri"""
        return cls.objects.filter(
            alan=kullanici,
            durum='beklemede'
        ).select_related('gonderen', 'gonderen__profil')