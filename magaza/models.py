from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class MagazaUrun(models.Model):
    """Mağaza Ürünleri"""

    KATEGORI_SECENEKLERI = [
        ('unvan', 'Unvan'),
        ('cerceve', 'Profil Çerçevesi'),
        ('tema', 'Tema'),
        ('avatar', 'Avatar'),
    ]

    isim = models.CharField(max_length=100, verbose_name='Ürün Adı')
    aciklama = models.TextField(verbose_name='Açıklama')
    kategori = models.CharField(max_length=20, choices=KATEGORI_SECENEKLERI, verbose_name='Kategori')
    fiyat = models.IntegerField(verbose_name='Fiyat (Puan)')
    icon = models.CharField(max_length=10, default='🎁', verbose_name='İkon')

    # Unvan için
    unvan_metni = models.CharField(max_length=50, null=True, blank=True, verbose_name='Unvan Metni')
    unvan_renk = models.CharField(max_length=20, default='#667eea', verbose_name='Unvan Rengi')

    # Çerçeve için
    cerceve_css = models.CharField(max_length=500, null=True, blank=True, verbose_name='Çerçeve CSS')
    cerceve_renk = models.CharField(max_length=200, null=True, blank=True, verbose_name='Çerçeve Rengi')

    # Tema için
    tema_primary = models.CharField(max_length=20, null=True, blank=True, verbose_name='Ana Renk')
    tema_secondary = models.CharField(max_length=20, null=True, blank=True, verbose_name='İkincil Renk')

    # Avatar için
    avatar_emoji = models.CharField(max_length=10, null=True, blank=True, verbose_name='Avatar Emoji')

    aktif = models.BooleanField(default=True, verbose_name='Aktif')
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mağaza Ürünü'
        verbose_name_plural = 'Mağaza Ürünleri'
        ordering = ['kategori', 'fiyat']

    def __str__(self):
        return f"{self.icon} {self.isim} ({self.fiyat} puan)"


class SatinAlma(models.Model):
    """Satın Alma Geçmişi"""

    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='satin_almalar')
    urun = models.ForeignKey(MagazaUrun, on_delete=models.CASCADE, related_name='satin_almalar')
    odenen_puan = models.IntegerField(verbose_name='Ödenen Puan')
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Satın Alma'
        verbose_name_plural = 'Satın Almalar'
        ordering = ['-tarih']
        unique_together = ['kullanici', 'urun']  # Aynı ürün 2 kez alınamaz

    def __str__(self):
        return f"{self.kullanici.username} - {self.urun.isim}"


class KullaniciEnvanter(models.Model):
    """Kullanıcının sahip olduğu ürünler ve aktif olanlar"""

    kullanici = models.OneToOneField(User, on_delete=models.CASCADE, related_name='envanter')

    # Aktif ürünler
    aktif_unvan = models.ForeignKey(
        MagazaUrun, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='aktif_unvan_kullanicilari', verbose_name='Aktif Unvan'
    )
    aktif_cerceve = models.ForeignKey(
        MagazaUrun, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='aktif_cerceve_kullanicilari', verbose_name='Aktif Çerçeve'
    )
    aktif_tema = models.ForeignKey(
        MagazaUrun, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='aktif_tema_kullanicilari', verbose_name='Aktif Tema'
    )

    class Meta:
        verbose_name = 'Kullanıcı Envanteri'
        verbose_name_plural = 'Kullanıcı Envanterleri'

    def __str__(self):
        return f"{self.kullanici.username} - Envanter"

    def sahip_mi(self, urun):
        """Kullanıcı bu ürüne sahip mi?"""
        return SatinAlma.objects.filter(kullanici=self.kullanici, urun=urun).exists()