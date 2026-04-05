from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StatikSayfalarSitemap(Sitemap):
    """Giriş gerektirmeyen statik sayfalar"""
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'

    def items(self):
        return [
            'giris',
            'kayit',
            'liderlik',
            'liderlik_genel',
            'liderlik_oyun_modu',
            'liderlik_ders',
            'rozetler_view',
            'yardim_merkezi',
            'sss',
            'iletisim',
            'gizlilik_politikasi',
        ]

    def location(self, item):
        return reverse(item)


class AnaSayfaSitemap(Sitemap):
    """Ana sayfa"""
    changefreq = 'daily'
    priority = 1.0
    protocol = 'https'

    def items(self):
        return ['profil']

    def location(self, item):
        return '/'
