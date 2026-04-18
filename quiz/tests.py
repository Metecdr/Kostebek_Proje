from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
from profile.models import OgrenciProfili
from quiz.models import Soru, Cevap, KarsilasmaOdasi, BulBakalimOyun, TabuOyun, Konu
import json


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


# ==================== KARŞILAŞMA BACKEND TESTS ====================

def _make_user(username):
    user = User.objects.create_user(username=username, password='test1234')
    profil = OgrenciProfili.objects.filter(kullanici=user).first()
    if not profil:
        OgrenciProfili.objects.create(kullanici=user, alan='sayisal')
    return user


def _make_soru(ders='fizik'):
    konu, _ = Konu.objects.get_or_create(isim=f'Konu_{ders}', ders=ders)
    soru = Soru.objects.create(metin='Test soru?', ders=ders, konu=konu, karsilasmada_cikar=True)
    Cevap.objects.create(soru=soru, metin='Doğru', dogru_mu=True)
    Cevap.objects.create(soru=soru, metin='Yanlış', dogru_mu=False)
    return soru


class KarsilasmaGetCacheHeaderTest(TestCase):
    """Cache-Control: no-store header on polling endpoints."""

    def setUp(self):
        self.client = Client()
        self.user1 = _make_user('cache_u1')
        self.user2 = _make_user('cache_u2')
        self.soru = _make_soru()
        self.oda = KarsilasmaOdasi.objects.create(
            oyuncu1=self.user1,
            oyuncu2=self.user2,
            secilen_ders='fizik',
            sinav_tipi='AYT',
            oyun_durumu='oynaniyor',
            aktif_soru=self.soru,
            aktif_soru_no=1,
            toplam_soru=5,
            soru_baslangic_zamani=timezone.now(),
        )

    def test_durum_get_no_store_header(self):
        self.client.login(username='cache_u1', password='test1234')
        url = reverse('karsilasma_durum_guncelle', args=[str(self.oda.oda_id)])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get('Cache-Control'), 'no-store')

    def test_bekleme_durum_no_store_header(self):
        oda = KarsilasmaOdasi.objects.create(
            oyuncu1=self.user1,
            secilen_ders='fizik',
            sinav_tipi='AYT',
            oyun_durumu='bekleniyor',
            oda_kodu='ABCDEF',
        )
        self.client.login(username='cache_u1', password='test1234')
        url = reverse('karsilasma_oda_bekleme_durum', args=['ABCDEF'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get('Cache-Control'), 'no-store')


class KarsilasmaRedirectBeklemeTest(TestCase):
    """redirect_bekleme JSON returned when game is waiting and oda_kodu is set."""

    def setUp(self):
        self.client = Client()
        self.user1 = _make_user('redir_u1')
        self.user2 = _make_user('redir_u2')
        self.oda = KarsilasmaOdasi.objects.create(
            oyuncu1=self.user1,
            oyuncu2=self.user2,
            secilen_ders='fizik',
            sinav_tipi='AYT',
            oyun_durumu='bekleniyor',
            oda_kodu='REDIR1',
        )

    def test_redirect_bekleme_returned(self):
        self.client.login(username='redir_u1', password='test1234')
        url = reverse('karsilasma_durum_guncelle', args=[str(self.oda.oda_id)])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('redirect_bekleme', data)
        self.assertIn('REDIR1', data['redirect_bekleme'])

    def test_no_redirect_without_oda_kodu(self):
        oda = KarsilasmaOdasi.objects.create(
            oyuncu1=self.user1,
            secilen_ders='fizik',
            sinav_tipi='AYT',
            oyun_durumu='bekleniyor',
        )
        self.client.login(username='redir_u1', password='test1234')
        url = reverse('karsilasma_durum_guncelle', args=[str(oda.oda_id)])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertNotIn('redirect_bekleme', data)


class KarsilasmaPostJsonErrorTest(TestCase):
    """Malformed JSON body in POST returns 400, not 500."""

    def setUp(self):
        self.client = Client()
        self.user1 = _make_user('json_u1')
        self.user2 = _make_user('json_u2')
        self.soru = _make_soru()
        self.oda = KarsilasmaOdasi.objects.create(
            oyuncu1=self.user1,
            oyuncu2=self.user2,
            secilen_ders='fizik',
            sinav_tipi='AYT',
            oyun_durumu='oynaniyor',
            aktif_soru=self.soru,
            aktif_soru_no=1,
            toplam_soru=5,
            soru_baslangic_zamani=timezone.now(),
        )

    def test_malformed_json_returns_400(self):
        self.client.login(username='json_u1', password='test1234')
        url = reverse('karsilasma_durum_guncelle', args=[str(self.oda.oda_id)])
        resp = self.client.post(url, data='not json{{', content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.content)
        self.assertIn('error', data)


class KarsilasmaRoundTransitionTest(TestCase):
    """Round transition: after both answer, 3s wait, new question assigned."""

    def setUp(self):
        self.client = Client()
        self.user1 = _make_user('round_u1')
        self.user2 = _make_user('round_u2')
        self.soru = _make_soru()
        self.soru2 = _make_soru()

    def test_round_transition_fires_after_3s(self):
        past = timezone.now() - timezone.timedelta(seconds=4)
        oda = KarsilasmaOdasi.objects.create(
            oyuncu1=self.user1,
            oyuncu2=self.user2,
            secilen_ders='fizik',
            sinav_tipi='AYT',
            oyun_durumu='oynaniyor',
            aktif_soru=self.soru,
            aktif_soru_no=1,
            toplam_soru=3,
            oyuncu1_cevapladi=True,
            oyuncu2_cevapladi=True,
            round_bekleme_durumu=True,
            round_bitis_zamani=past,
            soru_baslangic_zamani=past,
        )
        self.client.login(username='round_u1', password='test1234')
        url = reverse('karsilasma_durum_guncelle', args=[str(oda.oda_id)])

        with patch('quiz.views_karsilasma.get_random_soru_by_ders', return_value=self.soru2):
            resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        oda.refresh_from_db()
        self.assertEqual(oda.aktif_soru_no, 2)
        self.assertFalse(oda.round_bekleme_durumu)
        self.assertFalse(oda.oyuncu1_cevapladi)
        self.assertFalse(oda.oyuncu2_cevapladi)

    def test_game_ends_at_last_question(self):
        past = timezone.now() - timezone.timedelta(seconds=4)
        oda = KarsilasmaOdasi.objects.create(
            oyuncu1=self.user1,
            oyuncu2=self.user2,
            secilen_ders='fizik',
            sinav_tipi='AYT',
            oyun_durumu='oynaniyor',
            aktif_soru=self.soru,
            aktif_soru_no=5,
            toplam_soru=5,
            oyuncu1_cevapladi=True,
            oyuncu2_cevapladi=True,
            round_bekleme_durumu=True,
            round_bitis_zamani=past,
            soru_baslangic_zamani=past,
        )
        self.client.login(username='round_u1', password='test1234')
        url = reverse('karsilasma_durum_guncelle', args=[str(oda.oda_id)])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        oda.refresh_from_db()
        self.assertEqual(oda.oyun_durumu, 'bitti')


class KarsilasmaGetRandomSoruTest(TestCase):
    """get_random_soru_by_ders handles deleted-soru gracefully."""

    def setUp(self):
        self.soru = _make_soru('kimya')

    def test_returns_soru_normally(self):
        from quiz.helpers import get_random_soru_by_ders
        from django.core.cache import cache
        cache.clear()
        result = get_random_soru_by_ders('kimya')
        self.assertIsNotNone(result)
        self.assertEqual(result.ders, 'kimya')

    def test_handles_stale_cache_gracefully(self):
        from quiz.helpers import get_random_soru_by_ders
        from django.core.cache import cache
        cache.clear()
        # Put a non-existent ID in cache
        cache.set('karsilasma_soru_ids_kimya', [999999999], 300)
        result = get_random_soru_by_ders('kimya')
        # Should not raise, should either return a soru or None
        # (returns None only if no kimya sorusu exists at all, which is False)
        self.assertIsNotNone(result)