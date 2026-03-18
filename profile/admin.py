from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import OgrenciProfili, OyunModuIstatistik, DersIstatistik
from profile.models import Bildirim, Arkadaslik, GunlukGorevSablonu, KullaniciGunlukGorev, CalismaKaydi, XPGecmisi


# ========================================
# 1. OgrenciProfili Admin
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
    readonly_fields = []
    ordering = ['-toplam_puan']

    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('kullanici', 'ad', 'soyad', 'profil_fotografi')
        }),
        ('Seviye Sistemi', {
            'fields': ('seviye', 'xp'),
        }),
        ('Günlük Giriş & Streak', {
            'fields': ('son_giris_tarihi', 'ardasik_gun_sayisi', 'en_uzun_streak'),
        }),
        ('Akademik Bilgiler', {
            'fields': ('alan', 'hedef_puan', 'unvanlar')
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
            profil.haftalik_sifirla()
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
        from profile.xp_helper import xp_ekle
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
# 2. OyunModuIstatistik Admin
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

    @admin.action(description="🔄 Haftalık istatistikleri sıfırla")
    def haftalik_sifirla_action(self, request, queryset):
        count = 0
        for istatistik in queryset:
            istatistik.haftalik_sifirla()
            count += 1
        self.message_user(request, f"✅ {count} oyun modu istatistiği sıfırlandı.")


# ========================================
# 3. DersIstatistik Admin
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

    @admin.action(description="🔄 Haftalık istatistikleri sıfırla")
    def haftalik_sifirla_action(self, request, queryset):
        count = 0
        for istatistik in queryset:
            istatistik.haftalik_sifirla()
            count += 1
        self.message_user(request, f"✅ {count} ders istatistiği sıfırlandı.")


# ========================================
# 4. Bildirim Admin
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
            'fields': ('tip', 'baslik', 'mesaj', 'icon')
        }),
        ('Durum', {
            'fields': ('okundu_mu', 'iliskili_rozet')
        }),
        ('Tarih', {
            'fields': ('olusturma_tarihi',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('kullanici', 'iliskili_rozet')


# ========================================
# 5. Arkadaşlık Admin
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
            'fields': ('gonderen', 'alan')
        }),
        ('Durum', {
            'fields': ('durum',)
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('gonderen', 'alan')

    actions = ['kabul_et', 'reddet']

    @admin.action(description='✅ Seçili arkadaşlıkları kabul et')
    def kabul_et(self, request, queryset):
        guncellenen = queryset.update(durum='kabul_edildi')
        self.message_user(request, f'✅ {guncellenen} arkadaşlık kabul edildi.')

    @admin.action(description='❌ Seçili arkadaşlıkları reddet')
    def reddet(self, request, queryset):
        guncellenen = queryset.update(durum='reddedildi')
        self.message_user(request, f'❌ {guncellenen} arkadaşlık reddedildi.')


# ========================================
# 6. Günlük Görev Şablonu Admin
# ========================================
@admin.register(GunlukGorevSablonu)
class GunlukGorevSablonuAdmin(admin.ModelAdmin):
    list_display = [
        'icon', 'isim', 'gorev_tipi', 'hedef_sayi',
        'odul_xp', 'odul_puan', 'zorluk', 'aktif_mi'
    ]
    list_filter = ['gorev_tipi', 'zorluk', 'aktif_mi']
    list_editable = ['aktif_mi', 'hedef_sayi', 'odul_xp', 'zorluk']
    search_fields = ['isim', 'aciklama']
    ordering = ['zorluk', 'gorev_tipi']

    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('isim', 'aciklama', 'icon', 'gorev_tipi')
        }),
        ('Hedef & Ödül', {
            'fields': ('hedef_sayi', 'odul_xp', 'odul_puan', 'zorluk')
        }),
        ('Durum', {
            'fields': ('aktif_mi',)
        }),
    )

    actions = ['aktif_yap', 'pasif_yap']

    @admin.action(description='✅ Seçili görevleri aktif yap')
    def aktif_yap(self, request, queryset):
        guncellenen = queryset.update(aktif_mi=True)
        self.message_user(request, f'✅ {guncellenen} görev aktif yapıldı.')

    @admin.action(description='❌ Seçili görevleri pasif yap')
    def pasif_yap(self, request, queryset):
        guncellenen = queryset.update(aktif_mi=False)
        self.message_user(request, f'❌ {guncellenen} görev pasif yapıldı.')


