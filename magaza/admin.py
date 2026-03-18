from django.contrib import admin
from magaza.models import MagazaUrun, SatinAlma, KullaniciEnvanter


@admin.register(MagazaUrun)
class MagazaUrunAdmin(admin.ModelAdmin):
    list_display = ['icon', 'isim', 'kategori', 'fiyat', 'aktif']
    list_filter = ['kategori', 'aktif']
    search_fields = ['isim', 'aciklama']
    list_editable = ['fiyat', 'aktif']


@admin.register(SatinAlma)
class SatinAlmaAdmin(admin.ModelAdmin):
    list_display = ['kullanici', 'urun', 'odenen_puan', 'tarih']
    list_filter = ['urun__kategori']
    search_fields = ['kullanici__username', 'urun__isim']


@admin.register(KullaniciEnvanter)
class KullaniciEnvanterAdmin(admin.ModelAdmin):
    list_display = ['kullanici', 'aktif_unvan', 'aktif_cerceve', 'aktif_tema']
    search_fields = ['kullanici__username']