from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import models, transaction
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from quiz.models import KarsilasmaOdasi, Cevap, Soru, MeydanOkuma, TurnuvaMaci, KullaniciCevap
from quiz.helpers import get_random_soru_by_ders, update_stats_with_combo
from profile.models import OyunModuIstatistik, OgrenciProfili
from profile.rozet_kontrol import rozet_kontrol_yap
from profile.xp_helper import soru_cozuldu_xp, karsilasma_kazanildi_xp, xp_ekle
from profile.gorev_helper import gorev_ilerleme_guncelle, calisma_kaydi_guncelle
from profile.puan_helper import puan_ekle
import json
import logging
import random
import string

logger = logging.getLogger(__name__)


@login_required
def karsilasma_sinav_tipi_secimi(request):
    """Karşılaşma için sınav tipi seçimi (TYT/AYT)"""
    if request.method == 'POST':
        sinav_tipi = request.POST.get('sinav_tipi', 'AYT')
        logger.info(f"Sınav tipi seçildi: {sinav_tipi}, Kullanıcı: {request.user.username}")
        return redirect(f"{reverse('karsilasma_ders_secimi')}?sinav_tipi={sinav_tipi}")
    return render(request, 'quiz/karsilasma_sinav_tipi_secimi.html')


@login_required
def karsilasma_ders_secimi(request):
    """Karşılaşma için ders seçimi"""
    sinav_tipi = request.GET.get('sinav_tipi', 'AYT')

    if sinav_tipi == 'TYT':
        ders_secenekleri = [
            ('turkce', 'Türkçe', '📚'),
            ('fizik', 'Fizik', '⚛️'),
            ('kimya', 'Kimya', '🧪'),
            ('biyoloji', 'Biyoloji', '🧬'),
            ('tarih', 'Tarih', '🏛️'),
            ('cografya', 'Coğrafya', '🌍'),
            ('felsefe', 'Felsefe', '💭'),
            ('karisik_sayisal', 'Karışık Sayısal', '🔢🎲'),
            ('karisik_sozel', 'Karışık Sözel', '📚🎲'),
        ]
    else:
        ders_secenekleri = [
            ('fizik', 'Fizik', '⚛️'),
            ('kimya', 'Kimya', '🧪'),
            ('biyoloji', 'Biyoloji', '🧬'),
            ('edebiyat', 'Edebiyat', '📚'),
            ('tarih', 'Tarih', '🏛️'),
            ('cografya', 'Coğrafya', '🌍'),
            ('felsefe', 'Felsefe', '💭'),
            ('karisik_sayisal', 'Karışık Sayısal (F+K+B)', '🔢🎲'),
            ('karisik_ea', 'Karışık EA (Ed+Tar+Coğ)', '📖🎲'),
            ('karisik_sozel_ayt', 'Karışık Sözel (Din+Fel+Ed+Tar+Coğ)', '📚🎲'),
        ]

    if request.method == 'POST':
        selected_ders = request.POST.get('selected_ders')
        logger.info(f"Ders seçildi: {selected_ders}, Sınav: {sinav_tipi}, User: {request.user.username}")
        return redirect(f"{reverse('karsilasma_rakip_bul')}?ders={selected_ders}&sinav_tipi={sinav_tipi}")

    context = {
        'ders_secenekleri': ders_secenekleri,
        'sinav_tipi': sinav_tipi
    }
    return render(request, 'quiz/karsilasma_ders_secimi.html', context)


@login_required
def karsilasma_oyun(request, oda_id):
    """Karşılaşma oyun sayfası"""
    oda = get_object_or_404(
        KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2', 'aktif_soru'),
        oda_id=oda_id
    )

    if oda.oyuncu1 != request.user and oda.oyuncu2 != request.user:
        messages.error(request, 'Bu odaya erişim yetkiniz yok!')
        return redirect('karsilasma_sinav_tipi_secimi')

    # Oyun henüz başlamadıysa ve oda kodu varsa bekleme sayfasına yönlendir
    if oda.oyun_durumu == 'bekleniyor' and oda.oda_kodu:
        return redirect('karsilasma_oda_bekleme', oda_kodu=oda.oda_kodu)

    is_oyuncu1 = (oda.oyuncu1 == request.user)

    if is_oyuncu1:
        rakip = oda.oyuncu2
        rakip_username = rakip.username if rakip else 'Rakip Bekleniyor...'
        try:
            rakip_seviye = rakip.profil.seviye if rakip else '?'
            rakip_avatar = rakip.profil.avatar if rakip else '🦔'
        except Exception:
            rakip_seviye = '?'
            rakip_avatar = '🦔'
    else:
        rakip = oda.oyuncu1
        rakip_username = rakip.username
        try:
            rakip_seviye = rakip.profil.seviye
            rakip_avatar = rakip.profil.avatar
        except Exception:
            rakip_seviye = '?'
            rakip_avatar = '🦔'

    soru_obj = oda.aktif_soru
    cevaplar = []

    if soru_obj:
        try:
            cevaplar_qs = Cevap.objects.filter(soru=soru_obj).order_by('id')
            cevaplar = [{'id': c.id, 'metin': c.metin, 'dogru_mu': c.dogru_mu} for c in cevaplar_qs]
            logger.info(f"✅ Soru yüklendi: ID={soru_obj.id}, Cevap sayısı={len(cevaplar)}")
        except Exception as e:
            logger.error(f"❌ Cevap yükleme hatası: {e}", exc_info=True)
            cevaplar = []
    else:
        logger.warning(f"⚠️ Aktif soru yok! Oda={oda_id}")

    context = {
        'oda': oda,
        'is_oyuncu1': is_oyuncu1,
        'rakip_username': rakip_username,
        'rakip_seviye': rakip_seviye,
        'rakip_avatar': rakip_avatar,
        'soru': soru_obj,
        'cevaplar': cevaplar,
        'cevaplar_json': json.dumps(cevaplar)
    }
    return render(request, 'quiz/karsilasma_oyun.html', context)


