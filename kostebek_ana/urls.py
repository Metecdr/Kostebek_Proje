from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Django Admin özelleştirme
admin.site.site_header = "Köstebek YKS Yönetim Paneli"
admin.site.site_title = "Köstebek Admin"
admin.site.index_title = "Yönetim"

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Profile (giris, cikis profil içinde)
    path('', include('profile.urls')),
    
    # Quiz
    path('', include('quiz.urls')),

    # Magaza
    path('magaza/', include('magaza.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)