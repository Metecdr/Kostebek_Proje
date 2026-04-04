"""
Mağaza ürün fiyatlarını toplu güncelleme komutu.

Kullanım:
  python manage.py fiyat_guncelle --carpan 3      # Tüm fiyatları 3x yap
  python manage.py fiyat_guncelle --min 150        # Minimum fiyatı 150'ye çek
  python manage.py fiyat_guncelle --carpan 3 --min 150  # İkisini birden uygula
  python manage.py fiyat_guncelle --listele        # Mevcut fiyatları listele
"""

from django.core.management.base import BaseCommand
from magaza.models import MagazaUrun


class Command(BaseCommand):
    help = 'Mağaza ürün fiyatlarını toplu güncelle'

    def add_arguments(self, parser):
        parser.add_argument(
            '--carpan', type=float, default=None,
            help='Fiyat çarpanı (örn: 3 = tüm fiyatları 3 katına çıkar)'
        )
        parser.add_argument(
            '--min', type=int, default=None,
            help='Minimum fiyat (bu değerin altındaki fiyatlar bu değere çekilir)'
        )
        parser.add_argument(
            '--listele', action='store_true',
            help='Mevcut fiyatları listele (değişiklik yapmaz)'
        )

    def handle(self, *args, **options):
        urunler = MagazaUrun.objects.all().order_by('kategori', 'fiyat')

        if options['listele']:
            self.stdout.write('\n📦 MEVCUT MAĞAZA FİYATLARI:\n')
            self.stdout.write(f'{"Kategori":<12} {"Ürün":<30} {"Fiyat":>8}')
            self.stdout.write('-' * 55)
            for u in urunler:
                self.stdout.write(
                    f'{u.get_kategori_display():<12} {u.icon} {u.isim:<27} {u.fiyat:>6} puan'
                )
            self.stdout.write(f'\nToplam {urunler.count()} ürün')
            return

        if not options['carpan'] and not options['min']:
            self.stdout.write(self.style.WARNING(
                'Parametre belirtin: --carpan veya --min (veya --listele)'
            ))
            return

        guncellenen = 0
        self.stdout.write('\n💰 FİYAT GÜNCELLEMESİ:\n')

        for urun in urunler:
            eski_fiyat = urun.fiyat
            yeni_fiyat = eski_fiyat

            if options['carpan']:
                yeni_fiyat = int(yeni_fiyat * options['carpan'])

            if options['min'] and yeni_fiyat < options['min']:
                yeni_fiyat = options['min']

            if yeni_fiyat != eski_fiyat:
                urun.fiyat = yeni_fiyat
                urun.save()
                guncellenen += 1
                self.stdout.write(
                    f'  {urun.icon} {urun.isim}: {eski_fiyat} → {yeni_fiyat} puan'
                )

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ {guncellenen} ürün fiyatı güncellendi!'
        ))