@login_required
@transaction.atomic
def karsilasma_durum_guncelle(request, oda_id):
    """Karşılaşma durum güncelleme - AJAX endpoint"""

    logger.info(f"🔔 Durum kontrolü: Method={request.method}, Oda={oda_id}")

    try:
        # KRİTİK FIX:
        # select_for_update ile birlikte select_related(nullable side) PostgreSQL'de
        # "FOR UPDATE cannot be applied to the nullable side of an outer join" hatası verebilir.
        oda = get_object_or_404(
            KarsilasmaOdasi.objects.select_for_update(),
            oda_id=oda_id
        )

        # ==================== POST: CEVAP GÖNDERME ====================
        if request.method == 'POST':
            data = json.loads(request.body)
            cevap_id = data.get('cevap_id')

            # BOŞ GEÇİŞ
            if cevap_id is None:
                logger.info(f'⏰ BOŞ GEÇİŞ! User={request.user.username}, Oda={oda_id}')

                is_oyuncu1 = (oda.oyuncu1 == request.user)

                if (is_oyuncu1 and oda.oyuncu1_cevapladi) or (not is_oyuncu1 and oda.oyuncu2_cevapladi):
                    return JsonResponse({'error': 'Zaten cevaplandı'}, status=400)

                cevap_zamani = timezone.now()

                if is_oyuncu1:
                    oda.oyuncu1_cevapladi = True
                    oda.oyuncu1_cevap_zamani = cevap_zamani
                    oda.oyuncu1_yanlis += 1
                    oda.oyuncu1_combo = 0
                else:
                    oda.oyuncu2_cevapladi = True
                    oda.oyuncu2_cevap_zamani = cevap_zamani
                    oda.oyuncu2_yanlis += 1
                    oda.oyuncu2_combo = 0

                if oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi and not oda.round_bekleme_durumu:
                    oda.round_bekleme_durumu = True
                    oda.round_bitis_zamani = timezone.now()
                    logger.info(f"⏳ Round bekleme BAŞLATILDI (BOŞ GEÇİŞ)")

                oda.save()

                # Kullanıcı cevabını kaydet (boş geçiş) - duplicate önle
                try:
                    if oda.aktif_soru:
                        if not KullaniciCevap.objects.filter(
                            kullanici=request.user, oda=oda, soru=oda.aktif_soru
                        ).exists():
                            KullaniciCevap.objects.create(
                                kullanici=request.user,
                                oda=oda,
                                soru=oda.aktif_soru,
                                verilen_cevap=None,
                                dogru_mu=False
                            )
                except Exception as e:
                    logger.error(f"KullaniciCevap kayıt hatası (boş geçiş): {e}", exc_info=True)

                # ==================== GÖREV: SORU ÇÖZÜLDÜ (BOŞ GEÇİŞ) ====================
                try:
                    profil = request.user.profil
                    gorev_ilerleme_guncelle(profil, 'soru_coz', 1)
                    calisma_kaydi_guncelle(profil, cozulen=1, yanlis=1)
                except Exception as e:
                    logger.error(f"Görev güncelleme hatası (boş geçiş): {e}", exc_info=True)

                return JsonResponse({
                    'success': True,
                    'dogru_mu': False,
                    'kazanilan_xp': 0,
                    'seviye_atlandi': False,
                    'bos_gecis': True
                })

            # NORMAL CEVAP
            try:
                cevap_obj = Cevap.objects.select_related('soru').get(id=cevap_id)
            except Cevap.DoesNotExist:
                return JsonResponse({'error': 'Geçersiz cevap'}, status=400)

            if not oda.aktif_soru or cevap_obj.soru != oda.aktif_soru:
                return JsonResponse({'error': 'Geçersiz soru'}, status=400)

            is_oyuncu1 = (oda.oyuncu1 == request.user)

            if (is_oyuncu1 and oda.oyuncu1_cevapladi) or (not is_oyuncu1 and oda.oyuncu2_cevapladi):
                return JsonResponse({'error': 'Zaten cevaplandı'}, status=400)

            dogru_mu = cevap_obj.dogru_mu
            seviye_atlandi = False
            yeni_seviye = 0
            yeni_unvan = ''
            kazanilan_xp = 0

            cevap_zamani = timezone.now()
            if is_oyuncu1:
                oda.oyuncu1_cevapladi = True
                oda.oyuncu1_cevap_zamani = cevap_zamani
            else:
                oda.oyuncu2_cevapladi = True
                oda.oyuncu2_cevap_zamani = cevap_zamani

            # İstatistik güncelle
            update_stats_with_combo(request.user, oda, cevap_obj, is_oyuncu1)

            # Kullanıcı cevabını kaydet - duplicate önle
            try:
                if not KullaniciCevap.objects.filter(
                    kullanici=request.user, oda=oda, soru=oda.aktif_soru
                ).exists():
                    KullaniciCevap.objects.create(
                        kullanici=request.user,
                        oda=oda,
                        soru=oda.aktif_soru,
                        verilen_cevap=cevap_obj,
                        dogru_mu=dogru_mu
                    )
            except Exception as e:
                logger.error(f"KullaniciCevap kayıt hatası: {e}", exc_info=True)

            # XP + Görev güncelle
            try:
                profil = request.user.profil
                xp_sonuc = soru_cozuldu_xp(profil, dogru_mu)

                seviye_atlandi = xp_sonuc.get('seviye_atlandi', False)
                yeni_seviye = xp_sonuc.get('yeni_seviye', 0)
                yeni_unvan = xp_sonuc.get('unvan', '')
                kazanilan_xp = 5 if dogru_mu else 1

                # ==================== GÖREV: SORU ÇÖZÜLDÜ ====================
                gorev_ilerleme_guncelle(profil, 'soru_coz', 1)

                # ==================== GÖREV: DOĞRU CEVAP ====================
                if dogru_mu:
                    gorev_ilerleme_guncelle(profil, 'dogru_cevap', 1)

                # ==================== ÇALIŞMA TAKVİMİ ====================
                calisma_kaydi_guncelle(
                    profil,
                    cozulen=1,
                    dogru=1 if dogru_mu else 0,
                    yanlis=0 if dogru_mu else 1,
                    xp=kazanilan_xp,
                )

                # Rozet kontrolü (her 10 soruda bir)
                if profil.cozulen_soru_sayisi % 10 == 0:
                    try:
                        rozet_kontrol_yap(profil)
                    except Exception:
                        pass

            except Exception as e:
                logger.error(f"XP/Görev hatası: {e}", exc_info=True)

            # Round bekleme
            if oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi and not oda.round_bekleme_durumu:
                oda.round_bekleme_durumu = True
                oda.round_bitis_zamani = timezone.now()
                logger.info(f"⏳ Round bekleme BAŞLATILDI")

            oda.save()

            response_data = {
                'success': True,
                'dogru_mu': dogru_mu,
                'kazanilan_xp': kazanilan_xp,
                'seviye_atlandi': seviye_atlandi
            }
            if seviye_atlandi:
                response_data['yeni_seviye'] = yeni_seviye
                response_data['yeni_unvan'] = yeni_unvan

            return JsonResponse(response_data)

        # ==================== GET: DURUM KONTROLÜ ====================
        elif request.method == 'GET':

            # Oyun henüz başlamadıysa ve oda kodu varsa → hazır sayfasına yönlendir
            if oda.oyun_durumu == 'bekleniyor' and oda.oda_kodu:
                return JsonResponse({
                    'redirect_bekleme': reverse('karsilasma_oda_bekleme', args=[oda.oda_kodu])
                })

            # ⏰ SUNUCU TARAFI TIMEOUT: 32 saniye (client 30sn + 2sn tolerans)
            if oda.soru_baslangic_zamani and oda.oyun_durumu == 'oynaniyor':
                soru_gecen = (timezone.now() - oda.soru_baslangic_zamani).total_seconds()
                if soru_gecen >= 32 and not (oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi):
                    if not oda.oyuncu1_cevapladi:
                        oda.oyuncu1_cevapladi = True
                        oda.oyuncu1_cevap_zamani = timezone.now()
                        oda.oyuncu1_yanlis += 1
                        oda.oyuncu1_combo = 0
                        # Timeout boş geçiş cevap kaydı
                        if oda.aktif_soru and not KullaniciCevap.objects.filter(
                            kullanici=oda.oyuncu1, oda=oda, soru=oda.aktif_soru
                        ).exists():
                            KullaniciCevap.objects.create(
                                kullanici=oda.oyuncu1, oda=oda, soru=oda.aktif_soru,
                                verilen_cevap=None, dogru_mu=False
                            )
                        logger.info(f"⏰ Oyuncu1 timeout (boş geçiş): {oda.oyuncu1.username}")
                    if not oda.oyuncu2_cevapladi and oda.oyuncu2:
                        oda.oyuncu2_cevapladi = True
                        oda.oyuncu2_cevap_zamani = timezone.now()
                        oda.oyuncu2_yanlis += 1
                        oda.oyuncu2_combo = 0
                        # Timeout boş geçiş cevap kaydı
                        if oda.aktif_soru and not KullaniciCevap.objects.filter(
                            kullanici=oda.oyuncu2, oda=oda, soru=oda.aktif_soru
                        ).exists():
                            KullaniciCevap.objects.create(
                                kullanici=oda.oyuncu2, oda=oda, soru=oda.aktif_soru,
                                verilen_cevap=None, dogru_mu=False
                            )
                        logger.info(f"⏰ Oyuncu2 timeout (boş geçiş): {oda.oyuncu2.username}")
                    if not oda.round_bekleme_durumu:
                        oda.round_bekleme_durumu = True
                        oda.round_bitis_zamani = timezone.now()
                        logger.info(f"⏳ Round bekleme BAŞLATILDI (TIMEOUT)")
                    oda.save()

            if oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi and oda.round_bekleme_durumu:
                if oda.round_bitis_zamani:
                    gecen_sure = (timezone.now() - oda.round_bitis_zamani).total_seconds()

                    if gecen_sure >= 3:
                        logger.info(f"✅ 3 saniye geçti, yeni soruya geçiliyor")

                        if oda.aktif_soru_no >= oda.toplam_soru:
                            # OYUN BİTTİ
                            oda.oyun_durumu = 'bitti'
                            oda.bitis_zamani = timezone.now()
                            oda.aktif_soru = None
                            oda.save()
                            logger.info(f"🏁 OYUN BİTTİ!")

                            # Turnuva maçı otomatik sonuçlandir
                            try:
                                from quiz.models import TurnuvaMaci
                                turnuva_maci = TurnuvaMaci.objects.filter(
                                    karsilasma_oda=oda,
                                    tamamlandi=False
                                ).select_related('turnuva', 'oyuncu1', 'oyuncu2').first()

                                if turnuva_maci:
                                    logger.info(f"🏆 TURNUVA MAÇI TESPİT EDİLDİ!")

                                    if oda.oyuncu1_skor > oda.oyuncu2_skor:
                                        kazanan = turnuva_maci.oyuncu1
                                    elif oda.oyuncu2_skor > oda.oyuncu1_skor:
                                        kazanan = turnuva_maci.oyuncu2
                                    else:
                                        if oda.oyuncu1_dogru > oda.oyuncu2_dogru:
                                            kazanan = turnuva_maci.oyuncu1
                                        elif oda.oyuncu2_dogru > oda.oyuncu1_dogru:
                                            kazanan = turnuva_maci.oyuncu2
                                        else:
                                            kazanan = random.choice([turnuva_maci.oyuncu1, turnuva_maci.oyuncu2])
                                            logger.warning(f"🎲 BERABERE! Rastgele: {kazanan.username}")

                                    logger.info(f"👑 Kazanan: {kazanan.username}")
                                    turnuva_maci.oyuncu1_skor = oda.oyuncu1_skor
                                    turnuva_maci.oyuncu2_skor = oda.oyuncu2_skor
                                    turnuva_maci.save()

                                    from quiz.helpers import turnuva_mac_bitir, turnuva_siralama_guncelle
                                    turnuva_bitti = turnuva_mac_bitir(turnuva_maci, kazanan)
                                    if turnuva_bitti:
                                        turnuva_siralama_guncelle(turnuva_maci.turnuva)
                                        logger.info(f"🏆 TURNUVA BİTTİ!")

                            except Exception as e:
                                logger.error(f"❌ Turnuva sonuçlandırma hatası: {str(e)}", exc_info=True)

                        else:
                            # Yeni soruya geç
                            oda.aktif_soru_no += 1
                            yeni_soru = get_random_soru_by_ders(oda.secilen_ders)

                            if yeni_soru:
                                oda.aktif_soru = yeni_soru
                                oda.soru_baslangic_zamani = timezone.now()
                                oda.oyuncu1_cevapladi = False
                                oda.oyuncu2_cevapladi = False
                                oda.oyuncu1_cevap_zamani = None
                                oda.oyuncu2_cevap_zamani = None
                                oda.ilk_dogru_cevaplayan = None
                                oda.round_bekleme_durumu = False
                                oda.round_bitis_zamani = None
                                logger.info(f"❓ Yeni soru: {oda.aktif_soru_no}/{oda.toplam_soru}")
                            else:
                                oda.oyun_durumu = 'bitti'
                                logger.error(f"❌ Soru bulunamadı!")

                        oda.save()

            # Fallback: oyun oynaniyor ama aktif soru atanmadıysa ata
            if oda.oyun_durumu == 'oynaniyor' and oda.aktif_soru is None and not oda.round_bekleme_durumu:
                fallback_soru = get_random_soru_by_ders(oda.secilen_ders)
                if fallback_soru:
                    oda.aktif_soru = fallback_soru
                    if not oda.aktif_soru_no:
                        oda.aktif_soru_no = 1
                    oda.soru_baslangic_zamani = timezone.now()
                    oda.oyuncu1_cevapladi = False
                    oda.oyuncu2_cevapladi = False
                    oda.save()
                    logger.warning(f"⚠️ Fallback soru atandı: Oda={oda_id}, Soru={fallback_soru.id}")

            # Response hazırla
            soru_obj = oda.aktif_soru
            cevaplar = []

            if soru_obj:
                try:
                    cevaplar_qs = Cevap.objects.filter(soru=soru_obj).order_by('id')
                    cevaplar = [{'id': c.id, 'metin': c.metin, 'dogru_mu': c.dogru_mu} for c in cevaplar_qs]
                except Exception as e:
                    logger.error(f"❌ Cevap yükleme hatası: {e}")

            kalan_sure = 0
            if oda.round_bekleme_durumu and oda.round_bitis_zamani:
                gecen = (timezone.now() - oda.round_bitis_zamani).total_seconds()
                kalan_sure = max(0, round(3 - gecen, 1))

            response_data = {
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
                'kalan_sure': kalan_sure
            }

            return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"❌ Hata: {e}", exc_info=True)
        return JsonResponse({
            'error': str(e),
            'message': 'Bir hata oluştu!'
        }, status=500)


