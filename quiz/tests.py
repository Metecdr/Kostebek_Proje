from django.test import TestCase
from django.contrib.auth.models import User
from profile.models import OgrenciProfili
from quiz.models import Soru, Cevap, KarsilasmaOdasi, BulBakalimOyun, TabuOyun, Konu
from django.utils import timezone


class SoruModelTestCase(TestCase):
    def setUp(self):
        self.konu = Konu.objects.create(isim='Temel Matematik', ders='matematik')
        self.soru = Soru.objects.create(metin='Test sorusu? ', ders='matematik', konu=self.konu, karsilasmada_cikar=True, bul_bakalimda_cikar=True)
    
    def test_soru_olusturma(self):
        self.assertEqual(self.soru.metin, 'Test sorusu? ')
        self.assertEqual(self.soru.ders, 'matematik')
        self.assertTrue(self.soru.karsilasmada_cikar)
    
    def test_soru_str_metodu(self):
        soru_str = str(self.soru)
        self.assertIsInstance(soru_str, str)
        self.assertGreater(len(soru_str), 0)


class CevapModelTestCase(TestCase):
    def setUp(self):
        self.konu = Konu.objects.create(isim='Temel İşlemler', ders='matematik')
        self.soru = Soru.objects.create(metin='2+2=?', ders='matematik', konu=self.konu)
        self.dogru_cevap = Cevap.objects.create(soru=self.soru, metin='4', dogru_mu=True)
        self.yanlis_cevap = Cevap.objects.create(soru=self.soru, metin='5', dogru_mu=False)
    
    def test_cevap_olusturma(self):
        self.assertEqual(self.dogru_cevap.metin, '4')
        self.assertTrue(self.dogru_cevap.dogru_mu)
        self.assertFalse(self.yanlis_cevap.dogru_mu)
    
    def test_soru_cevap_iliskisi(self):
        cevaplar = self.soru.cevaplar.all()
        self.assertEqual(cevaplar.count(), 2)


class KarsilasmaOdasiTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='oyuncu1', password='test123')
        self.user2 = User.objects.create_user(username='oyuncu2', password='test123')
        self.profil1 = OgrenciProfili.objects.filter(kullanici=self.user1).first()
        self.profil2 = OgrenciProfili.objects.filter(kullanici=self.user2).first()
        if not self.profil1:
            self.profil1 = OgrenciProfili.objects.create(kullanici=self.user1, alan='sayisal')
        if not self.profil2:
            self.profil2 = OgrenciProfili.objects.create(kullanici=self.user2, alan='sayisal')
    
    def test_oda_olusturma(self):
        oda = KarsilasmaOdasi.objects.create(oyuncu1=self.user1, secilen_ders='matematik', sinav_tipi='ayt')
        self.assertEqual(oda.oyuncu1, self.user1)
        self.assertIsNone(oda.oyuncu2)
        self.assertIn(oda.oyun_durumu, ['bekleniyor', 'oynaniyor', 'bitti'])
        self.assertEqual(oda.secilen_ders, 'matematik')
    
    def test_oda_id_unique(self):
        oda1 = KarsilasmaOdasi.objects.create(oyuncu1=self.user1, secilen_ders='fizik')
        oda2 = KarsilasmaOdasi.objects.create(oyuncu1=self.user2, secilen_ders='kimya')
        self.assertNotEqual(oda1.oda_id, oda2.oda_id)
    
    def test_oyun_baslangic_durumu(self):
        oda = KarsilasmaOdasi.objects.create(oyuncu1=self.user1, secilen_ders='biyoloji')
        self.assertEqual(oda.oyuncu1_skor, 0)
        self.assertEqual(oda.oyuncu2_skor, 0)
        self.assertEqual(oda.oyuncu1_combo, 0)
        self.assertIn(oda.aktif_soru_no, [0, 1])
        self.assertEqual(oda.toplam_soru, 5)


class BulBakalimOyunTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testoyuncu', password='test123')
        self.profil = OgrenciProfili.objects.filter(kullanici=self.user).first()
        if not self.profil:
            self.profil = OgrenciProfili.objects.create(kullanici=self.user, alan='sayisal')
        self.konu1 = Konu.objects.create(isim='Konu 1', ders='matematik')
        self.konu2 = Konu.objects.create(isim='Konu 2', ders='fizik')
        self.soru1 = Soru.objects.create(metin='Soru 1?', ders='matematik', konu=self.konu1, bul_bakalimda_cikar=True)
        self.soru2 = Soru.objects.create(metin='Soru 2?', ders='fizik', konu=self.konu2, bul_bakalimda_cikar=True)
    
    def test_oyun_olusturma(self):
        oyun = BulBakalimOyun.objects.create(oyuncu=self.user, sorular=[self.soru1.id, self.soru2.id])
        self.assertEqual(oyun.oyuncu, self.user)
        self.assertEqual(len(oyun.sorular), 2)
        self.assertIn(oyun.oyun_durumu, ['devam', 'devam_ediyor', 'bitti'])
        self.assertEqual(oyun.dogru_sayisi, 0)
        self.assertEqual(oyun.yanlis_sayisi, 0)
    
    def test_oyun_bitir(self):
        oyun = BulBakalimOyun.objects.create(oyuncu=self.user, sorular=[self.soru1.id])
        oyun.oyun_bitir()
        self.assertEqual(oyun.oyun_durumu, 'bitti')
    
    def test_oyun_id_unique(self):
        oyun1 = BulBakalimOyun.objects.create(oyuncu=self.user, sorular=[self.soru1.id])
        oyun2 = BulBakalimOyun.objects.create(oyuncu=self.user, sorular=[self.soru2.id])
        self.assertNotEqual(oyun1.oyun_id, oyun2.oyun_id)


class TabuOyunTestCase(TestCase):
    def test_tabu_oyun_olusturma(self):
        oyun = TabuOyun.objects.create(takim_a_adi='Takım A', takim_b_adi='Takım B', tur_sayisi=1, aktif_takim='A')
        self.assertEqual(oyun.takim_a_adi, 'Takım A')
        self.assertEqual(oyun.takim_b_adi, 'Takım B')
        self.assertEqual(oyun.aktif_takim, 'A')
        self.assertIn(oyun.oyun_durumu, ['devam', 'devam_ediyor', 'bitti'])
    
    def test_tabu_skor_guncelleme(self):
        oyun = TabuOyun.objects.create(takim_a_adi='Takım X', takim_b_adi='Takım Y')
        oyun.takim_a_skor = 5
        oyun.takim_b_skor = 3
        oyun.save()
        oyun.refresh_from_db()
        self.assertEqual(oyun.takim_a_skor, 5)
        self.assertEqual(oyun.takim_b_skor, 3)