from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin 
from django.contrib.auth.models import User 
from .models import OgrenciProfili 

# 1. OgrenciProfili modelini, ana User modeline gömülü (inline) olarak gösteren sınıf.
class OgrenciProfiliInline(admin.StackedInline):
    model = OgrenciProfili
    can_delete = False 
    verbose_name_plural = 'Öğrenci İstatistikleri' 
    # Profil düzenleme sayfasında görünecek alanlar
    fieldsets = (
        (None, {'fields': ('ad', 'soyad', 'hedef_puan', 'alan', 'toplam_puan', 'haftalik_puan', 'unvanlar')}),
    )

# 2. Django'nun varsayılan User Admin'ini genişleten sınıf
class OgrenciUserAdmin(BaseUserAdmin):
    inlines = (OgrenciProfiliInline,) 
    
    # YENİ EKLENDİ: Kullanıcı listesinde Alanı tam isimle göstermek için metot
    def get_alan_isim(self, obj):
        # obj.profil, OneToOneField ile OgrenciProfili nesnesine erişir.
        return obj.profil.get_alan_display() 
    
    get_alan_isim.short_description = 'Alan Tercihi' # Admin başlığı

    # Kullanıcı listesinde (list_display) hangi alanların görüneceğini tanımlıyoruz.
    # 'get_alan_isim' fonksiyonunu listeye ekledik.
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_alan_isim') # <-- BURAYA EKLEDİK

# 3. Django'nun varsayılan Kullanıcı modelinin kaydını kaldır ve bizim yeni yapımızı kaydet
admin.site.unregister(User) 
admin.site.register(User, OgrenciUserAdmin)