from django.urls import path
from quiz.views import quiz_anasayfa
from . import views_turnuva
from quiz.views_tabu import (
    tabu_anasayfa, tabu_bolum_sec, tabu_lobi, tabu_oyun_basla, 
    tabu_oyun, tabu_tur_guncelle, tabu_tur_degistir, tabu_sonuc
)
from quiz.views_karsilasma import (
    karsilasma_sinav_tipi_secimi, karsilasma_ders_secimi, karsilasma_oyun, 
    karsilasma_durum_guncelle, karsilasma_sonuc, karsilasma_rakip_bul, 
    meydan_okuma_gonder,
    meydan_okuma_kabul,
    meydan_okuma_reddet,
    meydan_okumalarim,
    meydan_okuma_iptal,
    karsilasma_gecmis,
)
from quiz.views_bul_bakalim import (
    bul_bakalim_sinav_tipi_secimi, bul_bakalim_ders_secimi, bul_bakalim_basla, 
    bul_bakalim_oyun, bul_bakalim_cevapla, bul_bakalim_sonuc
)
from quiz.views_turnuva import (
    turnuva_listesi, turnuva_detay, turnuva_katil, turnuva_ayril,
    turnuva_mac_baslat, turnuva_mac_sonuc
)

urlpatterns = [
    # ==================== ANA SAYFA ====================
    path('', quiz_anasayfa, name='quiz_anasayfa'),
    
    # ==================== TABU ====================
    path('tabu/', tabu_anasayfa, name='tabu_anasayfa'),
    path('tabu/bolum-sec/', tabu_bolum_sec, name='tabu_bolum_sec'),
    path('tabu/lobi/', tabu_lobi, name='tabu_lobi'),
    path('tabu/basla/', tabu_oyun_basla, name='tabu_oyun_basla'),
    path('tabu/oyun/<int:oyun_id>/', tabu_oyun, name='tabu_oyun'),
    path('tabu/oyun/<int:oyun_id>/guncelle/', tabu_tur_guncelle, name='tabu_tur_guncelle'),
    path('tabu/oyun/<int:oyun_id>/tur-degistir/', tabu_tur_degistir, name='tabu_tur_degistir'),
    path('tabu/sonuc/<int:oyun_id>/', tabu_sonuc, name='tabu_sonuc'),
    
    # ==================== KARŞILAŞMA ====================
    path('karsilasma/sinav-tipi/', karsilasma_sinav_tipi_secimi, name='karsilasma_sinav_tipi_secimi'),
    path('karsilasma/ders-secimi/', karsilasma_ders_secimi, name='karsilasma_ders_secimi'),
    path('karsilasma/rakip-bul/', karsilasma_rakip_bul, name='karsilasma_rakip_bul'),
    path('karsilasma/oyun/<str:oda_id>/', karsilasma_oyun, name='karsilasma_oyun'),
    path('karsilasma/durum/<str:oda_id>/', karsilasma_durum_guncelle, name='karsilasma_durum_guncelle'),
    path('karsilasma/sonuc/<str:oda_id>/', karsilasma_sonuc, name='karsilasma_sonuc'),
    path('karsilasma/gecmis/', karsilasma_gecmis, name='karsilasma_gecmis'),
    
    # ==================== BUL BAKALIM ====================
    path('bul-bakalim/sinav-tipi/', bul_bakalim_sinav_tipi_secimi, name='bul_bakalim_sinav_tipi_secimi'),
    path('bul-bakalim/ders-secimi/', bul_bakalim_ders_secimi, name='bul_bakalim_ders_secimi'),
    path('bul-bakalim/basla/', bul_bakalim_basla, name='bul_bakalim_basla'),
    path('bul-bakalim/<uuid:oyun_id>/', bul_bakalim_oyun, name='bul_bakalim_oyun'),
    path('bul-bakalim/<uuid:oyun_id>/cevapla/', bul_bakalim_cevapla, name='bul_bakalim_cevapla'),
    path('bul-bakalim/<uuid:oyun_id>/sonuc/', bul_bakalim_sonuc, name='bul_bakalim_sonuc'),
    
    # ==================== 🏆 TURNUVA ====================
    path('turnuvalar/', turnuva_listesi, name='turnuva_listesi'),
    path('turnuva/<uuid:turnuva_id>/', turnuva_detay, name='turnuva_detay'),
    path('turnuva/<uuid:turnuva_id>/katil/', turnuva_katil, name='turnuva_katil'),
    path('turnuva/<uuid:turnuva_id>/ayril/', turnuva_ayril, name='turnuva_ayril'),
    
    # Turnuva Maç URL'leri
    path('turnuva/mac/<uuid:mac_id>/baslat/', turnuva_mac_baslat, name='turnuva_mac_baslat'),
    path('turnuva/mac/<uuid:mac_id>/sonuc/', turnuva_mac_sonuc, name='turnuva_mac_sonuc'),
    path('turnuva/mac/<uuid:mac_id>/hazir/', views_turnuva.turnuva_mac_hazir, name='turnuva_mac_hazir'),
    path('turnuva/mac/<uuid:mac_id>/bekleme/', views_turnuva.turnuva_mac_bekleme, name='turnuva_mac_bekleme'),

    # Turnuva Maç URL'leri (sıralama güncellemesi)
    path('turnuva/mac/<uuid:mac_id>/baslat/', views_turnuva.turnuva_mac_baslat, name='turnuva_mac_baslat'),
    path('turnuva/mac/<uuid:mac_id>/hazir/', views_turnuva.turnuva_mac_hazir, name='turnuva_mac_hazir'),
    path('turnuva/mac/<uuid:mac_id>/bekleme/', views_turnuva.turnuva_mac_bekleme, name='turnuva_mac_bekleme'),
    path('turnuva/mac/<uuid:mac_id>/sonuc/', views_turnuva.turnuva_mac_sonuc, name='turnuva_mac_sonuc'),

    # ==================== MEYDAN OKUMA ====================
    path('meydan-okuma/gonder/<int:kullanici_id>/', meydan_okuma_gonder, name='meydan_okuma_gonder'),
    path('meydan-okuma/kabul/<int:meydan_id>/', meydan_okuma_kabul, name='meydan_okuma_kabul'),
    path('meydan-okuma/reddet/<int:meydan_id>/', meydan_okuma_reddet, name='meydan_okuma_reddet'),
    path('meydan-okuma/iptal/<int:meydan_id>/', meydan_okuma_iptal, name='meydan_okuma_iptal'),
    path('meydan-okumalarim/', meydan_okumalarim, name='meydan_okumalarim'),
]