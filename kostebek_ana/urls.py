from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from kostebek_ana.sitemaps import StatikSayfalarSitemap, AnaSayfaSitemap

# Django Admin özelleştirme
admin.site.site_header = "Köstebek YKS Yönetim Paneli"
admin.site.site_title = "Köstebek Admin"
admin.site.index_title = "Yönetim"

sitemaps = {
    'statik': StatikSayfalarSitemap,
    'ana': AnaSayfaSitemap,
}

def ads_txt(request):
    return HttpResponse(
        "google.com, pub-2048768663669128, DIRECT, f08c47fec0942fa0",
        content_type="text/plain"
    )

urlpatterns = [
    path('admin/', admin.site.urls),

    # Sitemap (Google Search Console için)
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    # Google Adsense doğrulama için ads.txt
    path('ads.txt', ads_txt, name='ads_txt'),

    # Favicon (Google arama sonuçlarında logo gösterimi için)
    path('favicon.ico', lambda r: HttpResponseRedirect('/static/images/kostebek_logo.png')),

    # Profile (giris, cikis profil içinde)
    path('', include('profile.urls')),

    # Şifre sıfırlama (Django built-in, özel template'lerle)
    path('hesap/', include('django.contrib.auth.urls')),

    # Quiz
    path('', include('quiz.urls')),

    # Magaza
    path('magaza/', include('magaza.urls')),

    # Robots.txt
    path(
        "robots.txt",
        lambda r: HttpResponse(
            "User-agent: *\nAllow: /\n\nSitemap: https://kostebekyks.com/sitemap.xml\n",
            content_type="text/plain",
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)