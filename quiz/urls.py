# quiz/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # --- YENİ KARŞILAŞMA URL'LERİ (AJAX YÖNTEMİ) ---
    path('karsilasma/', views.karsilasma_rakip_bul, name='karsilasma_rakip_bul'),
    path('karsilasma/oda/<uuid:oda_id>/', views.karsilasma_oyun, name='karsilasma_oyun'),
    path('karsilasma/oda/<uuid:oda_id>/durum/', views.karsilasma_durum_guncelle, name='karsilasma_durum_guncelle'),
    
    # --- TAM VE EKSİKSİZ TABU URL'LERİ ---
    path('tabu/', views.tabu_lobi, name='tabu_lobi'),
    path('tabu/oyun/<int:oyun_id>/', views.tabu_oyna, name='tabu_oyna'),
    path('tabu/oyun/<int:oyun_id>/guncelle/', views.tabu_tur_guncelle, name='tabu_tur_guncelle'),
    path('tabu/oyun/<int:oyun_id>/tur-degistir/', views.tabu_tur_degistir, name='tabu_tur_degistir'),
    path('tabu/oyun/<int:oyun_id>/sonuc/', views.tabu_sonuc, name='tabu_sonuc'),
]