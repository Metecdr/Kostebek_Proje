from django.urls import path
from . import views

urlpatterns = [
    path('kayit/', views.kayit_view, name='kayit'),
    path('giris/', views.giris_view, name='giris'),
    path('cikis/', views.cikis_view, name='cikis'),
    path('profil/', views.profil_view, name='profil'),
    path('profil/duzenle/', views.profil_duzenle_view, name='profil_duzenle'),
    
    # LİDERLİK SAYFALARI
    path('liderlik/', views.liderlik_view, name='liderlik'),  # Ana liderlik
    path('liderlik/genel/', views.liderlik_genel_view, name='liderlik_genel'),
    path('liderlik/oyun-modu/', views.liderlik_oyun_modu_view, name='liderlik_oyun_modu'),
    path('liderlik/ders/', views.liderlik_ders_view, name='liderlik_ders'),

    # ROZETLER
    path('rozetler/', views.rozetler_view, name='rozetler_view'),  # ✅ EKLE

    # İSTATİSTİK SAYFALARI
    path('konu-istatistik/', views.konu_istatistik_view, name='konu_istatistik'),
]