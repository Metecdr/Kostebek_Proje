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
    karsilasma_oda_kur, karsilasma_oda_bekleme, karsilasma_oda_bekleme_durum,
    karsilasma_oda_katil, karsilasma_oda_hazir, karsilasma_oda_ayril, karsilasma_oda_birak,
    meydan_okuma_gonder,
    meydan_okuma_kabul,
    meydan_okuma_reddet,
    meydan_okumalarim,
    meydan_okuma_iptal,
    revans_gonder,
    karsilasma_gecmis,
)
from quiz.views_soru_yonetim import (
    soru_yonetim_anasayfa,
    soru_ekle,
    soru_duzenle,
    soru_sil,
    toplu_metin_ekle,
    konular_by_ders,
    gunun_sorusu_yonetim,
    soru_bildir,
    soru_bildirimleri_listesi,
    soru_bildirim_incele,
)
from quiz.views_gunun_sorusu import gunun_sorusu_view, gunun_sorusu_cevapla
from quiz.views_bul_bakalim import (
    bul_bakalim_sinav_tipi_secimi, bul_bakalim_ders_secimi, bul_bakalim_basla,
    bul_bakalim_oyun, bul_bakalim_cevapla, bul_bakalim_sonuc, bul_bakalim_konular
)
from quiz.views_yanlis_tekrar import yanlislarima_don, yanlis_tekrar_calis
from quiz.views_turnuva import (
    turnuva_listesi, turnuva_detay, turnuva_katil, turnuva_ayril,
    turnuva_mac_baslat, turnuva_mac_sonuc, turnuva_yonetim
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
    path('karsilasma/oda-kur/', karsilasma_oda_kur, name='karsilasma_oda_kur'),
    path('karsilasma/oda/<str:oda_kodu>/bekleme/', karsilasma_oda_bekleme, name='karsilasma_oda_bekleme'),
    path('karsilasma/oda/<str:oda_kodu>/durum/', karsilasma_oda_bekleme_durum, name='karsilasma_oda_bekleme_durum'),
    path('karsilasma/oda-katil/', karsilasma_oda_katil, name='karsilasma_oda_katil'),
    path('karsilasma/oda/<str:oda_kodu>/hazir/', karsilasma_oda_hazir, name='karsilasma_oda_hazir'),
    path('karsilasma/oda/<str:oda_kodu>/ayril/', karsilasma_oda_ayril, name='karsilasma_oda_ayril'),
    path('karsilasma/oda-birak/<str:oda_id>/', karsilasma_oda_birak, name='karsilasma_oda_birak'),
    
    # ==================== BUL BAKALIM ====================
    path('bul-bakalim/sinav-tipi/', bul_bakalim_sinav_tipi_secimi, name='bul_bakalim_sinav_tipi_secimi'),
    path('bul-bakalim/ders-secimi/', bul_bakalim_ders_secimi, name='bul_bakalim_ders_secimi'),
    path('bul-bakalim/konular/', bul_bakalim_konular, name='bul_bakalim_konular'),
    path('bul-bakalim/basla/', bul_bakalim_basla, name='bul_bakalim_basla'),

    # ==================== YANLIŞLARIMA DÖN ====================
    path('yanlislarima-don/', yanlislarima_don, name='yanlislarima_don'),
    path('yanlis-tekrar/', yanlis_tekrar_calis, name='yanlis_tekrar_calis'),
    path('bul-bakalim/<uuid:oyun_id>/', bul_bakalim_oyun, name='bul_bakalim_oyun'),
    path('bul-bakalim/<uuid:oyun_id>/cevapla/', bul_bakalim_cevapla, name='bul_bakalim_cevapla'),
    path('bul-bakalim/<uuid:oyun_id>/sonuc/', bul_bakalim_sonuc, name='bul_bakalim_sonuc'),
    
    # ==================== 🏆 TURNUVA ====================
    path('turnuva-yonetim/', turnuva_yonetim, name='turnuva_yonetim'),
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

    # ==================== GÜNÜN SORUSU ====================
    path('gunun-sorusu/', gunun_sorusu_view, name='gunun_sorusu'),
    path('gunun-sorusu/cevapla/', gunun_sorusu_cevapla, name='gunun_sorusu_cevapla'),

    # ==================== SORU YÖNETİM PANELİ ====================
    path('soru-yonetim/', soru_yonetim_anasayfa, name='soru_yonetim_anasayfa'),
    path('soru-yonetim/ekle/', soru_ekle, name='soru_ekle'),
    path('soru-yonetim/duzenle/<int:soru_id>/', soru_duzenle, name='soru_duzenle'),
    path('soru-yonetim/sil/<int:soru_id>/', soru_sil, name='soru_sil'),
    path('soru-yonetim/toplu-ekle/', toplu_metin_ekle, name='toplu_metin_ekle'),
    path('soru-yonetim/konular-by-ders/', konular_by_ders, name='konular_by_ders'),
    path('soru-yonetim/gunun-sorusu/', gunun_sorusu_yonetim, name='gunun_sorusu_yonetim'),
    path('soru-yonetim/bildirimler/', soru_bildirimleri_listesi, name='soru_bildirimleri_listesi'),
    path('soru-yonetim/bildirimler/<int:bildirim_id>/incele/', soru_bildirim_incele, name='soru_bildirim_incele'),

    # ==================== SORU BİLDİR ====================
    path('soru/<int:soru_id>/bildir/', soru_bildir, name='soru_bildir'),

    # ==================== RÖVANŞ ====================
    path('revans/gonder/<int:kullanici_id>/', revans_gonder, name='revans_gonder'),

    # ==================== MEYDAN OKUMA ====================
    path('meydan-okuma/gonder/<int:kullanici_id>/', meydan_okuma_gonder, name='meydan_okuma_gonder'),
    path('meydan-okuma/kabul/<int:meydan_id>/', meydan_okuma_kabul, name='meydan_okuma_kabul'),
    path('meydan-okuma/reddet/<int:meydan_id>/', meydan_okuma_reddet, name='meydan_okuma_reddet'),
    path('meydan-okuma/iptal/<int:meydan_id>/', meydan_okuma_iptal, name='meydan_okuma_iptal'),
    path('meydan-okumalarim/', meydan_okumalarim, name='meydan_okumalarim'),
]