# ========================================
# 7. Kullanıcı Günlük Görev Admin
# ========================================
@admin.register(KullaniciGunlukGorev)
class KullaniciGunlukGorevAdmin(admin.ModelAdmin):
    list_display = [
        'profil', 'sablon', 'tarih',
        'mevcut_ilerleme', 'tamamlandi_mi', 'odul_alindi_mi'
    ]
    list_filter = ['tamamlandi_mi', 'odul_alindi_mi', 'tarih', 'sablon__gorev_tipi']
    search_fields = ['profil__kullanici__username', 'sablon__isim']
    readonly_fields = ['tamamlanma_zamani']
    ordering = ['-tarih', 'tamamlandi_mi']
    date_hierarchy = 'tarih'

    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('profil', 'sablon', 'tarih')
        }),
        ('İlerleme', {
            'fields': ('mevcut_ilerleme', 'tamamlandi_mi', 'tamamlanma_zamani')
        }),
        ('Ödül', {
            'fields': ('odul_alindi_mi',)
        }),
    )

    actions = ['gorevi_tamamla', 'gorevi_sifirla']

    @admin.action(description='✅ Seçili görevleri tamamlandı olarak işaretle')
    def gorevi_tamamla(self, request, queryset):
        from django.utils import timezone
        guncellenen = queryset.update(
            tamamlandi_mi=True,
            tamamlanma_zamani=timezone.now()
        )
        self.message_user(request, f'✅ {guncellenen} görev tamamlandı olarak işaretlendi.')

    @admin.action(description='🔄 Seçili görevleri sıfırla')
    def gorevi_sifirla(self, request, queryset):
        guncellenen = queryset.update(
            mevcut_ilerleme=0,
            tamamlandi_mi=False,
            tamamlanma_zamani=None,
            odul_alindi_mi=False
        )
        self.message_user(request, f'🔄 {guncellenen} görev sıfırlandı.')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'profil__kullanici', 'sablon'
        )


# ========================================
# 8. Çalışma Kaydı Admin
# ========================================
@admin.register(CalismaKaydi)
class CalismaKaydiAdmin(admin.ModelAdmin):
    list_display = [
        'profil', 'tarih', 'cozulen_soru',
        'dogru_sayisi', 'yanlis_sayisi',
        'kazanilan_xp', 'oynanan_oyun', 'aktiflik_seviyesi'
    ]
    list_filter = ['tarih']
    search_fields = ['profil__kullanici__username']
    readonly_fields = ['aktiflik_seviyesi']
    ordering = ['-tarih']
    date_hierarchy = 'tarih'

    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('profil', 'tarih')
        }),
        ('Çalışma Verileri', {
            'fields': (
                'cozulen_soru', 'dogru_sayisi',
                'yanlis_sayisi', 'kazanilan_xp',
                'oynanan_oyun', 'aktiflik_seviyesi'
            )
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profil__kullanici')
        

@admin.register(XPGecmisi)
class XPGecmisiAdmin(admin.ModelAdmin):
    list_display = ['profil', 'miktar', 'sebep', 'tarih']
    list_filter = ['tarih']
    search_fields = ['profil__kullanici__username', 'sebep']
    ordering = ['-tarih']


# ========================================
# 9. User Admin - OgrenciProfili Inline
# ========================================
class OgrenciProfiliInline(admin.StackedInline):
    model = OgrenciProfili
    can_delete = False
    verbose_name_plural = 'Öğrenci Profili'
    fk_name = 'kullanici'

    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('alan', 'profil_fotografi', 'unvanlar', 'seviye', 'xp')
        }),
        ('İstatistikler', {
            'fields': ('toplam_puan', 'haftalik_puan', 'ardasik_gun_sayisi')
        }),
    )


class OgrenciUserAdmin(BaseUserAdmin):
    inlines = (OgrenciProfiliInline,)

    def get_alan_isim(self, obj):
        try:
            return obj.profil.get_alan_display()
        except Exception:
            return '-'
    get_alan_isim.short_description = 'Alan Tercihi'

    def get_toplam_puan(self, obj):
        try:
            return f"{obj.profil.toplam_puan} 🏆"
        except Exception:
            return '-'
    get_toplam_puan.short_description = 'Toplam Puan'

    def get_seviye(self, obj):
        try:
            return f"Lv.{obj.profil.seviye} ⭐"
        except Exception:
            return '-'
    get_seviye.short_description = 'Seviye'

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'get_alan_isim',
        'get_seviye',
        'get_toplam_puan'
    )


# User modelini yeniden kaydet
admin.site.unregister(User)
admin.site.register(User, OgrenciUserAdmin)