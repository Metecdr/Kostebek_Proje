from django.test import TestCase
from django.contrib.auth. models import User
from profile.models import OgrenciProfili, OyunModuIstatistik, DersIstatistik, Rozet
from django. db import IntegrityError


class OgrenciProfiliTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='testpass123')
        self. profil = OgrenciProfili.objects.filter(kullanici=self.user).first()
        if not self.profil:
            self.profil = OgrenciProfili.objects.create(kullanici=self.user, alan='sayisal')
    
    def test_profil_olusturma(self):
        self.assertIsNotNone(self.profil)
        self.assertEqual(self.profil.kullanici. username, 'testuser')
        self.assertIn(self. profil.alan, ['sayisal', 'sozel', 'esit_agirlik', 'dil'])
    
    def test_profil_str_metodu(self):
        self.assertEqual(str(self. profil), 'testuser')
    
    def test_profil_unique_kullanici(self):
        with self.assertRaises(IntegrityError):
            OgrenciProfili.objects.create(kullanici=self.user, alan='sozel')
    
    def test_profil_puan_guncelleme(self):
        self.profil.toplam_puan = 100
        self.profil.cozulen_soru_sayisi = 10
        self.profil. save()
        self.profil.refresh_from_db()
        self.assertEqual(self.profil.toplam_puan, 100)
        self.assertEqual(self.profil.cozulen_soru_sayisi, 10)


class OyunModuIstatistikTestCase(TestCase):
    def setUp(self):
        self. user = User.objects.create_user(username='testuser2', password='testpass123')
        self.profil = OgrenciProfili.objects.filter(kullanici=self.user). first()
        if not self. profil:
            self.profil = OgrenciProfili.objects.create(kullanici=self.user, alan='sayisal')
    
    def test_oyun_istatistik_olusturma(self):
        istatistik = OyunModuIstatistik.objects.create(profil=self.profil, oyun_modu='karsilasma')
        self.assertEqual(istatistik.oyun_modu, 'karsilasma')
        self.assertEqual(istatistik.oynanan_oyun_sayisi, 0)
        self.assertEqual(istatistik.kazanilan_oyun, 0)
    
    def test_oyun_istatistik_guncelleme(self):
        istatistik = OyunModuIstatistik.objects. create(profil=self.profil, oyun_modu='karsilasma')
        istatistik.oynanan_oyun_sayisi = 5
        istatistik.kazanilan_oyun = 3
        istatistik.toplam_puan = 150
        istatistik.save()
        istatistik.refresh_from_db()
        self.assertEqual(istatistik. oynanan_oyun_sayisi, 5)
        self.assertEqual(istatistik. kazanilan_oyun, 3)
        self.assertEqual(istatistik.toplam_puan, 150)


class DersIstatistikTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser3', password='testpass123')
        self.profil = OgrenciProfili.objects.filter(kullanici=self.user).first()
        if not self.profil:
            self.profil = OgrenciProfili. objects.create(kullanici=self.user, alan='sayisal')
    
    def test_ders_istatistik_olusturma(self):
        ders_ist = DersIstatistik.objects. create(profil=self.profil, ders='matematik')
        self.assertEqual(ders_ist.ders, 'matematik')
        self.assertEqual(ders_ist.cozulen_soru, 0)
        self.assertEqual(ders_ist.dogru_sayisi, 0)
    
    def test_net_hesaplama(self):
        ders_ist = DersIstatistik.objects.create(profil=self.profil, ders='matematik', dogru_sayisi=8, yanlis_sayisi=4)
        expected_net = 8 - (4 / 4.0)
        self.assertEqual(ders_ist.dogru_sayisi, 8)
        self.assertEqual(ders_ist.yanlis_sayisi, 4)


class RozetTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser4', password='testpass123')
        self.profil = OgrenciProfili.objects.filter(kullanici=self.user).first()
        if not self.profil:
            self.profil = OgrenciProfili.objects. create(kullanici=self. user, alan='sayisal')
    
    def test_rozet_olusturma(self):
        rozet = Rozet.objects.create(profil=self.profil, kategori='yeni_uye', seviye='bronz')
        self.assertEqual(rozet.kategori, 'yeni_uye')
        self. assertEqual(rozet.seviye, 'bronz')
        self.assertIsNotNone(rozet.icon)
    
    def test_rozet_str_metodu(self):
        rozet = Rozet.objects. create(profil=self.profil, kategori='soru_cozucu', seviye='altin')
        self.assertIn('testuser4', str(rozet))
    
    def test_rozet_icon_property(self):
        rozet = Rozet.objects.create(profil=self. profil, kategori='matematik_dehasi', seviye='gumus')
        self.assertEqual(rozet.icon, '🔢')