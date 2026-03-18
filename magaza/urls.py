from django.urls import path
from magaza import views

urlpatterns = [
    path('', views.magaza, name='magaza'),
    path('envanter/', views.envanter, name='envanter'),
    path('satin-al/<int:urun_id>/', views.satin_al, name='satin_al'),
    path('aktif-et/<int:urun_id>/', views.urun_aktif_et, name='urun_aktif_et'),
    path('kaldir/<int:urun_id>/', views.urun_kaldir, name='urun_kaldir'),
]