@login_required
def karsilasma_sonuc(request, oda_id):
    """Karşılaşma sonuç sayfası"""
    try:
        oda = get_object_or_404(
            KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2'),
            oda_id=oda_id
        )

        is_oyuncu1 = (oda.oyuncu1 == request.user)

        if is_oyuncu1:
            benim_skorom = oda.oyuncu1_skor
            rakip_skorom = oda.oyuncu2_skor
            benim_dogrum = oda.oyuncu1_dogru
            benim_yanlisim = oda.oyuncu1_yanlis
        else:
            benim_skorom = oda.oyuncu2_skor
            rakip_skorom = oda.oyuncu1_skor
            benim_dogrum = oda.oyuncu2_dogru
            benim_yanlisim = oda.oyuncu2_yanlis

        kazandim = benim_skorom > rakip_skorom
        berabere = benim_skorom == rakip_skorom
        puan_degisimi = 0
        kazanilan_toplam_xp = 0
        kazanilan_puan = 0
        puan_carpani = 1.0
        puan_bonusu = 0

        # Turnuva kontrolü
        turnuva_maci = None
        turnuva = None
        try:
            from quiz.models import TurnuvaMaci
            turnuva_maci = TurnuvaMaci.objects.filter(
                karsilasma_oda=oda
            ).select_related('turnuva').first()
            if turnuva_maci:
                turnuva = turnuva_maci.turnuva
        except Exception:
            pass

        # İstatistik güncelle (sadece bir kez)
        try:
            session_key = f'karsilasma_sonuc_{oda_id}_{request.user.id}'

            if not request.session.get(session_key, False):
                profil = request.user.profil
                oyun_ist, _ = OyunModuIstatistik.objects.get_or_create(
                    profil=profil,
                    oyun_modu='karsilasma'
                )

                oyun_ist.oynanan_oyun_sayisi += 1
                oyun_ist.haftalik_oyun_sayisi += 1

                if kazandim:
                    oyun_ist.kazanilan_oyun += 1

                    # ✅ Streak çarpanı + Doğruluk bonusu ile puan ekle
                    toplam_soru = oda.toplam_soru or 10
                    puan_sonuc = puan_ekle(
                        profil,
                        taban_puan=30,
                        sebep='Karşılaşma kazanıldı',
                        dogru=benim_dogrum,
                        toplam=toplam_soru
                    )
                    puan_degisimi = puan_sonuc['kazanilan_puan']
                    kazanilan_puan = puan_sonuc['kazanilan_puan']
                    puan_carpani = puan_sonuc['carpan']
                    puan_bonusu = puan_sonuc['bonus_yuzdesi']

                    xp_sonuc = karsilasma_kazanildi_xp(profil)
                    kazanilan_toplam_xp += 30

                    if xp_sonuc.get('seviye_atlandi'):
                        messages.success(
                            request,
                            f"🎉 SEVİYE ATLADIN! Seviye {xp_sonuc['yeni_seviye']} - {xp_sonuc['unvan']}"
                        )

                elif berabere:
                    puan_degisimi = 0
                    xp_ekle(profil, 10, 'Karşılaşma berabere')
                    kazanilan_toplam_xp += 10
                else:
                    # ✅ Artık puan düşmüyor
                    oyun_ist.kaybedilen_oyun += 1
                    puan_degisimi = 0
                    xp_ekle(profil, 5, 'Karşılaşma kaybetti')
                    kazanilan_toplam_xp += 5

                kazanilan_toplam_xp += (benim_dogrum * 5) + (benim_yanlisim * 1)

                oyun_ist.save()
                profil.save()

                # ==================== GÖREV: KARŞILAŞMA OYNANDI ====================
                tamamlanan = gorev_ilerleme_guncelle(profil, 'karsilasma_oyna', 1)
                for g in tamamlanan:
                    messages.success(
                        request,
                        f"🎯 Görev tamamlandı: {g.sablon.icon} {g.sablon.isim} (+{g.sablon.odul_xp} XP)"
                    )

                # ==================== GÖREV: KARŞILAŞMA KAZANILDI ====================
                if kazandim:
                    tamamlanan_kazan = gorev_ilerleme_guncelle(profil, 'karsilasma_kazan', 1)
                    for g in tamamlanan_kazan:
                        messages.success(
                            request,
                            f"🎯 Görev tamamlandı: {g.sablon.icon} {g.sablon.isim} (+{g.sablon.odul_xp} XP)"
                        )

                # ==================== ÇALIŞMA TAKVİMİ ====================
                calisma_kaydi_guncelle(
                    profil,
                    oyun=1,
                    xp=kazanilan_toplam_xp,
                )

                request.session[session_key] = True

                # ==================== ROZET KONTROLÜ ====================
                try:
                    yeni_rozetler = rozet_kontrol_yap(profil)
                    if yeni_rozetler:
                        for rozet in yeni_rozetler:
                            messages.success(
                                request,
                                f'🏆 YENİ ROZET! {rozet.icon} {rozet.get_kategori_display()}'
                            )
                except Exception:
                    pass

            else:
                # Sayfa yenilendi - session'dan oku
                puan_degisimi = kazanilan_puan if kazandim else 0
                kazanilan_toplam_xp = (benim_dogrum * 5) + (benim_yanlisim * 1)
                if kazandim:
                    kazanilan_toplam_xp += 30
                elif berabere:
                    kazanilan_toplam_xp += 10
                else:
                    kazanilan_toplam_xp += 5

        except Exception as e:
            logger.error(f"Sonuç hatası: {e}", exc_info=True)

        # Yanlış cevapları getir (optimize: tek sorguda doğru cevapları da çek)
        yanlislar = []
        try:
            kullanici_cevaplari = KullaniciCevap.objects.filter(
                kullanici=request.user,
                oda=oda,
                dogru_mu=False
            ).select_related('soru', 'verilen_cevap')

            # Tüm yanlış soruların doğru cevaplarını tek sorguda çek
            yanlis_soru_ids = [kc.soru_id for kc in kullanici_cevaplari]
            dogru_cevaplar = {}
            if yanlis_soru_ids:
                for c in Cevap.objects.filter(soru_id__in=yanlis_soru_ids, dogru_mu=True):
                    dogru_cevaplar[c.soru_id] = c

            for kc in kullanici_cevaplari:
                yanlislar.append({
                    'soru': kc.soru,
                    'verilen_cevap': kc.verilen_cevap,
                    'dogru_cevap': dogru_cevaplar.get(kc.soru_id),
                    'detayli_aciklama': kc.soru.detayli_aciklama or '',
                })
        except Exception as e:
            logger.error(f"Yanlış cevap getirme hatası: {e}", exc_info=True)

        # Rakip kullanıcı ID'si (rövanş için)
        rakip_kullanici = oda.oyuncu2 if is_oyuncu1 else oda.oyuncu1
        rakip_kullanici_id = rakip_kullanici.id if rakip_kullanici else None

        context = {
            'oda': oda,
            'kazandim': kazandim,
            'berabere': berabere,
            'benim_skorom': benim_skorom,
            'rakip_skorom': rakip_skorom,
            'benim_dogrum': benim_dogrum,
            'benim_yanlisim': benim_yanlisim,
            'puan_degisimi': puan_degisimi,
            'is_oyuncu1': is_oyuncu1,
            'kazanilan_xp': kazanilan_toplam_xp,
            'turnuva': turnuva,
            'turnuva_maci': turnuva_maci,
            'yanlislar': yanlislar,
            # ✅ YENİ - puan detayları
            'kazanilan_puan': kazanilan_puan,
            'puan_carpani': puan_carpani,
            'puan_bonusu': puan_bonusu,
            # ✅ Rövanş için rakip ID
            'rakip_kullanici_id': rakip_kullanici_id,
        }

        return render(request, 'quiz/karsilasma_sonuc.html', context)

    except Exception as e:
        logger.error(f"❌ Sonuç sayfası hatası: {e}", exc_info=True)
        messages.error(request, 'Bir hata oluştu.')
        return redirect('karsilasma_sinav_tipi_secimi')


