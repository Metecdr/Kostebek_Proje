from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import models, transaction
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from quiz.models import KarsilasmaOdasi, Cevap, Soru
from quiz.helpers import get_random_soru_by_ders, update_stats_with_combo
from profile.models import OyunModuIstatistik, OgrenciProfili
from profile.rozet_kontrol import rozet_kontrol_yap
from profile.xp_helper import soru_cozuldu_xp, karsilasma_kazanildi_xp, xp_ekle
import json
import logging
import random

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
            ('matematik', 'Matematik', '🔢'),
            ('turkce', 'Türkçe', '📚'),
            ('fizik', 'Fizik', '⚛️'),
            ('kimya', 'Kimya', '🧪'),
            ('biyoloji', 'Biyoloji', '🧬'),
            ('tarih', 'Tarih', '🏛️'),
            ('cografya', 'Coğrafya', '🌍'),
            ('felsefe', 'Felsefe', '💭'),
            ('karisik', 'Karışık', '🎲')
        ]
    else:
        ders_secenekleri = [
            ('matematik', 'Matematik', '🔢'),
            ('fizik', 'Fizik', '⚛️'),
            ('kimya', 'Kimya', '🧪'),
            ('biyoloji', 'Biyoloji', '🧬'),
            ('edebiyat', 'Edebiyat', '📚'),
            ('tarih', 'Tarih', '🏛️'),
            ('cografya', 'Coğrafya', '🌍'),
            ('felsefe', 'Felsefe', '💭'),
            ('karisik', 'Karışık', '🎲')
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
    
    is_oyuncu1 = (oda.oyuncu1 == request.user)
    
    if is_oyuncu1:
        rakip = oda.oyuncu2
        rakip_username = rakip.username if rakip else 'Rakip Bekleniyor...'
        try:
            rakip_seviye = rakip.profil.seviye if rakip else '?'
        except:
            rakip_seviye = '?'
    else:
        rakip = oda.oyuncu1
        rakip_username = rakip.username
        try:
            rakip_seviye = rakip.profil.seviye
        except:
            rakip_seviye = '?'
    
    soru_obj = oda.aktif_soru
    cevaplar = []
    
    if soru_obj:
        try:
            cevaplar_qs = Cevap.objects.filter(soru=soru_obj).order_by('id')
            cevaplar = [{'id': c.id, 'metin': c.metin} for c in cevaplar_qs]
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
        oda = get_object_or_404(
            KarsilasmaOdasi.objects.select_for_update().select_related(
                'oyuncu1', 'oyuncu2', 'aktif_soru', 'ilk_dogru_cevaplayan'
            ),
            oda_id=oda_id
        )
        
        # ✅ POST: CEVAP GÖNDERME
        if request.method == 'POST':
            data = json.loads(request.body)
            cevap_id = data.get('cevap_id')
            
            # ✅ BOŞ GEÇİŞ KONTROLÜ
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
                
                return JsonResponse({
                    'success': True,
                    'dogru_mu': False,
                    'kazanilan_xp': 0,
                    'seviye_atlandi': False,
                    'bos_gecis': True
                })
            
            # ✅ NORMAL CEVAP
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
            
            # XP ekle
            try:
                profil = request.user.profil
                xp_sonuc = soru_cozuldu_xp(profil, dogru_mu)
                
                seviye_atlandi = xp_sonuc.get('seviye_atlandi', False)
                yeni_seviye = xp_sonuc.get('yeni_seviye', 0)
                yeni_unvan = xp_sonuc.get('unvan', '')
                kazanilan_xp = 5 if dogru_mu else 1
                
                # Rozet kontrolü
                if profil.cozulen_soru_sayisi % 10 == 0:
                    try:
                        rozet_kontrol_yap(profil)
                    except:
                        pass
            except Exception as e:
                logger.error(f"XP hatası: {e}", exc_info=True)
            
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
        
        # ✅ GET: DURUM KONTROLÜ
        elif request.method == 'GET':
            # Her iki oyuncu cevapladıysa ve bekleme modundaysa
            if oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi and oda.round_bekleme_durumu:
                if oda.round_bitis_zamani:
                    gecen_sure = (timezone.now() - oda.round_bitis_zamani).total_seconds()
                    
                    # 5 saniye geçtiyse yeni soruya geç
                    if gecen_sure >= 5:
                        logger.info(f"✅ 5 saniye geçti, yeni soruya geçiliyor")
                        
                        if oda.aktif_soru_no >= oda.toplam_soru:
                            # ✅ OYUN BİTTİ!
                            oda.oyun_durumu = 'bitti'
                            oda.bitis_zamani = timezone.now()
                            oda.aktif_soru = None
                            oda.save()
                            
                            logger.info(f"🏁 OYUN BİTTİ!")
                            
                            # ✅ TURNUVA MAÇI OTOMATİK SONUÇLANDIR
                            try:
                                from quiz.models import TurnuvaMaci
                                
                                turnuva_maci = TurnuvaMaci.objects.filter(
                                    karsilasma_oda=oda,
                                    tamamlandi=False
                                ).select_related('turnuva', 'oyuncu1', 'oyuncu2').first()
                                
                                if turnuva_maci:
                                    logger.info(f"   🏆 TURNUVA MAÇI TESPİT EDİLDİ!")
                                    logger.info(f"   Turnuva: {turnuva_maci.turnuva.isim}")
                                    
                                    # Kazananı belirle
                                    if oda.oyuncu1_skor > oda.oyuncu2_skor:
                                        kazanan = turnuva_maci.oyuncu1
                                    elif oda.oyuncu2_skor > oda.oyuncu1_skor:
                                        kazanan = turnuva_maci.oyuncu2
                                    else:
                                        # Berabere - doğru sayısına bak
                                        if oda.oyuncu1_dogru > oda.oyuncu2_dogru:
                                            kazanan = turnuva_maci.oyuncu1
                                        elif oda.oyuncu2_dogru > oda.oyuncu2_dogru:
                                            kazanan = turnuva_maci.oyuncu2
                                        else:
                                            # Rastgele
                                            kazanan = random.choice([turnuva_maci.oyuncu1, turnuva_maci.oyuncu2])
                                            logger.warning(f"   🎲 BERABERE! Rastgele: {kazanan.username}")
                                    
                                    logger.info(f"   👑 Kazanan: {kazanan.username}")
                                    
                                    # Skorları kaydet
                                    turnuva_maci.oyuncu1_skor = oda.oyuncu1_skor
                                    turnuva_maci.oyuncu2_skor = oda.oyuncu2_skor
                                    turnuva_maci.save()
                                    
                                    # Maçı bitir
                                    from quiz.helpers import turnuva_mac_bitir, turnuva_siralama_guncelle
                                    
                                    turnuva_bitti = turnuva_mac_bitir(turnuva_maci, kazanan)
                                    
                                    if turnuva_bitti:
                                        turnuva_siralama_guncelle(turnuva_maci.turnuva)
                                        logger.info(f"   🏆 TURNUVA BİTTİ!")
                                    else:
                                        logger.info(f"   ✅ Sonraki round oluşturuldu")
                            
                            except Exception as e:
                                logger.error(f"❌ Turnuva sonuçlandırma hatası: {str(e)}", exc_info=True)
                        
                        else:
                            # Yeni soruya geç
                            oda.aktif_soru_no += 1
                            yeni_soru = get_random_soru_by_ders(oda.secilen_ders)
                            
                            if yeni_soru:
                                oda.aktif_soru = yeni_soru
                                oda.soru_baslangic_zamani = timezone.now()
                                
                                # Flag'leri sıfırla
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
            
            # Response hazırla
            soru_obj = oda.aktif_soru
            cevaplar = []
            
            if soru_obj:
                try:
                    cevaplar_qs = Cevap.objects.filter(soru=soru_obj).order_by('id')
                    cevaplar = [{'id': c.id, 'metin': c.metin} for c in cevaplar_qs]
                except Exception as e:
                    logger.error(f"❌ Cevap yükleme hatası: {e}")
            
            # Kalan süre
            kalan_sure = 0
            if oda.round_bekleme_durumu and oda.round_bitis_zamani:
                gecen = (timezone.now() - oda.round_bitis_zamani).total_seconds()
                kalan_sure = max(0, round(5 - gecen, 1))
            
            response_data = {
                'oyuncu1_skor': oda.oyuncu1_skor,
                'oyuncu2_skor': oda.oyuncu2_skor,
                'oyuncu1_combo': oda.oyuncu1_combo,
                'oyuncu2_combo': oda.oyuncu2_combo,
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
    """Karşılaşma sonuç sayfası - Turnuva destekli"""
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
        
        # ✅ TURNUVA KONTROLÜ
        turnuva_maci = None
        turnuva = None
        
        try:
            from quiz.models import TurnuvaMaci
            
            turnuva_maci = TurnuvaMaci.objects.filter(
                karsilasma_oda=oda
            ).select_related('turnuva').first()
            
            if turnuva_maci:
                turnuva = turnuva_maci.turnuva
                logger.info(f"🏆 Turnuva maçı sonucu: {turnuva.isim}")
        except:
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
                    puan_degisimi = 1
                    profil.toplam_puan += 1
                    profil.haftalik_puan += 1
                    
                    # Kazanma bonus XP (30 XP)
                    xp_sonuc = karsilasma_kazanildi_xp(profil)
                    kazanilan_toplam_xp += 30
                    
                    if xp_sonuc.get('seviye_atlandi'):
                        messages.success(request, f"🎉 SEVİYE ATLADIN! Seviye {xp_sonuc['yeni_seviye']} - {xp_sonuc['unvan']}")
                
                elif berabere:
                    puan_degisimi = 0
                    xp_ekle(profil, 10, 'Karşılaşma berabere')
                    kazanilan_toplam_xp += 10
                else:
                    oyun_ist.kaybedilen_oyun += 1
                    puan_degisimi = -1
                    profil.toplam_puan = max(0, profil.toplam_puan - 1)
                    profil.haftalik_puan = max(0, profil.haftalik_puan - 1)
                    xp_ekle(profil, 5, 'Karşılaşma kaybetti')
                    kazanilan_toplam_xp += 5
                
                # Soru başına XP
                kazanilan_toplam_xp += (benim_dogrum * 5) + (benim_yanlisim * 1)
                
                oyun_ist.save()
                profil.save()
                request.session[session_key] = True
                
                # Rozet kontrolü
                try:
                    yeni_rozetler = rozet_kontrol_yap(profil)
                    if yeni_rozetler:
                        for rozet in yeni_rozetler:
                            messages.success(request, f'🏆 YENİ ROZET! {rozet.icon} {rozet.get_kategori_display()}')
                except:
                    pass
            else:
                puan_degisimi = 1 if kazandim else (-1 if not berabere else 0)
                kazanilan_toplam_xp = (benim_dogrum * 5) + (benim_yanlisim * 1)
                if kazandim:
                    kazanilan_toplam_xp += 30
                elif berabere:
                    kazanilan_toplam_xp += 10
                else:
                    kazanilan_toplam_xp += 5
        except Exception as e:
            logger.error(f"Sonuç hatası: {e}", exc_info=True)
        
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
            'turnuva': turnuva,  # ✅ YENİ
            'turnuva_maci': turnuva_maci  # ✅ YENİ
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
    
    # Eski odaları temizle
    bes_dakika_once = timezone.now() - timedelta(minutes=5)
    KarsilasmaOdasi.objects.filter(
        oyuncu1=request.user,
        oyun_durumu='bekleniyor',
        oyuncu2=None,
        olusturma_tarihi__lt=bes_dakika_once
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
        # Odaya katıl
        bekleyen_oda.oyuncu2 = request.user
        bekleyen_oda.oyun_durumu = 'oynaniyor'
        
        ilk_soru = get_random_soru_by_ders(secilen_ders)
        if ilk_soru:
            bekleyen_oda.aktif_soru = ilk_soru
            bekleyen_oda.aktif_soru_no = 1
            bekleyen_oda.soru_baslangic_zamani = timezone.now()
            logger.info(f"Oyun başladı: Oda={bekleyen_oda.oda_id}")
        
        bekleyen_oda.save()
        return redirect('karsilasma_oyun', oda_id=bekleyen_oda.oda_id)
    else:
        # Yeni oda oluştur
        yeni_oda = KarsilasmaOdasi.objects.create(
            oyuncu1=request.user,
            oyun_durumu='bekleniyor',
            secilen_ders=secilen_ders,
            sinav_tipi=sinav_tipi
        )
        logger.info(f"Yeni oda: {yeni_oda.oda_id}")
        return redirect('karsilasma_oyun', oda_id=yeni_oda.oda_id)