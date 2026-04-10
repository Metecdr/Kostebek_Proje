from django.core.management.base import BaseCommand
from magaza.models import MagazaUrun


class Command(BaseCommand):
    help = 'Mağaza ürünlerini yükler (5 unvan + 5 çerçeve + 5 tema)'

    def handle(self, *args, **options):
        urunler = [
            # ==================== UNVANLAR (200-400 puan) ====================
            {
                'isim': 'Bilge',
                'aciklama': 'Bilgeliğin simgesi olan bu unvan, seni diğerlerinden ayırsın.',
                'kategori': 'unvan',
                'fiyat': 200,
                'icon': '🧙',
                'unvan_metni': 'Bilge',
                'unvan_renk': '#667eea',
            },
            {
                'isim': 'Şampiyon',
                'aciklama': 'Zafer senin ikinci adın! Şampiyon unvanıyla rakiplerini korkut.',
                'kategori': 'unvan',
                'fiyat': 300,
                'icon': '🏆',
                'unvan_metni': 'Şampiyon',
                'unvan_renk': '#ff6b6b',
            },
            {
                'isim': 'Deha',
                'aciklama': 'Parlak zekânı herkese göster! Altın harflerle yazılmış bir unvan.',
                'kategori': 'unvan',
                'fiyat': 350,
                'icon': '🧠',
                'unvan_metni': 'Deha',
                'unvan_renk': '#ffd700',
            },
            {
                'isim': 'Kaşif',
                'aciklama': 'Bilginin sınırlarını keşfet! Meraklı ruhlar için ideal.',
                'kategori': 'unvan',
                'fiyat': 250,
                'icon': '🔭',
                'unvan_metni': 'Kaşif',
                'unvan_renk': '#4caf50',
            },
            {
                'isim': 'Efsane',
                'aciklama': 'Efsaneler asla unutulmaz. Bu unvanla tarihe geç!',
                'kategori': 'unvan',
                'fiyat': 400,
                'icon': '⭐',
                'unvan_metni': 'Efsane',
                'unvan_renk': '#9c27b0',
            },
            # ==================== ÇERÇEVELER (400-700 puan) ====================
            {
                'isim': 'Ateş Çerçeve',
                'aciklama': 'Profilini alevlerle süsle! Rakiplerin gözlerini kamaştır.',
                'kategori': 'cerceve',
                'fiyat': 400,
                'icon': '🔥',
                'cerceve_renk': '#ff6b6b, #ff9800',
                'cerceve_css': 'border: 3px solid #ff6b6b; box-shadow: 0 0 15px rgba(255,107,107,0.6);',
            },
            {
                'isim': 'Buz Çerçeve',
                'aciklama': 'Soğuk ve zarif. Buz mavisi çerçeve ile fark yarat.',
                'kategori': 'cerceve',
                'fiyat': 450,
                'icon': '❄️',
                'cerceve_renk': '#00bcd4, #2196f3',
                'cerceve_css': 'border: 3px solid #00bcd4; box-shadow: 0 0 15px rgba(0,188,212,0.6);',
            },
            {
                'isim': 'Altın Çerçeve',
                'aciklama': 'Altın gibi parlayan lüks bir çerçeve. Premium görünüm.',
                'kategori': 'cerceve',
                'fiyat': 550,
                'icon': '✨',
                'cerceve_renk': '#ffd700, #ff9800',
                'cerceve_css': 'border: 3px solid #ffd700; box-shadow: 0 0 20px rgba(255,215,0,0.7);',
            },
            {
                'isim': 'Gökkuşağı Çerçeve',
                'aciklama': 'Tüm renklerin dansı! En renkli profil senin olsun.',
                'kategori': 'cerceve',
                'fiyat': 600,
                'icon': '🌈',
                'cerceve_renk': '#ff6b6b, #ff9800, #ffd700, #4caf50, #2196f3, #9c27b0',
                'cerceve_css': 'border: 3px solid; border-image: linear-gradient(45deg, #ff6b6b, #ff9800, #ffd700, #4caf50, #2196f3, #9c27b0) 1; box-shadow: 0 0 20px rgba(156,39,176,0.5);',
            },
            {
                'isim': 'Elmas Çerçeve',
                'aciklama': 'Nadide ve değerli. Elmas çerçeve ile statünü göster!',
                'kategori': 'cerceve',
                'fiyat': 700,
                'icon': '💎',
                'cerceve_renk': '#e0f7fa, #80deea, #00bcd4',
                'cerceve_css': 'border: 3px solid #80deea; box-shadow: 0 0 25px rgba(128,222,234,0.8), inset 0 0 10px rgba(128,222,234,0.3);',
            },
            # ==================== TEMALAR (700-1000 puan) ====================
            {
                'isim': 'Gece Modu Pro',
                'aciklama': 'Gelişmiş gece teması. Gözlerini yormadan çalış.',
                'kategori': 'tema',
                'fiyat': 700,
                'icon': '🌙',
                'tema_primary': '#1a1a2e',
                'tema_secondary': '#16213e',
            },
            {
                'isim': 'Orman',
                'aciklama': 'Doğanın huzurunu ekranına taşı. Yeşilin her tonu.',
                'kategori': 'tema',
                'fiyat': 750,
                'icon': '🌲',
                'tema_primary': '#1b5e20',
                'tema_secondary': '#2e7d32',
            },
            {
                'isim': 'Okyanus',
                'aciklama': 'Okyanusun derinliklerine dal. Mavi tonlarında sakin bir tema.',
                'kategori': 'tema',
                'fiyat': 800,
                'icon': '🌊',
                'tema_primary': '#0d47a1',
                'tema_secondary': '#1565c0',
            },
            {
                'isim': 'Gün Batımı',
                'aciklama': 'Sıcak turuncu ve kırmızı tonlarında muhteşem bir tema.',
                'kategori': 'tema',
                'fiyat': 900,
                'icon': '🌅',
                'tema_primary': '#e65100',
                'tema_secondary': '#ff6f00',
            },
            {
                'isim': 'Galaksi',
                'aciklama': 'Yıldızların arasında çalış! En premium tema deneyimi.',
                'kategori': 'tema',
                'fiyat': 1000,
                'icon': '🌌',
                'tema_primary': '#4a148c',
                'tema_secondary': '#6a1b9a',
            },
        ]

        eklenen = 0
        guncellenen = 0
        for urun_data in urunler:
            obj, created = MagazaUrun.objects.get_or_create(
                isim=urun_data['isim'],
                defaults=urun_data
            )
            if created:
                eklenen += 1
            else:
                guncellenen += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Mağaza ürünleri yüklendi! {eklenen} yeni, {guncellenen} mevcut.'
        ))
        self.stdout.write(f'  🏷️ Unvanlar: 5 (200-400 puan)')
        self.stdout.write(f'  🖼️ Çerçeveler: 5 (400-700 puan)')
        self.stdout.write(f'  🎨 Temalar: 5 (700-1000 puan)')