@login_required
def karsilasma_rakip_bul(request):
    """Rakip bulma sistemi"""
    secilen_ders = request.GET.get('ders', 'karisik')
    sinav_tipi = request.GET.get('sinav_tipi', 'AYT')
    logger.info(f"Rakip aranıyor: User={request.user.username}, Ders={secilen_ders}, Sınav={sinav_tipi}")

    # Eski odaları temizle (2 dakikadan eski bekleyen odalar)
    iki_dakika_once = timezone.now() - timedelta(minutes=2)
    KarsilasmaOdasi.objects.filter(
        oyun_durumu='bekleniyor',
        oyuncu2=None,
        olusturma_tarihi__lt=iki_dakika_once
    ).update(oyun_durumu='bitti')

    # Aktif oda var mı?
    aktif_oda = KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2').filter(
        models.Q(oyuncu1=request.user) | models.Q(oyuncu2=request.user),
        oyun_durumu__in=['bekleniyor', 'oynaniyor'],
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    ).first()

    if aktif_oda:
        logger.info(f"Aktif oda bulundu: {aktif_oda.oda_id}")
        return redirect('karsilasma_oyun', oda_id=aktif_oda.oda_id)

    # Farklı dersteki odaları kapat
    KarsilasmaOdasi.objects.filter(
        models.Q(oyuncu1=request.user) | models.Q(oyuncu2=request.user),
        oyun_durumu__in=['bekleniyor', 'oynaniyor']
    ).exclude(secilen_ders=secilen_ders, sinav_tipi=sinav_tipi).update(oyun_durumu='bitti')

    # Bekleyen oda bul
    bekleyen_oda = KarsilasmaOdasi.objects.select_related('oyuncu1').filter(
        oyun_durumu='bekleniyor',
        oyuncu2=None,
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    ).exclude(oyuncu1=request.user).first()

    if bekleyen_oda:
        # Rakip bulundu — oyunu henüz başlatma, hazır sistemi bekle
        bekleyen_oda.oyuncu2 = request.user
        # Oda kodunu ata (yoksa bekleme sayfası çalışmaz)
        if not bekleyen_oda.oda_kodu:
            bekleyen_oda.oda_kodu = oda_kodu_olustur()
        bekleyen_oda.save()
        logger.info(f"Rakip bulundu, hazır bekleniyor: Oda={bekleyen_oda.oda_id}")
        return redirect('karsilasma_oda_bekleme', oda_kodu=bekleyen_oda.oda_kodu)
    else:
        yeni_oda = KarsilasmaOdasi.objects.create(
            oyuncu1=request.user,
            oyun_durumu='bekleniyor',
            secilen_ders=secilen_ders,
            sinav_tipi=sinav_tipi
        )
        logger.info(f"Yeni oda: {yeni_oda.oda_id}")
        return redirect('karsilasma_oyun', oda_id=yeni_oda.oda_id)


