from django.contrib import admin
from .models import (
    Konu,
    Soru, 
    Cevap, 
    TabuKelime, 
    YasakliKelime, 
    TabuOyun, 
    KarsilasmaOdasi, 
    KullaniciCevap,
    Rozet,
    KullaniciRozet,
    Turnuva,
    TurnuvaKatilim,
    TurnuvaMaci

)

@admin.register(Konu)
class KonuAdmin(admin.ModelAdmin):
    list_display = ('isim', 'sira', 'ders')  # 'sira' alanı eklendi
    list_editable = ('sira',)  # 'sira' düzenlenebilir hale getirildi
    ordering = ['sira']  # 'sira' sıralama için kullanılıyor


@admin.register(Soru)
class SoruAdmin(admin.ModelAdmin):
    list_display = ['metin_kisaltma', 'ders', 'konu', 'bul_bakalimda_cikar']
    list_filter = ['ders', 'konu', 'bul_bakalimda_cikar']
    search_fields = ['metin']
    list_per_page = 20
    
    def metin_kisaltma(self, obj):
        return obj.metin[:50] + "..." if len(obj.metin) > 50 else obj.metin
    metin_kisaltma.short_description = 'Soru Metni'

@admin.register(Cevap)
class CevapAdmin(admin.ModelAdmin):
    list_display = ['soru_kisaltma', 'metin', 'dogru_mu']
    list_filter = ['dogru_mu']
    search_fields = ['metin', 'soru__metin']
    list_per_page = 50
    
    def soru_kisaltma(self, obj):
        return obj.soru.metin[:30] + "..." if len(obj.soru.metin) > 30 else obj.soru.metin
    soru_kisaltma.short_description = 'Soru'

class YasakliKelimeInline(admin.TabularInline):
    model = YasakliKelime
    extra = 5      # 5 kutucuk çıkar
    max_num = 5    # En fazla 5 kutucuk olur
    min_num = 5    # En az 5 kutucuk doldurulmalı (Django 3.1+)

@admin.register(TabuKelime)
class TabuKelimeAdmin(admin.ModelAdmin):
    list_display = ['kelime']
    inlines = [YasakliKelimeInline]

@admin.register(YasakliKelime)
class YasakliKelimeAdmin(admin.ModelAdmin):
    list_display = ['tabu_kelime', 'yasakli_kelime']
    list_filter = ['tabu_kelime']
    search_fields = ['yasakli_kelime', 'tabu_kelime__kelime']
    list_per_page = 100

@admin.register(TabuOyun)
class TabuOyunAdmin(admin.ModelAdmin):
    list_display = ['takim_a_adi', 'takim_b_adi', 'takim_a_skor', 'takim_b_skor', 'oyun_durumu', 'olusturma_tarihi']
    list_filter = ['oyun_durumu', 'olusturma_tarihi']
    search_fields = ['takim_a_adi', 'takim_b_adi']
    readonly_fields = ['olusturma_tarihi']
    list_per_page = 20

@admin.register(KarsilasmaOdasi)
class KarsilasmaOdasiAdmin(admin.ModelAdmin):
    list_display = [
        'oda_id_kisaltma', 
        'oyuncu1', 
        'oyuncu2', 
        'oyuncu1_skor', 
        'oyuncu2_skor',
        'oyuncu1_dogru',
        'oyuncu1_yanlis',
        'oyun_durumu', 
        'aktif_soru_no',
        'olusturma_tarihi'
    ]
    list_filter = ['oyun_durumu', 'olusturma_tarihi']
    search_fields = ['oyuncu1__username', 'oyuncu2__username']
    readonly_fields = ['oda_id', 'olusturma_tarihi']
    list_per_page = 20
    
    def oda_id_kisaltma(self, obj):
        return str(obj.oda_id)[:8]
    oda_id_kisaltma.short_description = 'Oda ID'

