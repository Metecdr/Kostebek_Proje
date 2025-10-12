from django.urls import path
from . import views

urlpatterns = [
    # Anasayfa (Default)
    path('', views.anasayfa, name='anasayfa'), 
    
    # Oturum Yönetimi
    path('kayit/', views.kayit_view, name='kayit'),
    path('giris/', views.giris_view, name='giris'),
    path('cikis/', views.cikis_view, name='cikis'),
    
    # PROFİL URL'LERİ
    path('profil/', views.profil_view, name='profil'),
    path('liderlik/', views.liderlik_view, name='liderlik'), 

    # Profil Düzenleme
    path('profil/duzenle/', views.profil_duzenle_view, name='profil_duzenle'),
    
    # YENİ EKLENEN URL
    path('istatistik/konu/', views.konu_istatistik_view, name='konu_istatistik'), 
]