# ==================== ODA KURMA SİSTEMİ ====================

def oda_kodu_olustur():
    """6 haneli büyük harf + rakam oda kodu üret"""
    while True:
        kod = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not KarsilasmaOdasi.objects.filter(oda_kodu=kod).exists():
            return kod


@login_required
def karsilasma_oda_kur(request):
    """Oda oluşturma sayfası - ders ve sınav tipi seçilir, kod oluşturulur"""
    sinav_tipi = request.GET.get('sinav_tipi', 'AYT')

    if sinav_tipi == 'TYT':
        ders_secenekleri = [
            ('turkce', 'Türkçe', '📚'),
            ('fizik', 'Fizik', '⚛️'),
            ('kimya', 'Kimya', '🧪'),
            ('biyoloji', 'Biyoloji', '🧬'),
            ('tarih', 'Tarih', '🏛️'),
            ('cografya', 'Coğrafya', '🌍'),
            ('felsefe', 'Felsefe', '💭'),
            ('karisik_sayisal', 'Karışık Sayısal', '🔢🎲'),
            ('karisik_sozel', 'Karışık Sözel', '📚🎲'),
        ]
    else:
        ders_secenekleri = [
            ('fizik', 'Fizik', '⚛️'),
            ('kimya', 'Kimya', '🧪'),
            ('biyoloji', 'Biyoloji', '🧬'),
            ('edebiyat', 'Edebiyat', '📚'),
            ('tarih', 'Tarih', '🏛️'),
            ('cografya', 'Coğrafya', '🌍'),
            ('felsefe', 'Felsefe', '💭'),
            ('karisik_sayisal', 'Karışık Sayısal (F+K+B)', '🔢🎲'),
            ('karisik_ea', 'Karışık EA (Ed+Tar+Coğ)', '📖🎲'),
            ('karisik_sozel_ayt', 'Karışık Sözel (Din+Fel+Ed+Tar+Coğ)', '📚🎲'),
        ]

    if request.method == 'POST':
        secilen_ders = request.POST.get('selected_ders', 'karisik')
        kod = oda_kodu_olustur()

        oda = KarsilasmaOdasi.objects.create(
            oyuncu1=request.user,
            oyun_durumu='bekleniyor',
            secilen_ders=secilen_ders,
            sinav_tipi=sinav_tipi,
            oda_kodu=kod
        )
        logger.info(f"Oda kuruldu: Kod={kod}, Ders={secilen_ders}, User={request.user.username}")
        return redirect('karsilasma_oda_bekleme', oda_kodu=kod)

    context = {
        'ders_secenekleri': ders_secenekleri,
        'sinav_tipi': sinav_tipi
    }
    return render(request, 'quiz/karsilasma_oda_kur.html', context)


