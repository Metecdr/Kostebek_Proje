from django.core.management.base import BaseCommand
from profile.models import GunlukGorevSablonu


class Command(BaseCommand):
    help = 'Günlük görev şablonlarını yükler (5 kolay + 5 orta + 5 zor)'

    def handle(self, *args, **options):
        gorevler = [
            # ==================== KOLAY ====================
            {
                'isim': '5 Soru Çöz',
                'aciklama': 'Bugün 5 soru çözerek günlük antrenmanını tamamla!',
                'gorev_tipi': 'soru_coz',
                'hedef_sayi': 5,
                'odul_xp': 30,
                'odul_puan': 10,
                'icon': '📝',
                'zorluk': 'kolay',
            },
            {
                'isim': '3 Doğru Cevap',
                'aciklama': '3 soruyu doğru yanıtla ve ödülünü kap!',
                'gorev_tipi': 'dogru_cevap',
                'hedef_sayi': 3,
                'odul_xp': 40,
                'odul_puan': 15,
                'icon': '✅',
                'zorluk': 'kolay',
            },
            {
                'isim': '1 Bul Bakalım Oyna',
                'aciklama': 'Bir Bul Bakalım oyunu oynayarak eğlenerek öğren!',
                'gorev_tipi': 'bul_bakalim_oyna',
                'hedef_sayi': 1,
                'odul_xp': 25,
                'odul_puan': 10,
                'icon': '🔍',
                'zorluk': 'kolay',
            },
            {
                'isim': '1 Karşılaşma Oyna',
                'aciklama': 'Bir rakiple karşılaş ve yeteneklerini test et!',
                'gorev_tipi': 'karsilasma_oyna',
                'hedef_sayi': 1,
                'odul_xp': 35,
                'odul_puan': 15,
                'icon': '⚔️',
                'zorluk': 'kolay',
            },
            {
                'isim': 'Streak Koru',
                'aciklama': 'Günlük giriş streak\'ini koruyarak sadakatini göster!',
                'gorev_tipi': 'streak_koru',
                'hedef_sayi': 1,
                'odul_xp': 50,
                'odul_puan': 20,
                'icon': '🔥',
                'zorluk': 'kolay',
            },
            # ==================== ORTA ====================
            {
                'isim': '15 Soru Çöz',
                'aciklama': '15 soru çözerek bilgini pekiştir!',
                'gorev_tipi': 'soru_coz',
                'hedef_sayi': 15,
                'odul_xp': 80,
                'odul_puan': 30,
                'icon': '📚',
                'zorluk': 'orta',
            },
            {
                'isim': '10 Doğru Cevap',
                'aciklama': '10 doğru cevap vererek ustalaş!',
                'gorev_tipi': 'dogru_cevap',
                'hedef_sayi': 10,
                'odul_xp': 100,
                'odul_puan': 40,
                'icon': '🎯',
                'zorluk': 'orta',
            },
            {
                'isim': '2 Farklı Dersten Çöz',
                'aciklama': 'En az 2 farklı dersten soru çözerek ufkunu genişlet!',
                'gorev_tipi': 'farkli_ders',
                'hedef_sayi': 2,
                'odul_xp': 70,
                'odul_puan': 25,
                'icon': '📖',
                'zorluk': 'orta',
            },
            {
                'isim': '3 Karşılaşma Oyna',
                'aciklama': '3 karşılaşma oynayarak rekabeti hisset!',
                'gorev_tipi': 'karsilasma_oyna',
                'hedef_sayi': 3,
                'odul_xp': 90,
                'odul_puan': 35,
                'icon': '🏟️',
                'zorluk': 'orta',
            },
            {
                'isim': '1 Karşılaşma Kazan',
                'aciklama': 'Bir karşılaşma kazanarak zaferini ilan et!',
                'gorev_tipi': 'karsilasma_kazan',
                'hedef_sayi': 1,
                'odul_xp': 120,
                'odul_puan': 50,
                'icon': '🏆',
                'zorluk': 'orta',
            },
            # ==================== ZOR ====================
            {
                'isim': '30 Soru Çöz',
                'aciklama': '30 soru çözerek sınav maratonu yap!',
                'gorev_tipi': 'soru_coz',
                'hedef_sayi': 30,
                'odul_xp': 200,
                'odul_puan': 80,
                'icon': '💪',
                'zorluk': 'zor',
            },
            {
                'isim': '20 Doğru Cevap',
                'aciklama': '20 doğru cevap vererek bilgi seviyeni kanıtla!',
                'gorev_tipi': 'dogru_cevap',
                'hedef_sayi': 20,
                'odul_xp': 250,
                'odul_puan': 100,
                'icon': '🌟',
                'zorluk': 'zor',
            },
            {
                'isim': '5 Karşılaşma Oyna',
                'aciklama': '5 karşılaşma oynayarak dayanıklılığını göster!',
                'gorev_tipi': 'karsilasma_oyna',
                'hedef_sayi': 5,
                'odul_xp': 220,
                'odul_puan': 90,
                'icon': '⚡',
                'zorluk': 'zor',
            },
            {
                'isim': '3 Karşılaşma Kazan',
                'aciklama': '3 karşılaşma kazanarak liderliğini ilan et!',
                'gorev_tipi': 'karsilasma_kazan',
                'hedef_sayi': 3,
                'odul_xp': 300,
                'odul_puan': 120,
                'icon': '👑',
                'zorluk': 'zor',
            },
            {
                'isim': '4 Farklı Dersten Çöz',
                'aciklama': '4 farklı dersten soru çözerek çok yönlü ol!',
                'gorev_tipi': 'farkli_ders',
                'hedef_sayi': 4,
                'odul_xp': 180,
                'odul_puan': 70,
                'icon': '🎓',
                'zorluk': 'zor',
            },
        ]

        eklenen = 0
        mevcut = 0
        for gorev_data in gorevler:
            obj, created = GunlukGorevSablonu.objects.get_or_create(
                isim=gorev_data['isim'],
                defaults=gorev_data
            )
            if created:
                eklenen += 1
            else:
                mevcut += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Günlük görev şablonları yüklendi! {eklenen} yeni, {mevcut} mevcut.'
        ))
        self.stdout.write(f'  🟢 Kolay: 5 görev')
        self.stdout.write(f'  🟡 Orta: 5 görev')
        self.stdout.write(f'  🔴 Zor: 5 görev')
