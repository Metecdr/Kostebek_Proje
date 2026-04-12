"""
2026 YKS müfredatına göre konu listesini veritabanına yükler.
Kullanım: python manage.py yks_konulari_yukle
"""
from django.core.management.base import BaseCommand
from quiz.models import Konu


YKS_KONULARI = {
    'turkce': [
        'Sözcükte Anlam', 'Cümlede Anlam', 'Paragraf', 'Ses Bilgisi',
        'Yazım Kuralları', 'Noktalama İşaretleri', 'Sözcük Yapısı',
        'Sözcük Türleri', 'Fiiller', 'Cümlenin Ögeleri', 'Cümle Türleri',
        'Anlatım Bozukluğu',
    ],
    'matematik': [
        # Temel Matematik
        'Temel Kavramlar', 'Sayı Basamakları', 'Bölme ve Bölünebilme',
        'EBOB-EKOK', 'Rasyonel Sayılar', 'Basit Eşitsizlikler', 'Mutlak Değer',
        'Üslü Sayılar', 'Köklü Sayılar', 'Çarpanlara Ayırma', 'Oran Orantı',
        'Denklem Çözme', 'Problemler', 'Kümeler', 'Mantık', 'Fonksiyonlar',
        'Polinomlar', '2. Dereceden Denklemler', 'Permütasyon-Kombinasyon',
        'Olasılık', 'Veri-İstatistik',
        # Geometri
        'Doğruda Açı', 'Üçgende Açı', 'Özel Üçgenler', 'Açıortay',
        'Kenarortay', 'Üçgende Eşlik-Benzerlik', 'Açı-Kenar Bağıntıları',
        'Üçgende Alan', 'Çokgenler', 'Dörtgenler', 'Çember-Daire',
        'Analitik Geometri', 'Katı Cisimler',
        # AYT Ek Konular
        'Karmaşık Sayılar', '2. Dereceden Eşitsizlikler', 'Parabol',
        'Trigonometri', 'Logaritma', 'Diziler', 'Limit', 'Türev', 'İntegral',
        'Dönüşüm Geometrisi', 'Çemberin Analitiği',
    ],
    'fizik': [
        # TYT Fizik
        'Fizik Bilimine Giriş', 'Madde ve Özellikleri', 'Hareket ve Kuvvet',
        'İş-Güç-Enerji', 'Isı-Sıcaklık-Genleşme', 'Basınç',
        'Kaldırma Kuvveti', 'Elektrostatik', 'Elektrik-Manyetizma',
        'Dalgalar', 'Optik',
        # AYT Fizik
        'Vektörler', 'Kuvvet-Tork-Denge', 'Kütle Merkezi', 'Basit Makineler',
        "Newton'un Yasaları", 'Atışlar', 'İtme-Momentum',
        'Elektrik Alan-Potansiyel', 'Manyetik Alan',
        'İndüksiyon-Alternatif Akım', 'Döngüsel Hareket',
        'Kütle Çekim-Kepler', 'Basit Harmonik Hareket', 'Dalga Mekaniği',
        'Atom Fiziği', 'Modern Fizik',
    ],
    'kimya': [
        # TYT Kimya
        'Kimya Bilimi', 'Atom ve Periyodik Sistem',
        'Kimyasal Türler Arası Etkileşimler', 'Maddenin Halleri',
        'Doğa ve Kimya', 'Kimyanın Temel Kanunları', 'Kimyasal Hesaplamalar',
        'Karışımlar', 'Asit-Baz-Tuz', 'Kimya Her Yerde',
        # AYT Kimya
        'Modern Atom Teorisi', 'Gazlar', 'Sıvı Çözeltiler',
        'Kimyasal Tepkimelerde Enerji', 'Kimyasal Tepkime Hızı',
        'Kimyasal Denge', 'Asit-Baz Dengesi', 'Çözünürlük Dengesi',
        'Kimya ve Elektrik', 'Organik Kimya', 'Enerji Kaynakları',
    ],
    'biyoloji': [
        # TYT Biyoloji
        'Canlıların Ortak Özellikleri', 'Temel Bileşenler',
        'Hücre ve Organelleri', 'Hücre Zarından Madde Geçişi',
        'Canlıların Sınıflandırılması', 'Mitoz ve Eşeysiz Üreme',
        'Mayoz ve Eşeyli Üreme', 'Kalıtım', 'Ekosistem Ekolojisi',
        'Güncel Çevre Sorunları',
        # AYT Biyoloji
        'Sinir Sistemi', 'Endokrin Sistem', 'Duyu Organları',
        'Destek-Hareket Sistemi', 'Sindirim Sistemi',
        'Dolaşım-Bağışıklık Sistemi', 'Solunum Sistemi', 'Üriner Sistem',
        'Üreme Sistemi', 'Komünite-Popülasyon Ekolojisi',
        'Nükleik Asitler-Protein Sentezi', 'Canlılarda Enerji Dönüşümleri',
        'Bitki Biyolojisi',
    ],
    'tarih': [
        # TYT Tarih
        'Tarih ve Zaman', 'İnsanlığın İlk Dönemleri', 'Türk Dünyası',
        'İslam Medeniyeti', 'Osmanlı Siyaseti ve Medeniyeti',
        'Milli Mücadele', 'Atatürkçülük',
        # AYT Tarih
        'Osmanlı Klasik Dönemi', 'Osmanlı Duraklama ve Gerileme',
        'Osmanlı Çöküş Dönemi', 'İki Savaş Arası Dönem',
        'II. Dünya Savaşı Süreci ve Sonrası', 'Toplumsal Devrim Çağı',
        '21. Yüzyıl Dünya Siyaseti',
    ],
    'cografya': [
        # TYT Coğrafya
        'Doğa ve İnsan', "Dünya'nın Şekli ve Hareketleri", 'Coğrafi Konum',
        'Harita Bilgisi', 'İklim Bilgisi', 'Tektonik Oluşum',
        'Jeolojik Zamanlar', 'İç-Dış Kuvvetler', 'Kayaçlar',
        'Nüfus', 'Göç', 'Ekonomik Faaliyetler', 'Çevre ve Doğal Afetler',
        # AYT Coğrafya
        'Ekosistemlerin Özellikleri', 'Biyoçeşitlilik',
        'Enerji Akışı-Madde Döngüleri', 'Nüfus Politikaları', 'Yerleşmeler',
        'Ekonomik Faaliyetler-Doğal Kaynaklar', 'Türkiye Ekonomisi',
        'Hizmet Sektörü', 'Küresel Ticaret', 'Turizm', 'Jeopolitik',
        'Çevre Sorunları', 'Sürdürülebilirlik',
    ],
    'felsefe': [
        # TYT Felsefe
        "Felsefenin Konusu", 'Bilgi Felsefesi', 'Varlık Felsefesi',
        'Ahlak Felsefesi', 'Sanat Felsefesi', 'Din Felsefesi',
        'Siyaset Felsefesi', 'Bilim Felsefesi', 'Tarihsel Dönem Felsefeleri',
        # AYT Felsefe / Sosyal Bilimler
        'Klasik Mantık', 'Sembolik Mantık',
        'Psikolojiye Giriş', 'Psikolojide Temel Süreçler',
        'Öğrenme ve Bellek', 'Düşünme ve Zeka', 'Ruh Sağlığı',
        'Sosyolojiye Giriş', 'Birey ve Toplum', 'Toplumsal Yapı',
        'Toplumsal Değişme', 'Kültür ve Medeniyet', 'Sosyal Kurumlar',
    ],
    'edebiyat': [
        # AYT Edebiyat
        'Anlam Bilgisi', 'Şiir Bilgisi', 'Söz Sanatları',
        'İslam Öncesi Türk Edebiyatı', 'Halk Edebiyatı', 'Divan Edebiyatı',
        'Tanzimat Edebiyatı', 'Servet-i Fünun Edebiyatı', 'Fecr-i Ati',
        'Milli Edebiyat Dönemi', 'Cumhuriyet Dönemi Edebiyatı',
        'Dünya Edebiyatı', 'Edebi Akımlar', 'Roman Özetleri',
    ],
}


class Command(BaseCommand):
    help = '2026 YKS müfredatına göre konuları veritabanına yükler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--temizle',
            action='store_true',
            help='Mevcut konuları sil ve yeniden yükle',
        )

    def handle(self, *args, **options):
        if options['temizle']:
            silinen = Konu.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Mevcut konular silindi.'))

        toplam_eklenen = 0
        toplam_atlanan = 0

        for ders, konular in YKS_KONULARI.items():
            for sira, konu_isim in enumerate(konular, start=1):
                obj, created = Konu.objects.get_or_create(
                    ders=ders,
                    isim=konu_isim,
                    defaults={'sira': sira}
                )
                if created:
                    toplam_eklenen += 1
                else:
                    toplam_atlanan += 1

            self.stdout.write(f'  ✓ {ders}: {len(konular)} konu')

        self.stdout.write(self.style.SUCCESS(
            f'\nToplam: {toplam_eklenen} konu eklendi, {toplam_atlanan} konu zaten vardı.'
        ))