@login_required
def karsilasma_oda_bekleme(request, oda_kodu):
    """Her iki oyuncu da burada bekler, ikisi de hazır olunca oyun başlar"""
    try:
        oda = KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2').get(
            oda_kodu=oda_kodu
        )
    except KarsilasmaOdasi.DoesNotExist:
        messages.error(request, 'Oda bulunamadı!')
        return redirect('karsilasma_sinav_tipi_secimi')

    # Sadece oyuncu1 veya oyuncu2 erişebilir
    if request.user != oda.oyuncu1 and request.user != oda.oyuncu2:
        messages.error(request, 'Bu odaya erişim yetkiniz yok!')
        return redirect('karsilasma_sinav_tipi_secimi')

    # Oyun başladıysa oyuna yönlendir
    if oda.oyun_durumu == 'oynaniyor':
        return redirect('karsilasma_oyun', oda_id=oda.oda_id)

    ben_oyuncu1 = (request.user == oda.oyuncu1)

    context = {
        'oda': oda,
        'oda_kodu': oda_kodu,
        'ben_oyuncu1': ben_oyuncu1,
    }
    return render(request, 'quiz/karsilasma_oda_bekleme.html', context)


@login_required
def karsilasma_oda_bekleme_durum(request, oda_kodu):
    """AJAX: Oda durumu kontrolü"""
    try:
        oda = KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2').get(oda_kodu=oda_kodu)
    except KarsilasmaOdasi.DoesNotExist:
        return JsonResponse({'error': 'Oda bulunamadı'}, status=404)

    return JsonResponse({
        'oyun_durumu': oda.oyun_durumu,
        'oyuncu2_var': oda.oyuncu2 is not None,
        'oyuncu1_adi': oda.oyuncu1.username,
        'oyuncu2_adi': oda.oyuncu2.username if oda.oyuncu2 else None,
        'oyuncu1_hazir': oda.oyuncu1_hazir,
        'oyuncu2_hazir': oda.oyuncu2_hazir,
        'redirect_url': reverse('karsilasma_oyun', args=[str(oda.oda_id)]) if oda.oyun_durumu == 'oynaniyor' else None,
    })


@login_required
def karsilasma_oda_katil(request):
    """Oda kodunu girip odaya katılma"""
    if request.method == 'POST':
        oda_kodu = request.POST.get('oda_kodu', '').strip().upper()

        if not oda_kodu or len(oda_kodu) != 6:
            messages.error(request, 'Geçersiz oda kodu! 6 haneli bir kod girin.')
            return render(request, 'quiz/karsilasma_oda_katil.html')

        try:
            oda = KarsilasmaOdasi.objects.get(
                oda_kodu=oda_kodu,
                oyun_durumu='bekleniyor',
                oyuncu2=None
            )
        except KarsilasmaOdasi.DoesNotExist:
            messages.error(request, 'Oda bulunamadı veya dolu! Kodu kontrol edin.')
            return render(request, 'quiz/karsilasma_oda_katil.html')

        if oda.oyuncu1 == request.user:
            messages.error(request, 'Kendi odanıza katılamazsınız!')
            return render(request, 'quiz/karsilasma_oda_katil.html')

        # Odaya katıl - oyunu henüz başlatma, hazır sistemi bekle
        oda.oyuncu2 = request.user
        oda.save()
        logger.info(f"Odaya katılındı: Kod={oda_kodu}, User={request.user.username}")
        return redirect('karsilasma_oda_bekleme', oda_kodu=oda.oda_kodu)

    return render(request, 'quiz/karsilasma_oda_katil.html')


@login_required
@require_http_methods(["POST"])
def karsilasma_oda_hazir(request, oda_kodu):
    """Oyuncu hazır olduğunu bildirir. İkisi de hazırsa oyun başlar."""
    try:
        with transaction.atomic():
            oda = KarsilasmaOdasi.objects.select_for_update().get(oda_kodu=oda_kodu)

            if oda.oyun_durumu == 'oynaniyor':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('karsilasma_oyun', args=[str(oda.oda_id)])
                })

            if request.user == oda.oyuncu1:
                oda.oyuncu1_hazir = True
            elif request.user == oda.oyuncu2:
                oda.oyuncu2_hazir = True
            else:
                return JsonResponse({'success': False, 'error': 'Bu odada değilsiniz'}, status=403)

            # İkisi de hazırsa oyunu başlat
            if oda.oyuncu1_hazir and oda.oyuncu2_hazir and oda.oyuncu2 is not None:
                oda.oyun_durumu = 'oynaniyor'
                ilk_soru = get_random_soru_by_ders(oda.secilen_ders)
                if ilk_soru:
                    oda.aktif_soru = ilk_soru
                    oda.aktif_soru_no = 1
                    oda.soru_baslangic_zamani = timezone.now()

            oda.save()

            redirect_url = None
            if oda.oyun_durumu == 'oynaniyor':
                redirect_url = reverse('karsilasma_oyun', args=[str(oda.oda_id)])

            return JsonResponse({
                'success': True,
                'oyuncu1_hazir': oda.oyuncu1_hazir,
                'oyuncu2_hazir': oda.oyuncu2_hazir,
                'oyun_basladi': oda.oyun_durumu == 'oynaniyor',
                'redirect_url': redirect_url,
            })
    except KarsilasmaOdasi.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Oda bulunamadı'}, status=404)


@login_required
@require_http_methods(["POST"])
def karsilasma_oda_ayril(request, oda_kodu):
    """Eşleşmeden önce odadan ayrıl"""
    try:
        oda = KarsilasmaOdasi.objects.get(oda_kodu=oda_kodu)
    except KarsilasmaOdasi.DoesNotExist:
        return JsonResponse({'success': True})  # zaten silinmiş

    # Oyun başlamışsa ayrılamaz
    if oda.oyun_durumu == 'oynaniyor':
        return JsonResponse({'success': False, 'error': 'Oyun başlamış'}, status=400)

    # Oyuncu 1 (oda sahibi) ayrılırsa → odayı sil
    if oda.oyuncu1 == request.user:
        logger.info(f"Oda silindi (sahip ayrıldı): Kod={oda_kodu}, User={request.user.username}")
        oda.delete()
        return JsonResponse({'success': True})

    # Oyuncu 2 ayrılırsa → oyuncu2'yi temizle, hazır durumunu sıfırla
    if oda.oyuncu2 == request.user:
        logger.info(f"Oyuncu2 ayrıldı: Kod={oda_kodu}, User={request.user.username}")
        oda.oyuncu2 = None
        oda.oyuncu2_hazir = False
        oda.oyuncu1_hazir = False  # İkisini de sıfırla
        oda.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Bu odada değilsiniz'}, status=400)


@login_required
@require_http_methods(["POST"])
def karsilasma_oda_birak(request, oda_id):
    """Rakip beklerken sayfadan ayrılırsa odayı temizle (random eşleşme)"""
    try:
        oda = KarsilasmaOdasi.objects.get(oda_id=oda_id)
    except KarsilasmaOdasi.DoesNotExist:
        return JsonResponse({'success': True})

    # Oyun başlamışsa dokunma
    if oda.oyun_durumu == 'oynaniyor':
        return JsonResponse({'success': False, 'error': 'Oyun başlamış'}, status=400)

    # Oda sahibi ayrılıyorsa ve rakip yoksa → odayı sil
    if oda.oyuncu1 == request.user and oda.oyuncu2 is None:
        logger.info(f"Oda silindi (bekleme sırasında ayrıldı): OdaID={oda_id}, User={request.user.username}")
        oda.delete()
        return JsonResponse({'success': True})

    # Oyuncu2 ayrılıyorsa → temizle
    if oda.oyuncu2 == request.user:
        oda.oyuncu2 = None
        oda.oyuncu2_hazir = False
        oda.oyuncu1_hazir = False
        oda.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': True})