@admin.register(KullaniciCevap)
class KullaniciCevapAdmin(admin.ModelAdmin):
    list_display = ['kullanici', 'soru_kisaltma', 'verilen_cevap_kisaltma', 'dogru_mu', 'tarih']
    list_filter = ['dogru_mu', 'tarih']
    search_fields = ['kullanici__username', 'soru__metin']
    readonly_fields = ['tarih']
    list_per_page = 50
    
    def soru_kisaltma(self, obj):
        return obj.soru.metin[:50] + "..." if len(obj.soru.metin) > 50 else obj.soru.metin
    soru_kisaltma.short_description = 'Soru'
    
    def verilen_cevap_kisaltma(self, obj):
        return obj.verilen_cevap.metin[:30] + "..." if len(obj.verilen_cevap.metin) > 30 else obj.verilen_cevap.metin
    verilen_cevap_kisaltma.short_description = 'Verilen Cevap'

@admin.register(Rozet)
class RozetAdmin(admin.ModelAdmin):
    list_display = ['ikon', 'adi', 'kosul_turu', 'kosul_degeri', 'sira']
    list_filter = ['kosul_turu']
    search_fields = ['adi']
    list_editable = ['sira']
    ordering = ['sira', 'kosul_degeri']

# ✅ SADECE BİR KEZ REGISTER EDİLDİ
@admin.register(KullaniciRozet)
class KullaniciRozetAdmin(admin.ModelAdmin):
    list_display = ['kullanici', 'rozet', 'kazanma_tarihi']
    list_filter = ['rozet', 'kazanma_tarihi']
    search_fields = ['kullanici__username', 'rozet__adi']
    readonly_fields = ['kazanma_tarihi']
    list_per_page = 50


@admin.register(Turnuva)
class TurnuvaAdmin(admin.ModelAdmin):
    list_display = ['isim', 'sinav_tipi', 'durum', 'katilimci_sayisi_display', 'max_katilimci', 'kayit_baslangic', 'baslangic']
    list_filter = ['durum', 'sinav_tipi', 'baslangic']
    search_fields = ['isim', 'aciklama']
    filter_horizontal = ['katilimcilar']
    readonly_fields = ['turnuva_id', 'olusturma_tarihi', 'guncelleme_tarihi']
    
    def katilimci_sayisi_display(self, obj):
        return f"{obj.katilimci_sayisi}/{obj.max_katilimci}"
    katilimci_sayisi_display.short_description = 'Katılımcı'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('turnuva_id', 'isim', 'aciklama', 'sinav_tipi', 'ders')
        }),
        ('Tarih ve Saat', {
            'fields': ('kayit_baslangic', 'kayit_bitis', 'baslangic', 'bitis')
        }),
        ('Ayarlar', {
            'fields': ('toplam_soru', 'max_katilimci', 'durum')
        }),
        ('Ödüller', {
            'fields': ('odul_xp_1', 'odul_xp_2', 'odul_xp_3')
        }),
        ('Katılımcılar', {
            'fields': ('katilimcilar',)
        }),
        ('Kazananlar', {
            'fields': ('birinci', 'ikinci', 'ucuncu')
        }),
        ('Zaman Damgaları', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi')
        }),
    )


@admin.register(TurnuvaMaci)
class TurnuvaMaciAdmin(admin.ModelAdmin):
    list_display = ['turnuva', 'round', 'oyuncu1', 'oyuncu2', 'kazanan', 'tamamlandi', 'mac_tarihi']
    list_filter = ['turnuva', 'round', 'tamamlandi']
    search_fields = ['turnuva__isim', 'oyuncu1__username', 'oyuncu2__username']
    readonly_fields = ['mac_id', 'olusturma_tarihi']


@admin.register(TurnuvaKatilim)
class TurnuvaKatilimAdmin(admin.ModelAdmin):
    list_display = ['turnuva', 'kullanici', 'sira', 'katilim_tarihi', 'elendi']
    list_filter = ['turnuva', 'elendi']
    search_fields = ['turnuva__isim', 'kullanici__username']