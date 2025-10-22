from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin 
from django.contrib.auth.models import User 
from .models import OgrenciProfili, OyunModuIstatistik, DersIstatistik


# ========================================
# 1. OgrenciProfili Admin (Bağımsız)
# ========================================
@admin.register(OgrenciProfili)
class OgrenciProfiliAdmin(admin.ModelAdmin):
    list_display = [
        'kullanici', 
        'alan', 
        'toplam_puan', 
        'genel_basari_orani', 
        'haftalik_puan',
        'haftalik_basari_orani',
        'unvanlar'
    ]
    list_filter = ['alan', 'kayit_tarihi', 'unvanlar']
    search_fields = ['kullanici__username', 'kullanici__email']
    readonly_fields = ['kayit_tarihi', 'son_giris', 'genel_basari_orani', 'haftalik_basari_orani']
    ordering = ['-toplam_puan']
    
    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('kullanici', 'alan', 'profil_fotografi')
        }),
        ('Genel İstatistikler', {
            'fields': ('toplam_puan', 'cozulen_soru_sayisi', 'toplam_dogru', 'toplam_yanlis', 'genel_basari_orani')
        }),
        ('Haftalık İstatistikler', {
            'fields': ('haftalik_puan', 'haftalik_cozulen', 'haftalik_dogru', 'haftalik_yanlis', 'haftalik_basari_orani', 'hafta_baslangic'),
            'classes': ['collapse']
        }),
        ('Rozet & Tarihler', {
            'fields': ('unvanlar', 'kayit_tarihi', 'son_giris')
        }),
    )
    
    actions = ['haftalik_sifirla_action']
    
    def haftalik_sifirla_action(self, request, queryset):
        """Seçili profillerin haftalık istatistiklerini sıfırla"""
        count = 0
        for profil in queryset:
            profil.haftalik_sifirla()
            count += 1
        self.message_user(request, f"✅ {count} profilin haftalık istatistikleri sıfırlandı.")
    haftalik_sifirla_action.short_description = "🔄 Haftalık istatistikleri sıfırla"


# ========================================
# 2. OyunModuIstatistik Admin (Karşılaşma/Bul Bakalım)
# ========================================
@admin.register(OyunModuIstatistik)
class OyunModuIstatistikAdmin(admin.ModelAdmin):
    list_display = [
        'profil', 
        'oyun_modu', 
        'toplam_puan', 
        'oynanan_oyun_sayisi',
        'kazanilan_oyun',
        'kaybedilen_oyun',
        'basari_orani', 
        'galibiyet_orani'
    ]
    list_filter = ['oyun_modu']
    search_fields = ['profil__kullanici__username']
    readonly_fields = ['basari_orani', 'galibiyet_orani']
    ordering = ['-toplam_puan']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('profil', 'oyun_modu')
        }),
        ('Genel İstatistikler', {
            'fields': (
                'toplam_puan', 
                'oynanan_oyun_sayisi', 
                'kazanilan_oyun', 
                'kaybedilen_oyun',
                'cozulen_soru',
                'dogru_sayisi',
                'yanlis_sayisi',
                'basari_orani',
                'galibiyet_orani'
            )
        }),
        ('Haftalık İstatistikler', {
            'fields': (
                'haftalik_puan',
                'haftalik_oyun_sayisi',
                'haftalik_dogru',
                'haftalik_yanlis',
                'hafta_baslangic'
            ),
            'classes': ['collapse']
        }),
    )
    
    actions = ['haftalik_sifirla_action']
    
    def haftalik_sifirla_action(self, request, queryset):
        count = 0
        for istatistik in queryset:
            istatistik.haftalik_sifirla()
            count += 1
        self.message_user(request, f"✅ {count} oyun modu istatistiği sıfırlandı.")
    haftalik_sifirla_action.short_description = "🔄 Haftalık istatistikleri sıfırla"


# ========================================
# 3. DersIstatistik Admin (Ders Bazlı Liderlik)
# ========================================
@admin.register(DersIstatistik)
class DersIstatistikAdmin(admin.ModelAdmin):
    list_display = [
        'profil', 
        'ders', 
        'dogru_sayisi', 
        'yanlis_sayisi', 
        'net', 
        'basari_orani',
        'toplam_puan'
    ]
    list_filter = ['ders']
    search_fields = ['profil__kullanici__username']
    readonly_fields = ['net', 'basari_orani', 'haftalik_basari_orani']
    ordering = ['-dogru_sayisi']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('profil', 'ders')
        }),
        ('Genel İstatistikler', {
            'fields': (
                'toplam_puan',
                'cozulen_soru',
                'dogru_sayisi',
                'yanlis_sayisi',
                'bos_sayisi',
                'net',
                'basari_orani'
            )
        }),
        ('Haftalık İstatistikler', {
            'fields': (
                'haftalik_puan',
                'haftalik_cozulen',
                'haftalik_dogru',
                'haftalik_yanlis',
                'haftalik_basari_orani',
                'hafta_baslangic'
            ),
            'classes': ['collapse']
        }),
    )
    
    actions = ['haftalik_sifirla_action']
    
    def haftalik_sifirla_action(self, request, queryset):
        count = 0
        for istatistik in queryset:
            istatistik.haftalik_sifirla()
            count += 1
        self.message_user(request, f"✅ {count} ders istatistiği sıfırlandı.")
    haftalik_sifirla_action.short_description = "🔄 Haftalık istatistikleri sıfırla"


# ========================================
# 4. User Admin'e OgrenciProfili Inline Ekle
# ========================================
class OgrenciProfiliInline(admin.StackedInline):
    model = OgrenciProfili
    can_delete = False 
    verbose_name_plural = 'Öğrenci Profili' 
    fk_name = 'kullanici'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('alan', 'profil_fotografi', 'unvanlar')
        }),
        ('İstatistikler', {
            'fields': ('toplam_puan', 'haftalik_puan')
        }),
    )


class OgrenciUserAdmin(BaseUserAdmin):
    inlines = (OgrenciProfiliInline,) 
    
    def get_alan_isim(self, obj):
        try:
            return obj.profil.get_alan_display() 
        except:
            return '-'
    get_alan_isim.short_description = 'Alan Tercihi'
    
    def get_toplam_puan(self, obj):
        try:
            return f"{obj.profil.toplam_puan} 🏆"
        except:
            return '-'
    get_toplam_puan.short_description = 'Toplam Puan'

    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'is_staff', 
        'get_alan_isim',
        'get_toplam_puan'
    )


# User modelini yeniden kaydet
admin.site.unregister(User) 
admin.site.register(User, OgrenciUserAdmin)