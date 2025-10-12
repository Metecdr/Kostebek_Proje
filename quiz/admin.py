from django.contrib import admin
from .models import (
    Konu, Soru, Cevap, KullaniciCevap, 
    TabuKelime, TabuYasakliKelime, TabuOyun
)

# Bu, bir soru eklerken cevaplarını da aynı sayfada eklememizi sağlar. Çok kullanışlıdır.
class CevapInline(admin.TabularInline):
    model = Cevap
    extra = 4 # 4 tane boş cevap kutusu gösterir

class SoruAdmin(admin.ModelAdmin):
    list_display = ('metin', 'konu')
    list_filter = ('konu',)
    search_fields = ['metin']
    inlines = [CevapInline] # Cevapları bu sayfaya dahil et

class TabuYasakliKelimeInline(admin.TabularInline):
    model = TabuYasakliKelime
    extra = 5 

class TabuKelimeAdmin(admin.ModelAdmin):
    list_display = ('kelime', 'id')
    search_fields = ['kelime']
    inlines = [TabuYasakliKelimeInline]

class TabuOyunAdmin(admin.ModelAdmin):
    list_display = ('id', 'takim_a_adi', 'takim_a_skor', 'takim_b_adi', 'takim_b_skor', 'oyun_durumu')
    list_filter = ('oyun_durumu',)

# Modellerimizi admin paneline kaydediyoruz
admin.site.register(Konu)
admin.site.register(Soru, SoruAdmin) # Artık Soru'yu bu özel admin sınıfıyla kaydediyoruz
admin.site.register(KullaniciCevap)
admin.site.register(TabuKelime, TabuKelimeAdmin)
admin.site.register(TabuOyun, TabuOyunAdmin)