# ==================== MEYDAN OKUMA ====================

@login_required
def meydan_okuma_gonder(request, kullanici_id):
    """Arkadaşa meydan okuma isteği gönder"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Geçersiz JSON'}, status=400)

    secilen_ders = data.get('ders', 'karisik')
    sinav_tipi = data.get('sinav_tipi', 'AYT')

    try:
        hedef_kullanici = User.objects.get(id=kullanici_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Kullanıcı bulunamadı!'}, status=404)

    if hedef_kullanici == request.user:
        return JsonResponse({'success': False, 'message': 'Kendinize meydan okuyamazsınız!'})

    # Arkadaş mı kontrol et
    from profile.models import Arkadaslik
    from django.db.models import Q
    arkadaslar_mi = Arkadaslik.objects.filter(
        Q(gonderen=request.user, alan=hedef_kullanici) |
        Q(gonderen=hedef_kullanici, alan=request.user),
        durum='kabul_edildi'
    ).exists()

    if not arkadaslar_mi:
        return JsonResponse({'success': False, 'message': 'Sadece arkadaşlarınıza meydan okuyabilirsiniz!'})

    # Zaten bekleyen meydan okuma var mı?
    mevcut = MeydanOkuma.objects.filter(
        gonderen=request.user,
        alan=hedef_kullanici,
        durum='beklemede'
    ).first()

    if mevcut:
        return JsonResponse({'success': False, 'message': 'Zaten bekleyen bir meydan okuma var!'})

    # Yeni oda oluştur
    oda = KarsilasmaOdasi.objects.create(
        oyuncu1=request.user,
        oyun_durumu='bekleniyor',
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    )

    # Meydan okuma oluştur
    meydan = MeydanOkuma.objects.create(
        gonderen=request.user,
        alan=hedef_kullanici,
        oda=oda,
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    )

    # Bildirim gönder
    try:
        from profile.bildirim_helper import bildirim_gonder
        bildirim_gonder(
            kullanici=hedef_kullanici,
            tip='sistem',
            baslik='⚔️ Meydan Okuma!',
            mesaj=f'{request.user.username} sana {secilen_ders} konusunda meydan okuyor!',
            icon='⚔️'
        )
    except Exception as e:
        logger.error(f"Meydan okuma bildirimi hatası: {e}", exc_info=True)

    logger.info(f"Meydan okuma gönderildi: {request.user.username} → {hedef_kullanici.username}")

    return JsonResponse({
        'success': True,
        'message': f'⚔️ {hedef_kullanici.username} kullanıcısına meydan okuma gönderildi!',
        'meydan_id': meydan.id
    })


@login_required
def revans_gonder(request, kullanici_id):
    """Rövanş isteği gönder - arkadaşlık şartı yok"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Geçersiz JSON'}, status=400)

    secilen_ders = data.get('ders', 'karisik')
    sinav_tipi = data.get('sinav_tipi', 'AYT')

    try:
        hedef_kullanici = User.objects.get(id=kullanici_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Kullanıcı bulunamadı!'}, status=404)

    if hedef_kullanici == request.user:
        return JsonResponse({'success': False, 'message': 'Kendinize rövanş gönderemezsiniz!'})

    # Zaten bekleyen meydan okuma var mı?
    mevcut = MeydanOkuma.objects.filter(
        gonderen=request.user,
        alan=hedef_kullanici,
        durum='beklemede'
    ).first()

    if mevcut:
        return JsonResponse({'success': False, 'message': 'Zaten bekleyen bir rövanş isteği var!'})

    # Yeni oda oluştur
    oda = KarsilasmaOdasi.objects.create(
        oyuncu1=request.user,
        oyun_durumu='bekleniyor',
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    )

    # Meydan okuma oluştur
    meydan = MeydanOkuma.objects.create(
        gonderen=request.user,
        alan=hedef_kullanici,
        oda=oda,
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    )

    # Bildirim gönder
    try:
        from profile.bildirim_helper import bildirim_gonder
        bildirim_gonder(
            kullanici=hedef_kullanici,
            tip='meydan_okuma',
            baslik='🔄 Rövanş İsteği!',
            mesaj=f'{request.user.username} sana rövanş istiyor!',
            icon='🔄'
        )
    except Exception as e:
        logger.error(f"Rövanş bildirimi hatası: {e}", exc_info=True)

    logger.info(f"Rövanş gönderildi: {request.user.username} → {hedef_kullanici.username}")

    return JsonResponse({
        'success': True,
        'message': f'🔄 {hedef_kullanici.username} kullanıcısına rövanş isteği gönderildi!',
        'meydan_id': meydan.id
    })


@login_required
def meydan_okuma_kabul(request, meydan_id):
    """Meydan okumayı kabul et"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)

    try:
        meydan = MeydanOkuma.objects.select_related(
            'gonderen', 'alan', 'oda'
        ).get(id=meydan_id, alan=request.user, durum='beklemede')
    except MeydanOkuma.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Meydan okuma bulunamadı!'}, status=404)

    # Süresi geçmiş mi?
    if meydan.suresi_gecti_mi():
        meydan.durum = 'suresi_doldu'
        meydan.save()
        return JsonResponse({'success': False, 'message': 'Meydan okumanın süresi doldu!'})

    # Odaya katıl — oyunu henüz başlatma, hazır sistemi bekle
    oda = meydan.oda
    oda.oyuncu2 = request.user
    if not oda.oda_kodu:
        oda.oda_kodu = oda_kodu_olustur()
    oda.save()

    # Meydan okumayı güncelle
    meydan.durum = 'kabul_edildi'
    meydan.save()

    # Gönderene bildirim
    try:
        from profile.bildirim_helper import bildirim_gonder
        bildirim_gonder(
            kullanici=meydan.gonderen,
            tip='sistem',
            baslik='✅ Meydan Okuma Kabul Edildi!',
            mesaj=f'{request.user.username} meydan okumanı kabul etti! Hazır ol!',
            icon='⚔️'
        )
    except Exception as e:
        logger.error(f"Kabul bildirimi hatası: {e}", exc_info=True)

    logger.info(f"Meydan okuma kabul edildi: {meydan.gonderen.username} vs {request.user.username}")

    return JsonResponse({
        'success': True,
        'message': 'Meydan okuma kabul edildi! Hazır sayfasına yönlendiriliyorsunuz...',
        'redirect_url': reverse('karsilasma_oda_bekleme', args=[oda.oda_kodu])
    })


@login_required
def meydan_okuma_reddet(request, meydan_id):
    """Meydan okumayı reddet"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)

    try:
        meydan = MeydanOkuma.objects.select_related(
            'gonderen', 'alan'
        ).get(id=meydan_id, alan=request.user, durum='beklemede')
    except MeydanOkuma.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Meydan okuma bulunamadı!'}, status=404)

    meydan.durum = 'reddedildi'
    meydan.save()

    # Odayı kapat
    if meydan.oda:
        meydan.oda.oyun_durumu = 'bitti'
        meydan.oda.save()

    # Gönderene bildirim
    try:
        from profile.bildirim_helper import bildirim_gonder
        bildirim_gonder(
            kullanici=meydan.gonderen,
            tip='sistem',
            baslik='❌ Meydan Okuma Reddedildi',
            mesaj=f'{request.user.username} meydan okumanı reddetti.',
            icon='❌'
        )
    except Exception as e:
        logger.error(f"Ret bildirimi hatası: {e}", exc_info=True)

    logger.info(f"Meydan okuma reddedildi: {meydan.gonderen.username} → {request.user.username}")

    return JsonResponse({
        'success': True,
        'message': 'Meydan okuma reddedildi.'
    })


@login_required
def meydan_okumalarim(request):
    """Gelen ve gönderilen meydan okumalar"""

    # 5 dakikası dolmuş bekleyen meydan okumaları otomatik iptal et
    bes_dk_once = timezone.now() - timedelta(minutes=5)
    suresi_dolanlar = MeydanOkuma.objects.filter(
        durum='beklemede',
        olusturma_tarihi__lt=bes_dk_once
    )
    for m in suresi_dolanlar:
        m.durum = 'suresi_doldu'
        m.save()
        if m.oda and m.oda.oyun_durumu == 'bekleniyor':
            m.oda.oyun_durumu = 'bitti'
            m.oda.save()
    if suresi_dolanlar.count() > 0:
        logger.info(f"⏰ {suresi_dolanlar.count()} meydan okuma süresi doldu (otomatik iptal)")

    gelen = MeydanOkuma.objects.filter(
        alan=request.user,
        durum='beklemede'
    ).select_related('gonderen', 'gonderen__profil').order_by('-olusturma_tarihi')

    gonderilen = MeydanOkuma.objects.filter(
        gonderen=request.user,
        durum='beklemede'
    ).select_related('alan', 'alan__profil').order_by('-olusturma_tarihi')

    gecmis = MeydanOkuma.objects.filter(
        models.Q(gonderen=request.user) | models.Q(alan=request.user)
    ).exclude(durum='beklemede').select_related(
        'gonderen', 'alan'
    ).order_by('-olusturma_tarihi')[:20]

    context = {
        'gelen': gelen,
        'gonderilen': gonderilen,
        'gecmis': gecmis,
        'gelen_sayisi': gelen.count(),
    }
    return render(request, 'quiz/meydan_okumalarim.html', context)


@login_required
def meydan_okuma_iptal(request, meydan_id):
    """Gönderilen meydan okumayı iptal et"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)

    try:
        meydan = MeydanOkuma.objects.get(
            id=meydan_id,
            gonderen=request.user,
            durum='beklemede'
        )
    except MeydanOkuma.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Meydan okuma bulunamadı!'}, status=404)

    meydan.durum = 'reddedildi'
    meydan.save()

    if meydan.oda:
        meydan.oda.oyun_durumu = 'bitti'
        meydan.oda.save()

    return JsonResponse({'success': True, 'message': 'Meydan okuma iptal edildi.'})


@login_required
def karsilasma_gecmis(request):
    """
    Kullanıcının bitmiş karşılaşmalarını listeler.
    - En yeni en üstte: bitis_zamani DESC, yoksa olusturma_tarihi DESC
    - Turnuva maçı ise Turnuva etiketi gösterebilmek için TurnuvaMaci eşlemesi yapar.
    """
    user = request.user

    try:
        # Not: oda_id UUID PK olduğu için order_by ve filtrelerde sorun yok
        odalar = (
            KarsilasmaOdasi.objects
            .select_related('oyuncu1', 'oyuncu2')
            .filter(models.Q(oyuncu1=user) | models.Q(oyuncu2=user))
            .filter(oyun_durumu='bitti')
            .filter(oyuncu2__isnull=False)
            .order_by('-bitis_zamani', '-olusturma_tarihi')
        )

        # Turnuva maçlarını tek seferde çek (DB sütunu yoksa sessizce atla)
        try:
            turnuva_maclari = (
                TurnuvaMaci.objects
                .filter(karsilasma_oda__in=odalar)
                .select_related('turnuva', 'kazanan', 'karsilasma_oda')
            )
            turnuva_by_oda_id = {
                tm.karsilasma_oda_id: tm
                for tm in turnuva_maclari
                if tm.karsilasma_oda_id
            }
        except Exception as tm_err:
            logger.warning(f"⚠️ TurnuvaMaci sorgusu atlandı: {tm_err}")
            turnuva_by_oda_id = {}

        rows = []
        for oda in odalar:
            is_oyuncu1 = (oda.oyuncu1_id == user.id)

            rakip = oda.oyuncu2 if is_oyuncu1 else oda.oyuncu1
            benim_skor = oda.oyuncu1_skor if is_oyuncu1 else oda.oyuncu2_skor
            rakip_skor = oda.oyuncu2_skor if is_oyuncu1 else oda.oyuncu1_skor

            if benim_skor > rakip_skor:
                sonuc = "Kazandı"
            elif benim_skor < rakip_skor:
                sonuc = "Kaybetti"
            else:
                sonuc = "Berabere"

            tm = turnuva_by_oda_id.get(oda.oda_id)

            benim_dogru = oda.oyuncu1_dogru if is_oyuncu1 else oda.oyuncu2_dogru
            benim_yanlis = oda.oyuncu1_yanlis if is_oyuncu1 else oda.oyuncu2_yanlis
            rakip_dogru = oda.oyuncu2_dogru if is_oyuncu1 else oda.oyuncu1_dogru
            rakip_yanlis = oda.oyuncu2_yanlis if is_oyuncu1 else oda.oyuncu1_yanlis

            rows.append({
                "oda": oda,
                "rakip": rakip,
                "benim_skor": benim_skor,
                "rakip_skor": rakip_skor,
                "sonuc": sonuc,
                "puan_farki": abs(benim_skor - rakip_skor),
                "is_turnuva": tm is not None,
                "turnuva_maci": tm,
                "benim_dogru": benim_dogru,
                "benim_yanlis": benim_yanlis,
                "rakip_dogru": rakip_dogru,
                "rakip_yanlis": rakip_yanlis,
            })

        context = {"rows": rows}
        return render(request, "quiz/karsilasma_gecmisi.html", context)

    except Exception as e:
        logger.error(f"❌ Karşılaşma geçmişi hatası: {e}", exc_info=True)
        messages.error(request, "Karşılaşma geçmişi yüklenirken bir hata oluştu.")
        return redirect('quiz_anasayfa')