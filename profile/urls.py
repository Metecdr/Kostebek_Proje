from django.urls import path
from .import views

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

    # KONU ANALİZİ
    path('konu-analiz/', views.konu_analiz_view, name='konu_analiz'),

    # Bildirimler
    path('profil/bildirimler/', views.bildirimler_sayfa, name='bildirimler_sayfa'),
    path('profil/bildirimler/json/', views.bildirimler_json, name='bildirimler_json'),
    path('profil/bildirimler/<int:bildirim_id>/okundu/', views.bildirim_okundu, name='bildirim_okundu'),
    path('profil/bildirimler/hepsini-okundu-yap/', views.tum_bildirimleri_okundu_yap, name='tum_bildirimleri_okundu_yap'),

    # Arkadaşlık
    path('arkadaslarim/', views.arkadaslarim, name='arkadaslarim'),
    path('arkadas-ara/', views.arkadas_ara, name='arkadas_ara'),
    path('arkadaslik/gonder/<int:kullanici_id>/', views.arkadaslik_istek_gonder, name='arkadaslik_istek_gonder'),
    path('arkadaslik/kabul/<int:istek_id>/', views.arkadaslik_istek_kabul, name='arkadaslik_istek_kabul'),
    path('arkadaslik/reddet/<int:istek_id>/', views.arkadaslik_istek_reddet, name='arkadaslik_istek_reddet'),
    path('arkadas/cikar/<int:kullanici_id>/', views.arkadas_cikar, name='arkadas_cikar'),

    # Destek Sayfaları
    path('yardim-merkezi/', views.yardim_merkezi, name='yardim_merkezi'),
    path('sss/', views.sss, name='sss'),
    path('iletisim/', views.iletisim, name='iletisim'),
    path('gizlilik-politikasi/', views.gizlilik_politikasi, name='gizlilik_politikasi'),
]