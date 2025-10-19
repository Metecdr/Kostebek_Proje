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
    KullaniciRozet
)

@admin.register(Konu)
class KonuAdmin(admin.ModelAdmin):
    list_display = ('isim', 'sira', 'ders')  # 'sira' alanı eklendi
    list_editable = ('sira',)  # 'sira' düzenlenebilir hale getirildi
    ordering = ['sira']  # 'sira' sıralama için kullanılıyor

admin.site.register(Konu, KonuAdmin)

@admin.register(Soru)
class SoruAdmin(admin.ModelAdmin):
    list_display = ['metin_kisaltma', 'konu', 'zorluk']
    list_filter = ['zorluk', 'konu']
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

@admin.register(TabuKelime)
class TabuKelimeAdmin(admin.ModelAdmin):
    list_display = ['kelime']
    search_fields = ['kelime']
    list_per_page = 50

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