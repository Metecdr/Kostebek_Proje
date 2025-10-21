from django.urls import path
from . import views

urlpatterns = [
    # Ana sayfa
    path('', views.quiz_anasayfa, name='quiz_anasayfa'),

    # Tabu Oyunu (Çalışan Versiyonlar)
    path('tabu/', views.tabu_lobi, name='tabu_lobi'),
    path('tabu/', views.tabu_lobi, name='tabu_anasayfa'),
    path('tabu/oyun/<int:oyun_id>/', views.tabu_oyna, name='tabu_oyna'),
    path('tabu/oyun/<int:oyun_id>/tur-guncelle/', views.tabu_tur_guncelle, name='tabu_tur_guncelle'),
    path('tabu/oyun/<int:oyun_id>/tur-degistir/', views.tabu_tur_degistir, name='tabu_tur_degistir'),
    path('tabu/oyun/<int:oyun_id>/sonuc/', views.tabu_sonuc, name='tabu_sonuc'),

    # Karşılaşma Modu (Çalışan Versiyonlar)
    path('karsilasma/', views.karsilasma_rakip_bul, name='karsilasma_rakip_bul'),
    path('karsilasma/oda/<uuid:oda_id>/', views.karsilasma_oyun, name='karsilasma_oyun'),
    path('karsilasma/oda/<uuid:oda_id>/durum/', views.karsilasma_durum_guncelle, name='karsilasma_durum'),


    # BUL BAKALIM OYUNU
    path('bul-bakalim/', views.bul_bakalim_basla, name='bul_bakalim_basla'),
    path('bul-bakalim/<uuid:oyun_id>/', views.bul_bakalim_oyun, name='bul_bakalim_oyun'),
    path('bul-bakalim/<uuid:oyun_id>/cevapla/', views.bul_bakalim_cevapla, name='bul_bakalim_cevapla'),
    path('bul-bakalim/<uuid:oyun_id>/sonuc/', views.bul_bakalim_sonuc, name='bul_bakalim_sonuc'),
    path('bul-bakalim/ders-secimi/', views.bul_bakalim_ders_secimi, name='bul_bakalim_ders_secimi'),
    path('bul-bakalim/sinav-tipi/', views.bul_bakalim_sinav_tipi_secimi, name='bul_bakalim_sinav_tipi_secimi'),
    path('bul-bakalim/ders-secimi/', views.bul_bakalim_ders_secimi, name='bul_bakalim_ders_secimi'),

]