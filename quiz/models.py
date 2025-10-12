from django.db import models
from django.contrib.auth.models import User
import uuid

# --- YKS SORU MODELLERİ ---
class Konu(models.Model):
    ad = models.CharField(max_length=255, default='Genel Konu')
    def __str__(self): return self.ad

class Soru(models.Model):
    konu = models.ForeignKey(Konu, on_delete=models.CASCADE)
    metin = models.TextField()
    def __str__(self): return self.metin[:50]

class Cevap(models.Model):
    soru = models.ForeignKey(Soru, on_delete=models.CASCADE)
    metin = models.CharField(max_length=255)
    dogru_mu = models.BooleanField(default=False)
    def __str__(self): return f"{self.soru.metin[:20]}... - {self.metin}"

class KullaniciCevap(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    soru = models.ForeignKey(Soru, on_delete=models.CASCADE)
    verilen_cevap = models.ForeignKey(Cevap, on_delete=models.CASCADE)
    tarih = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.kullanici.username} - {self.soru.metin[:20]}"

# --- TABU OYUNU MODELLERİ ---
class TabuKelime(models.Model):
    kelime = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.kelime

class TabuYasakliKelime(models.Model):
    ana_kelime = models.ForeignKey(TabuKelime, on_delete=models.CASCADE, related_name='yasakli_kelimeler')
    yasakli_kelime = models.CharField(max_length=100)
    def __str__(self): return f"{self.ana_kelime.kelime} -> {self.yasakli_kelime}"

class TabuOyun(models.Model):
    TAKIM_SECENEKLERI = [('A', 'Takım A'), ('B', 'Takım B')]
    OYUN_MODLARI = [('normal', 'Normal'), ('uzatma', 'Uzatma')]
    takim_a_adi = models.CharField(max_length=50, default='Takım A')
    takim_b_adi = models.CharField(max_length=50, default='Takım B')
    takim_a_skor = models.IntegerField(default=0)
    takim_b_skor = models.IntegerField(default=0)
    aktif_takim = models.CharField(max_length=1, choices=TAKIM_SECENEKLERI, default='A')
    oyun_durumu = models.CharField(max_length=20, default='baslamadi')
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    tur_sayisi = models.IntegerField(default=0)
    oyun_modu = models.CharField(max_length=10, choices=OYUN_MODLARI, default='normal')
    def __str__(self): return f"{self.takim_a_adi} vs {self.takim_b_adi} - Oyun ID: {self.id}"
    def get_kazanan(self):
        if self.takim_a_skor > self.takim_b_skor: return self.takim_a_adi
        elif self.takim_b_skor > self.takim_a_skor: return self.takim_b_adi
        else: return "Berabere"

# --- KARŞILAŞMA ODASI MODELİ ---
class KarsilasmaOdasi(models.Model):
    OYUN_DURUMLARI = (('bekleniyor', 'Rakip Bekleniyor'), ('oynaniyor', 'Oynanıyor'), ('bitti', 'Bitti'))
    oda_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oyuncu1 = models.ForeignKey(User, related_name='oyun_odalari1', on_delete=models.SET_NULL, null=True)
    oyuncu2 = models.ForeignKey(User, related_name='oyun_odalari2', on_delete=models.SET_NULL, null=True, blank=True)
    oyuncu1_skor = models.IntegerField(default=0)
    oyuncu2_skor = models.IntegerField(default=0)
    oyun_durumu = models.CharField(max_length=10, choices=OYUN_DURUMLARI, default='bekleniyor')
    created_at = models.DateTimeField(auto_now_add=True)
    aktif_soru = models.ForeignKey(Soru, on_delete=models.SET_NULL, null=True, blank=True)
    
    # "Yarış Durumu" hatasını çözmek için eklenen hafıza alanları
    oyuncu1_cevapladi = models.BooleanField(default=False)
    oyuncu2_cevapladi = models.BooleanField(default=False)
    ilk_dogru_cevaplayan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Oda: {self.oda_id} - {self.oyun_durumu}"