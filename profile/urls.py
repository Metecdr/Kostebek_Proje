from django.urls import path
from .import views
from profile.views_gorev import gunluk_gorevler_view, calisma_takvimi_view, gorev_odul_al
from profile.views_xp import xp_gecmisi_view, haftalik_rapor_view

urlpatterns = [
    path('kayit/', views.kayit_view, name='kayit'),
    path('giris/', views.giris_view, name='giris'),
    path('cikis/', views.cikis_view, name='cikis'),
    path('profil/', views.profil_view, name='profil'),
    path('profil/duzenle/', views.profil_duzenle_view, name='profil_duzenle'),
    
    # LİDERLİK SAYFALARI
    path('liderlik/', views.liderlik_view, name='liderlik'),
    path('liderlik/genel/', views.liderlik_genel_view, name='liderlik_genel'),
    path('liderlik/oyun-modu/', views.liderlik_oyun_modu_view, name='liderlik_oyun_modu'),
    path('liderlik/ders/', views.liderlik_ders_view, name='liderlik_ders'),

    # ROZETLER
    path('rozetler/', views.rozetler_view, name='rozetler_view'),

    # İSTATİSTİK SAYFALARI
    path('konu-istatistik/', views.konu_istatistik_view, name='konu_istatistik'),

    # KONU ANALİZİ
    path('konu-analiz/', views.konu_analiz_view, name='konu_analiz'),

    # Bildirimler
    path('profil/bildirimler/', views.bildirimler_sayfa, name='bildirimler_sayfa'),
    path('profil/bildirimler/json/', views.bildirimler_json, name='bildirimler_json'),
    path('profil/bildirimler/<int:bildirim_id>/okundu/', views.bildirim_okundu, name='bildirim_okundu'),
    path('profil/bildirimler/hepsini-okundu-yap/', views.tum_bildirimleri_okundu_yap, name='tum_bildirimleri_okundu_yap'),
    path('profil/bildirimler/<int:bildirim_id>/sil/', views.bildirim_sil, name='bildirim_sil'),

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
    path('kullanim-kosullari/', views.kullanim_kosullari, name='kullanim_kosullari'),
    path('hakkimizda/', views.hakkimizda, name='hakkimizda'),

    # Görevler
    path('gorevler/', gunluk_gorevler_view, name='gunluk_gorevler'),
    path('takvim/', calisma_takvimi_view, name='calisma_takvimi'),
    path('gorev/<int:gorev_id>/odul/', gorev_odul_al, name='gorev_odul_al'),

    # XP Geçmişi
    path('xp-gecmisi/', xp_gecmisi_view, name='xp_gecmisi'),

    path('haftalik-rapor/', haftalik_rapor_view, name='haftalik_rapor'),

    # Admin Dashboard
    path('yonetim/', views.admin_dashboard, name='admin_dashboard'),

    # Seviye Ödülleri
    path('seviye-oduller/', views.seviye_oduller_view, name='seviye_oduller'),

    # Duyuru Yönetimi (superuser only)
    path('duyurular/', views.duyuru_listesi, name='duyuru_listesi'),
    path('duyurular/ekle/', views.duyuru_ekle, name='duyuru_ekle'),
    path('duyurular/<int:duyuru_id>/duzenle/', views.duyuru_duzenle, name='duyuru_duzenle'),
    path('duyurular/<int:duyuru_id>/sil/', views.duyuru_sil, name='duyuru_sil'),
]