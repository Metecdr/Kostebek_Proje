"""
KarsilasmaConsumer — WebSocket tüketicisi
Karşılaşma oyununun gerçek zamanlı iletişimini yönetir.
Polling (500ms GET) → WebSocket (anlık push) geçişi.
"""
import json
import logging
import threading

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class KarsilasmaConsumer(WebsocketConsumer):

    # ─────────────────────────────────────────────
    # Bağlantı
    # ─────────────────────────────────────────────

    def connect(self):
        self.oda_id = self.scope['url_route']['kwargs']['oda_id']
        self.group_name = f"karsilasma_{self.oda_id}"
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )
        self.accept()

        # İlk state'i gönder
        state = self._get_game_state()
        self.send(text_data=json.dumps(state))
        logger.info(f"WS bağlandı: {self.user.username} → oda {self.oda_id}")

    def disconnect(self, close_code):
        from quiz.models import KarsilasmaOdasi

        try:
            oda = KarsilasmaOdasi.objects.get(oda_id=self.oda_id)
            if oda.oyun_durumu == 'oynaniyor':
                with transaction.atomic():
                    oda_locked = KarsilasmaOdasi.objects.select_for_update().get(
                        oda_id=self.oda_id
                    )
                    if oda_locked.oyun_durumu == 'oynaniyor':
                        oda_locked.oyun_durumu = 'bitti'
                        oda_locked.bitis_zamani = timezone.now()
                        oda_locked.save(update_fields=['oyun_durumu', 'bitis_zamani'])

                # Rakibe bildir
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    {
                        'type': 'game_state_update',
                        'state': {
                            'rakip_terk_etti': True,
                            'oyun_durumu': 'bitti',
                        },
                    },
                )
                logger.info(f"WS bağlantı kesildi (oyun bitti): {self.user.username}")
        except Exception as e:
            logger.error(f"Consumer disconnect hatası: {e}", exc_info=True)

        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )

    # ─────────────────────────────────────────────
    # Mesaj yönlendirme
    # ─────────────────────────────────────────────

    def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        action = data.get('action', '')

        if action == 'ping':
            self._update_ping()

        elif action == 'cevap_gonder':
            cevap_id = data.get('cevap_id')
            if cevap_id is not None:
                self._handle_answer(int(cevap_id))

        elif action == 'get_state':
            # Client state talep ederse (round transition kontrolü için)
            state = self._get_game_state()
            self.send(text_data=json.dumps(state))

    # ─────────────────────────────────────────────
    # Ping
    # ─────────────────────────────────────────────

    def _update_ping(self):
        from quiz.models import KarsilasmaOdasi
        try:
            oda = KarsilasmaOdasi.objects.only(
                'oda_id', 'oyuncu1_id', 'oyuncu2_id'
            ).get(oda_id=self.oda_id)
            is_oyuncu1 = (oda.oyuncu1_id == self.user.id)
            field = 'oyuncu1_son_ping' if is_oyuncu1 else 'oyuncu2_son_ping'
            KarsilasmaOdasi.objects.filter(oda_id=self.oda_id).update(
                **{field: timezone.now()}
            )
        except Exception as e:
            logger.error(f"Ping güncelleme hatası: {e}")

    # ─────────────────────────────────────────────
    # Cevap işleme
    # ─────────────────────────────────────────────

    def _handle_answer(self, cevap_id):
        from quiz.models import KarsilasmaOdasi, Cevap, KullaniciCevap
        from quiz.helpers import update_stats_with_combo
        from profile.xp_helper import soru_cozuldu_xp
        from profile.gorev_helper import gorev_ilerleme_guncelle, calisma_kaydi_guncelle
        from profile.rozet_kontrol import rozet_kontrol_yap

        her_ikisi_cevapladi = False

        try:
            with transaction.atomic():
                oda = KarsilasmaOdasi.objects.select_for_update().select_related(
                    'oyuncu1', 'oyuncu2', 'aktif_soru', 'ilk_dogru_cevaplayan'
                ).get(oda_id=self.oda_id)

                if oda.oyun_durumu != 'oynaniyor':
                    return

                # Anti-cheat: minimum 0.4 saniye
                if oda.soru_baslangic_zamani:
                    gecen = (timezone.now() - oda.soru_baslangic_zamani).total_seconds()
                    if gecen < 0.4:
                        logger.warning(
                            f"Anti-cheat tetiklendi: {self.user.username} ({gecen:.2f}s)"
                        )
                        return

                try:
                    cevap_obj = Cevap.objects.select_related('soru').get(id=cevap_id)
                except Cevap.DoesNotExist:
                    return

                if not oda.aktif_soru or cevap_obj.soru_id != oda.aktif_soru_id:
                    return

                is_oyuncu1 = (oda.oyuncu1_id == self.user.id)

                if (is_oyuncu1 and oda.oyuncu1_cevapladi) or \
                   (not is_oyuncu1 and oda.oyuncu2_cevapladi):
                    return  # Zaten cevaplandı

                dogru_mu = cevap_obj.dogru_mu
                cevap_zamani = timezone.now()

                if is_oyuncu1:
                    oda.oyuncu1_cevapladi = True
                    oda.oyuncu1_cevap_zamani = cevap_zamani
                else:
                    oda.oyuncu2_cevapladi = True
                    oda.oyuncu2_cevap_zamani = cevap_zamani

                # Skor + combo güncelle
                update_stats_with_combo(self.user, oda, cevap_obj, is_oyuncu1)

                # İlk doğru cevaplayan bonusu
                if dogru_mu and oda.ilk_dogru_cevaplayan is None:
                    oda.ilk_dogru_cevaplayan = self.user

                # DB'ye kaydet (duplicate korumalı)
                try:
                    KullaniciCevap.objects.get_or_create(
                        kullanici=self.user,
                        oda=oda,
                        soru=oda.aktif_soru,
                        defaults={'verilen_cevap': cevap_obj, 'dogru_mu': dogru_mu},
                    )
                except Exception as e:
                    logger.error(f"KullaniciCevap kayıt hatası: {e}")

                # XP + Görev + Çalışma takvimi
                try:
                    profil = self.user.profil
                    soru_cozuldu_xp(profil, dogru_mu)
                    kazanilan_xp = 5 if dogru_mu else 1
                    gorev_ilerleme_guncelle(profil, 'soru_coz', 1)
                    if dogru_mu:
                        gorev_ilerleme_guncelle(profil, 'dogru_cevap', 1)
                    calisma_kaydi_guncelle(
                        profil,
                        cozulen=1,
                        dogru=1 if dogru_mu else 0,
                        yanlis=0 if dogru_mu else 1,
                        xp=kazanilan_xp,
                    )
                    if profil.cozulen_soru_sayisi % 10 == 0:
                        try:
                            rozet_kontrol_yap(profil)
                        except Exception:
                            pass
                except Exception as e:
                    logger.error(f"XP/Görev consumer hatası: {e}")

                # Her iki oyuncu cevapladıysa round bekleme başlat
                her_ikisi_cevapladi = (
                    oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi
                )
                if her_ikisi_cevapladi and not oda.round_bekleme_durumu:
                    oda.round_bekleme_durumu = True
                    oda.round_bitis_zamani = timezone.now()

                oda.save()

        except Exception as e:
            logger.error(f"_handle_answer hatası: {e}", exc_info=True)
            return

        # State'i tüm gruba broadcast et
        self._broadcast_state()

        # 3.2 saniye sonra round advance tetikle
        if her_ikisi_cevapladi:
            t = threading.Timer(3.2, self._advance_round)
            t.daemon = True
            t.start()

    # ─────────────────────────────────────────────
    # Round geçişi
    # ─────────────────────────────────────────────

    def _advance_round(self):
        """3 saniye sonra bir thread'de çalışır, bir sonraki soruya geçer."""
        from quiz.models import KarsilasmaOdasi
        from quiz.helpers import get_random_soru_by_ders

        try:
            with transaction.atomic():
                oda = KarsilasmaOdasi.objects.select_for_update().get(
                    oda_id=self.oda_id
                )

                if oda.oyun_durumu != 'oynaniyor' or not oda.round_bekleme_durumu:
                    return

                if oda.aktif_soru_no >= oda.toplam_soru:
                    # Oyun bitti
                    oda.oyun_durumu = 'bitti'
                    oda.bitis_zamani = timezone.now()
                    oda.save(update_fields=['oyun_durumu', 'bitis_zamani'])
                    logger.info(f"✅ Oyun tamamlandı: {self.oda_id}")
                else:
                    # Yeni soru
                    yeni_soru = get_random_soru_by_ders(oda.secilen_ders)
                    if yeni_soru:
                        oda.aktif_soru = yeni_soru
                        oda.aktif_soru_no += 1
                        oda.soru_baslangic_zamani = timezone.now()
                        oda.oyuncu1_cevapladi = False
                        oda.oyuncu2_cevapladi = False
                        oda.oyuncu1_cevap_zamani = None
                        oda.oyuncu2_cevap_zamani = None
                        oda.ilk_dogru_cevaplayan = None
                        oda.round_bekleme_durumu = False
                        oda.round_bitis_zamani = None
                        oda.save()
                        logger.info(
                            f"❓ Yeni soru: {oda.aktif_soru_no}/{oda.toplam_soru} "
                            f"(oda {self.oda_id})"
                        )
                    else:
                        oda.oyun_durumu = 'bitti'
                        oda.save(update_fields=['oyun_durumu'])

            self._broadcast_state()

        except Exception as e:
            logger.error(f"_advance_round hatası: {e}", exc_info=True)

    # ─────────────────────────────────────────────
    # State
    # ─────────────────────────────────────────────

    def _broadcast_state(self):
        state = self._get_game_state()
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {'type': 'game_state_update', 'state': state},
        )

    def _get_game_state(self):
        from quiz.models import KarsilasmaOdasi, Cevap

        try:
            oda = KarsilasmaOdasi.objects.select_related(
                'oyuncu1', 'oyuncu2', 'aktif_soru'
            ).get(oda_id=self.oda_id)
        except KarsilasmaOdasi.DoesNotExist:
            return {'error': 'Oda bulunamadı'}

        soru_obj = oda.aktif_soru
        cevaplar = []
        if soru_obj:
            cevaplar = [
                {'id': c.id, 'metin': c.metin, 'dogru_mu': c.dogru_mu}
                for c in Cevap.objects.filter(soru=soru_obj).order_by('id')
            ]

        kalan_sure = 0
        if oda.round_bekleme_durumu and oda.round_bitis_zamani:
            gecen = (timezone.now() - oda.round_bitis_zamani).total_seconds()
            kalan_sure = max(0, round(3 - gecen, 1))

        return {
            'oyuncu1_skor': oda.oyuncu1_skor,
            'oyuncu2_skor': oda.oyuncu2_skor,
            'oyuncu1_combo': oda.oyuncu1_combo,
            'oyuncu2_combo': oda.oyuncu2_combo,
            'oyuncu1_adi': oda.oyuncu1.username if oda.oyuncu1 else None,
            'oyuncu2_adi': oda.oyuncu2.username if oda.oyuncu2 else None,
            'oyun_durumu': oda.oyun_durumu,
            'soru': soru_obj.metin if soru_obj else None,
            'soru_id': soru_obj.id if soru_obj else None,
            'cevaplar': cevaplar,
            'oyuncu1_cevapladi': oda.oyuncu1_cevapladi,
            'oyuncu2_cevapladi': oda.oyuncu2_cevapladi,
            'aktif_soru_no': oda.aktif_soru_no,
            'toplam_soru': oda.toplam_soru,
            'round_bekleme': oda.round_bekleme_durumu,
            'kalan_sure': kalan_sure,
            'rakip_terk_etti': False,
        }

    def game_state_update(self, event):
        """Channel group'tan gelen state mesajını WebSocket üzerinden client'a ilet."""
        self.send(text_data=json.dumps(event['state']))
