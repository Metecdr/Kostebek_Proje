from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django Yönetim Paneli
    path('admin/', admin.site.urls),
    
    # Anasayfa, Giriş, Kayıt, Profil ve Liderlik URL'leri
    path('', include('profile.urls')), 
    
    # Quiz (Karşılaşma) URL'leri
    path('quiz/', include('quiz.urls')), 
]