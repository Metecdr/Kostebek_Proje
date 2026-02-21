from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin 
from django.contrib.auth.models import User 
from .models import OgrenciProfili, OyunModuIstatistik, DersIstatistik
from profile.models import Bildirim, Arkadaslik

# ========================================
# 1.OgrenciProfili Admin (Bağımsız)
# ========================================
@admin.register(OgrenciProfili)
class OgrenciProfiliAdmin(admin.ModelAdmin):
    list_display = [
        'kullanici', 
        'alan', 
        'seviye',
        'xp',
        'toplam_puan', 
        'haftalik_puan',
        'ardasik_gun_sayisi',
        'unvanlar'
    ]
    list_filter = ['alan', 'kayit_tarihi', 'seviye', 'ardasik_gun_sayisi']
    search_fields = ['kullanici__username', 'kullanici__email']
    
    # ✅ READONLY FIELDS:  ŞİMDİ BOŞ!   HATA VERMESİN DİYE
    readonly_fields = []
    
    ordering = ['-toplam_puan']
    
    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('kullanici', 'ad', 'soyad', 'profil_fotografi')
        }),
        ('Seviye Sistemi', {
            'fields':   ('seviye', 'xp'),
        }),
        ('Günlük Giriş & Streak', {
            'fields':  ('son_giris_tarihi', 'ardasik_gun_sayisi', 'en_uzun_streak'),
        }),
        ('Akademik Bilgiler', {
            'fields':  ('alan', 'hedef_puan', 'unvanlar')
        }),
        ('İstatistikler', {
            'fields': ('toplam_puan', 'haftalik_puan', 'cozulen_soru_sayisi', 'toplam_dogru', 'toplam_yanlis')
        }),
    )
    
    actions = ['haftalik_sifirla_action', 'xp_ekle_100', 'xp_ekle_500', 'seviye_sifirla']
    
    @admin.action(description="🔄 Haftalık istatistikleri sıfırla")
    def haftalik_sifirla_action(self, request, queryset):
        count = 0
        for profil in queryset:
            profil.  haftalik_sifirla()
            count += 1
        self.message_user(request, f"✅ {count} profilin haftalık istatistikleri sıfırlandı.")

    @admin.action(description='⭐ Seçili profillere 100 XP ekle')
    def xp_ekle_100(self, request, queryset):
        from profile.xp_helper import xp_ekle
        for profil in queryset:
            xp_ekle(profil, 100, 'Admin tarafından eklendi')
        self.message_user(request, f'✅ {queryset.count()} profile 100 XP eklendi.')
    
    @admin.action(description='🌟 Seçili profillere 500 XP ekle')
    def xp_ekle_500(self, request, queryset):
        from profile. xp_helper import xp_ekle
        for profil in queryset:
            xp_ekle(profil, 500, 'Admin tarafından eklendi')
        self.message_user(request, f'✅ {queryset.count()} profile 500 XP eklendi.')
    
    @admin.action(description='🔄 Seçili profillerin seviyesini sıfırla')
    def seviye_sifirla(self, request, queryset):
        guncellenen = queryset.update(xp=0, seviye=1, ardasik_gun_sayisi=0)
        self.message_user(request, f'✅ {guncellenen} profilin seviyesi sıfırlandı.')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('kullanici')

# ========================================
# 2.OyunModuIstatistik Admin (Karşılaşma/Bul Bakalım)
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
# 3.DersIstatistik Admin (Ders Bazlı Liderlik)
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
# 4.Bildirim Admin
# ========================================
@admin.register(Bildirim)
class BildirimAdmin(admin.ModelAdmin):
    list_display = ('kullanici', 'tip', 'baslik', 'okundu_mu', 'olusturma_tarihi')
    list_filter = ('tip', 'okundu_mu', 'olusturma_tarihi')
    search_fields = ('kullanici__username', 'baslik', 'mesaj')
    readonly_fields = ('olusturma_tarihi',)
    list_per_page = 50
    
    fieldsets = (
        ('Kullanıcı', {
            'fields': ('kullanici',)
        }),
        ('Bildirim Bilgileri', {
            'fields':  ('tip', 'baslik', 'mesaj', 'icon')
        }),
        ('Durum', {
            'fields':  ('okundu_mu', 'iliskili_rozet')
        }),
        ('Tarih', {
            'fields':  ('olusturma_tarihi',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('kullanici', 'iliskili_rozet')


# ========================================
# 5.Arkadaşlık Admin
# ========================================
@admin.register(Arkadaslik)
class ArkadaslikAdmin(admin.ModelAdmin):
    list_display = ('gonderen', 'alan', 'durum', 'olusturma_tarihi')
    list_filter = ('durum', 'olusturma_tarihi')
    search_fields = ('gonderen__username', 'alan__username')
    readonly_fields = ('olusturma_tarihi', 'guncelleme_tarihi')
    list_per_page = 50
    
    fieldsets = (
        ('Kullanıcılar', {
            'fields':  ('gonderen', 'alan')
        }),
        ('Durum', {
            'fields':  ('durum',)
        }),
        ('Tarihler', {
            'fields':  ('olusturma_tarihi', 'guncelleme_tarihi')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('gonderen', 'alan')
    
    actions = ['kabul_et', 'reddet']
    
    def kabul_et(self, request, queryset):
        guncellenen = queryset.update(durum='kabul_edildi')
        self.message_user(request, f'✅ {guncellenen} arkadaşlık kabul edildi.')
    kabul_et.short_description = '✅ Seçili arkadaşlıkları kabul et'
    
    def reddet(self, request, queryset):
        guncellenen = queryset.update(durum='reddedildi')
        self.message_user(request, f'❌ {guncellenen} arkadaşlık reddedildi.')
    reddet.short_description = '❌ Seçili arkadaşlıkları reddet'


# ========================================
# 6.User Admin'e OgrenciProfili Inline Ekle
# ========================================
class OgrenciProfiliInline(admin.StackedInline):
    model = OgrenciProfili
    can_delete = False 
    verbose_name_plural = 'Öğrenci Profili' 
    fk_name = 'kullanici'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('alan', 'profil_fotografi', 'unvanlar', 'seviye', 'xp')  # ✅ GÜNCELLENDI
        }),
        ('İstatistikler', {
            'fields': ('toplam_puan', 'haftalik_puan', 'ardasik_gun_sayisi')  # ✅ GÜNCELLENDI
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

    # ✅ YENİ:  Seviye gösterimi
    def get_seviye(self, obj):
        try:
            return f"Lv.{obj.profil.seviye} ⭐"
        except: 
            return '-'
    get_seviye.short_description = 'Seviye'

    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'is_staff', 
        'get_alan_isim',
        'get_seviye',  # ✅ YENİ EKLENDI
        'get_toplam_puan'
    )


# User modelini yeniden kaydet
admin.site.unregister(User) 
admin.site.register(User, OgrenciUserAdmin)