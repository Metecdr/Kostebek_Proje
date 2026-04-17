from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db.models import Q, Count
from django.db import transaction
from datetime import timedelta
from .models import Turnuva, TurnuvaMaci, TurnuvaKatilim, KarsilasmaOdasi
from .helpers import get_random_soru_by_ders, turnuva_mac_bitir, turnuva_siralama_guncelle
import random
import logging

logger = logging.getLogger(__name__)

superuser_required = user_passes_test(lambda u: u.is_active and u.is_superuser)

DERS_SECENEKLERI_TURNUVA = [
    ('fizik', 'Fizik'), ('kimya', 'Kimya'), ('biyoloji', 'Biyoloji'),
    ('edebiyat', 'Edebiyat'), ('tarih', 'Tarih'), ('cografya', 'Coğrafya'),
    ('felsefe', 'Felsefe'), ('turkce', 'Türkçe'),
    ('karisik_sayisal', 'Karışık Sayısal'), ('karisik_sozel', 'Karışık Sözel'),
    ('karisik_ea', 'Karışık EA'), ('karisik_sozel_ayt', 'Karışık Sözel AYT'),
]


@login_required
@superuser_required
@transaction.atomic
def turnuva_yonetim(request):
    """Superuser-only turnuva yönetim paneli"""
    if request.method == 'POST':
        aksiyon = request.POST.get('aksiyon')

        if aksiyon == 'create':
            try:
                isim = request.POST.get('isim', '').strip()
                if not isim:
                    messages.error(request, 'Turnuva adı zorunludur.')
                    return redirect('turnuva_yonetim')

                aciklama = request.POST.get('aciklama', '').strip()
                sinav_tipi = request.POST.get('sinav_tipi', 'TYT')
                ders = request.POST.get('ders', 'karisik_sayisal')
                toplam_soru = int(request.POST.get('toplam_soru', 5))
                max_katilimci = int(request.POST.get('max_katilimci', 16))
                odul_1 = int(request.POST.get('odul_1', 100))
                odul_2 = int(request.POST.get('odul_2', 50))
                odul_3 = int(request.POST.get('odul_3', 25))

                # Tarihler
                baslangic_str = request.POST.get('baslangic_tarihi')
                bitis_str = request.POST.get('bitis_tarihi')
                baslangic = None
                bitis = None
                if baslangic_str:
                    dt = parse_datetime(baslangic_str)
                    if dt:
                        baslangic = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                if bitis_str:
                    dt = parse_datetime(bitis_str)
                    if dt:
                        bitis = timezone.make_aware(dt) if timezone.is_naive(dt) else dt

                t = Turnuva.objects.create(
                    isim=isim, aciklama=aciklama, sinav_tipi=sinav_tipi,
                    ders=ders, toplam_soru=toplam_soru, max_katilimci=max_katilimci,
                    odul_birinci=odul_1, odul_ikinci=odul_2, odul_ucuncu=odul_3,
                    baslangic_tarihi=baslangic, bitis_tarihi=bitis,
                    durum='beklemede'
                )
                messages.success(request, f'✅ "{t.isim}" turnuvası oluşturuldu.')
            except Exception as e:
                messages.error(request, f'Hata: {e}')

        elif aksiyon == 'durum_degistir':
            tid = request.POST.get('turnuva_id')
            yeni_durum = request.POST.get('durum')
            try:
                t = Turnuva.objects.get(pk=tid)
                t.durum = yeni_durum
                t.save(update_fields=['durum'])
                messages.success(request, f'"{t.isim}" durumu → {yeni_durum}')
            except Turnuva.DoesNotExist:
                messages.error(request, 'Turnuva bulunamadı.')

        elif aksiyon == 'bracket_olustur':
            tid = request.POST.get('turnuva_id')
            try:
                t = Turnuva.objects.get(pk=tid)
                katilimcilar = list(TurnuvaKatilim.objects.filter(
                    turnuva=t, durum='aktif'
                ).select_related('kullanici'))
                if len(katilimcilar) < 2:
                    messages.error(request, 'Bracket için en az 2 katılımcı gerekli.')
                    return redirect('turnuva_yonetim')

                # Mevcut maçları temizle
                TurnuvaMaci.objects.filter(turnuva=t).delete()

                random.shuffle(katilimcilar)
                tur = 1
                for i in range(0, len(katilimcilar), 2):
                    o1 = katilimcilar[i].kullanici
                    if i + 1 < len(katilimcilar):
                        o2 = katilimcilar[i + 1].kullanici
                        TurnuvaMaci.objects.create(turnuva=t, tur=tur, oyuncu1=o1, oyuncu2=o2)
                    else:
                        # Tek kalan → bye (direkt geçiş)
                        TurnuvaMaci.objects.create(
                            turnuva=t, tur=tur, oyuncu1=o1, oyuncu2=None,
                            kazanan=o1, tamamlandi=True
                        )

                t.durum = 'basladi'
                t.save(update_fields=['durum'])
                messages.success(request, f'✅ "{t.isim}" bracket oluşturuldu, turnuva başladı!')
            except Turnuva.DoesNotExist:
                messages.error(request, 'Turnuva bulunamadı.')
            except Exception as e:
                messages.error(request, f'Bracket hatası: {e}')

        elif aksiyon == 'sil':
            tid = request.POST.get('turnuva_id')
            try:
                t = Turnuva.objects.get(pk=tid)
                isim = t.isim
                t.delete()
                messages.success(request, f'🗑️ "{isim}" silindi.')
            except Turnuva.DoesNotExist:
                messages.error(request, 'Turnuva bulunamadı.')

        return redirect('turnuva_yonetim')

    # GET
    turnuvalar = Turnuva.objects.annotate(
        katilimci_count=Count('turnuvakatilim', distinct=True),
        mac_count=Count('turnuvamaci', distinct=True)
    ).order_by('-olusturulma_tarihi')

    context = {
        'turnuvalar': turnuvalar,
        'ders_secenekleri': DERS_SECENEKLERI_TURNUVA,
        'durum_secenekleri': Turnuva.DURUM_CHOICES if hasattr(Turnuva, 'DURUM_CHOICES') else [
            ('beklemede', 'Beklemede'), ('kayit_acik', 'Kayıt Açık'),
            ('basladi', 'Başladı'), ('devam_ediyor', 'Devam Ediyor'), ('bitti', 'Bitti'),
        ],
    }
    return render(request, 'quiz/turnuva_yonetim.html', context)


@login_required
def turnuva_listesi(request):
    """Turnuva listesi sayfası - Optimize edilmiş"""
    try:
        now = timezone.now()
        
        logger.info(f"📊 TURNUVA LİSTESİ VIEW - Kullanıcı: {request.user.username}")
        
        # Kayıt açık turnuvalar
        kayit_acik = Turnuva.objects.filter(
            durum='kayit_acik'
        ).select_related().order_by('baslangic')
        
        # Devam eden turnuvalar
        devam_eden = Turnuva.objects.filter(
            Q(durum='basladi') | Q(durum='devam_ediyor')
        ).select_related('birinci', 'ikinci', 'ucuncu').order_by('baslangic')
        
        # Biten turnuvalar (son 10)
        biten = Turnuva.objects.filter(
            durum='bitti'
        ).select_related('birinci', 'ikinci', 'ucuncu').order_by('-bitis')[:10]
        
        # Katıldığım turnuvalar
        katildigim = Turnuva.objects.filter(
            katilimcilar=request.user
        ).select_related('birinci', 'ikinci', 'ucuncu').order_by('-baslangic')
        
        logger.info(f"   ✅ Kayıt Açık: {kayit_acik.count()}")
        logger.info(f"   ⚔️ Devam Eden: {devam_eden.count()}")
        logger.info(f"   🏁 Biten: {biten.count()}")
        logger.info(f"   ⭐ Katıldığım: {katildigim.count()}")
        
        context = {
            'kayit_acik': kayit_acik,
            'devam_eden': devam_eden,
            'biten': biten,
            'katildigim': katildigim
        }
        
        return render(request, 'quiz/turnuva_listesi.html', context)
    
    except Exception as e:
        logger.error(f"❌ Turnuva listesi hatası: {str(e)}", exc_info=True)
        messages.error(request, 'Turnuvalar yüklenirken bir hata oluştu.')
        return render(request, 'quiz/turnuva_listesi.html', {
            'kayit_acik': [],
            'devam_eden': [],
            'biten': [],
            'katildigim': []
        })


@login_required
def turnuva_detay(request, turnuva_id):
    """Turnuva detay sayfası - Optimize edilmiş"""
    try:
        # Turnuvayı al (ilişkili verilerle birlikte)
        turnuva = get_object_or_404(
            Turnuva.objects.select_related('birinci', 'ikinci', 'ucuncu'),
            turnuva_id=turnuva_id
        )
        
        logger.info(f"📋 TURNUVA DETAY: {turnuva.isim} - Kullanıcı: {request.user.username}")
        
        # Kullanıcı katıldı mı?
        katildi = turnuva.katilimcilar.filter(id=request.user.id).exists()
        
        # Maçları al (ilişkili verilerle birlikte)
        maclar = TurnuvaMaci.objects.filter(
            turnuva=turnuva
        ).select_related(
            'oyuncu1', 'oyuncu2', 'kazanan', 'karsilasma_oda'
        ).prefetch_related(
            'turnuva'
        ).order_by('round', 'olusturma_tarihi')
        
        # Bracket oluştur (round'a göre)
        bracket = {}
        for mac in maclar:
            round_name = mac.get_round_display()
            if round_name not in bracket:
                bracket[round_name] = []
            bracket[round_name].append(mac)
        
        # ✅ SIRALAMA TABLOSU AL
        siralama = None
        if turnuva.durum == 'bitti':
            from .models import TurnuvaSiralama
            siralama = TurnuvaSiralama.objects.filter(
                turnuva=turnuva
            ).select_related('kullanici').order_by('sira')
        
        logger.info(f"   Durum: {turnuva.durum}")
        logger.info(f"   Katılımcı: {turnuva.katilimci_sayisi}/{turnuva.max_katilimci}")
        logger.info(f"   Toplam maç: {maclar.count()}")
        logger.info(f"   Bracket roundları: {len(bracket)}")
        if siralama:
            logger.info(f"   Sıralama: {siralama.count()} kişi")
        
        context = {
            'turnuva': turnuva,
            'katildi': katildi,
            'maclar': maclar,
            'bracket': bracket,
            'siralama': siralama,  # ✅ YENİ
        }
        
        return render(request, 'quiz/turnuva_detay.html', context)
    
    except Turnuva.DoesNotExist:
        logger.error(f"❌ Turnuva bulunamadı: {turnuva_id}")
        messages.error(request, 'Turnuva bulunamadı.')
        return redirect('turnuva_listesi')
    
    except Exception as e:
        logger.error(f"❌ Turnuva detay hatası: {str(e)}", exc_info=True)
        messages.error(request, 'Turnuva bilgileri yüklenirken bir hata oluştu.')
        return redirect('turnuva_listesi')


@login_required
@transaction.atomic
def turnuva_katil(request, turnuva_id):
    """Turnuvaya katıl - Transaction korumalı"""
    try:
        # Turnuvayı kilitle (race condition önleme)
        turnuva = Turnuva.objects.select_for_update().get(turnuva_id=turnuva_id)
        
        logger.info(f"🎯 KATILIM İSTEĞİ: {request.user.username} -> {turnuva.isim}")
        
        # Kayıt açık mı?
        if not turnuva.kayit_acik_mi:
            messages.error(request, 'Bu turnuvaya kayıt yapılamaz!')
            logger.warning(f"   ❌ Kayıt kapalı! Durum: {turnuva.durum}")
            return redirect('turnuva_detay', turnuva_id=turnuva_id)
        
        # Zaten katıldı mı?
        if turnuva.katilimcilar.filter(id=request.user.id).exists():
            messages.warning(request, 'Bu turnuvaya zaten katıldınız!')
            logger.warning(f"   ⚠️ Zaten katılmış!")
            return redirect('turnuva_detay', turnuva_id=turnuva_id)
        
        # Dolu mu?
        if turnuva.dolu_mu:
            messages.error(request, 'Bu turnuva dolu!')
            logger.warning(f"   ❌ Dolu! {turnuva.katilimci_sayisi}/{turnuva.max_katilimci}")
            return redirect('turnuva_detay', turnuva_id=turnuva_id)
        
        # Katılımı kaydet
        sira = turnuva.katilimci_sayisi + 1
        
        TurnuvaKatilim.objects.create(
            turnuva=turnuva,
            kullanici=request.user,
            sira=sira
        )
        
        turnuva.katilimcilar.add(request.user)
        
        messages.success(request, f'✅ {turnuva.isim} turnuvasına başarıyla katıldınız!')
        logger.info(f"   ✅ Başarılı! Sıra: {sira}/{turnuva.max_katilimci}")
        
        # Turnuva doldu mu?
        if turnuva.dolu_mu:
            logger.info(f"   🏆 TURNUVA DOLDU! Otomatik bracket oluşturulabilir.")
        
        return redirect('turnuva_detay', turnuva_id=turnuva_id)
    
    except Turnuva.DoesNotExist:
        logger.error(f"❌ Turnuva bulunamadı: {turnuva_id}")
        messages.error(request, 'Turnuva bulunamadı.')
        return redirect('turnuva_listesi')
    
    except Exception as e:
        logger.error(f"❌ Katılım hatası: {str(e)}", exc_info=True)
        messages.error(request, 'Katılım sırasında bir hata oluştu.')
        return redirect('turnuva_listesi')


@login_required
@transaction.atomic
def turnuva_ayril(request, turnuva_id):
    """Turnuvadan ayrıl - Transaction korumalı"""
    try:
        turnuva = Turnuva.objects.select_for_update().get(turnuva_id=turnuva_id)
        
        logger.info(f"🚪 AYRILMA İSTEĞİ: {request.user.username} <- {turnuva.isim}")
        
        # Turnuva başladıysa ayrılamaz
        if turnuva.durum in ['basladi', 'devam_ediyor', 'bitti']:
            messages.error(request, 'Başlamış bir turnuvadan ayrılamazsınız!')
            logger.warning(f"   ❌ Turnuva durumu: {turnuva.durum}")
            return redirect('turnuva_detay', turnuva_id=turnuva_id)
        
        # Katıldı mı?
        if not turnuva.katilimcilar.filter(id=request.user.id).exists():
            messages.warning(request, 'Bu turnuvaya katılmamışsınız!')
            logger.warning(f"   ⚠️ Katılmamış!")
            return redirect('turnuva_detay', turnuva_id=turnuva_id)
        
        # Ayrıl
        turnuva.katilimcilar.remove(request.user)
        TurnuvaKatilim.objects.filter(turnuva=turnuva, kullanici=request.user).delete()
        
        messages.success(request, f'❌ {turnuva.isim} turnuvasından ayrıldınız.')
        logger.info(f"   ✅ Ayrılış başarılı!")
        
        return redirect('turnuva_detay', turnuva_id=turnuva_id)
    
    except Turnuva.DoesNotExist:
        logger.error(f"❌ Turnuva bulunamadı: {turnuva_id}")
        messages.error(request, 'Turnuva bulunamadı.')
        return redirect('turnuva_listesi')
    
    except Exception as e:
        logger.error(f"❌ Ayrılma hatası: {str(e)}", exc_info=True)
        messages.error(request, 'Ayrılma sırasında bir hata oluştu.')
        return redirect('turnuva_listesi')


@login_required
def turnuva_mac_baslat(request, mac_id):
    """Turnuva maçını başlat (ESKİ SİSTEM - Geriye uyumluluk için)"""
    try:
        mac = get_object_or_404(
            TurnuvaMaci.objects.select_related('turnuva', 'oyuncu1', 'oyuncu2'),
            mac_id=mac_id
        )

        logger.info(f"⚔️ MAÇ BAŞLAT (ESKİ): {request.user.username}")
        logger.warning("   ⚠️ Eski sistem kullanılıyor! Yeni sisteme yönlendir.")

        # Yeni sisteme yönlendir
        if mac.karsilasma_oda:
            messages.info(request, 'Maç için "Hazırım" butonunu kullanın.')
            return redirect('turnuva_mac_hazir', mac_id=mac.mac_id)
        else:
            messages.error(request, 'Maç henüz hazırlanmadı! Admin tarafından başlatılması bekleniyor.')
            return redirect('turnuva_detay', turnuva_id=mac.turnuva.turnuva_id)

    except Exception as e:
        logger.error(f"❌ Maç başlatma hatası: {str(e)}", exc_info=True)
        messages.error(request, 'Maç başlatılırken bir hata oluştu.')
        return redirect('turnuva_listesi')


@login_required
@transaction.atomic
def turnuva_mac_hazir(request, mac_id):
    """Oyuncu 'Hazırım' der - Transaction korumalı"""
    try:
        # KRİTİK FIX:
        # select_for_update ile birlikte select_related(nullable ilişki) kullanma.
        mac = TurnuvaMaci.objects.select_for_update().get(mac_id=mac_id)

        logger.info(
            f"🎮 HAZIR OL: {request.user.username} -> "
            f"{mac.oyuncu1.username if mac.oyuncu1 else '?'} vs "
            f"{mac.oyuncu2.username if mac.oyuncu2 else '?'}"
        )

        # Yetki kontrolü
        if request.user not in [mac.oyuncu1, mac.oyuncu2]:
            messages.error(request, 'Bu maçın oyuncusu değilsiniz!')
            logger.warning(f"   ❌ Yetkisiz! Kullanıcı: {request.user.username}")
            return redirect('turnuva_detay', turnuva_id=mac.turnuva.turnuva_id)

        # Maç durumu kontrolü
        if mac.tamamlandi:
            messages.warning(request, 'Bu maç zaten tamamlanmış!')
            logger.warning("   ⚠️ Maç tamamlanmış!")
            return redirect('turnuva_detay', turnuva_id=mac.turnuva.turnuva_id)

        # Oda kontrolü
        if not mac.karsilasma_oda:
            messages.error(request, 'Maç henüz hazırlanmadı! Lütfen bekleyin.')
            logger.warning("   ❌ Oda yok!")
            return redirect('turnuva_detay', turnuva_id=mac.turnuva.turnuva_id)
        
        # Zaman kontrolü
        now = timezone.now()
        if mac.mac_baslangic_zamani:
            baslama_penceresi_baslangic = mac.mac_baslangic_zamani - timedelta(minutes=5)
            baslama_penceresi_bitis = mac.mac_baslangic_zamani + timedelta(minutes=5)
            
            # Henüz erken mi?
            if now < baslama_penceresi_baslangic:
                kalan = baslama_penceresi_baslangic - now
                kalan_dakika = int(kalan.total_seconds() / 60)
                kalan_saniye = int(kalan.total_seconds() % 60)
                messages.warning(request, f'Maç henüz başlamadı! {kalan_dakika} dakika {kalan_saniye} saniye sonra hazırlanabilirsiniz.')
                logger.warning(f"   ⏰ Henüz erken! {kalan_dakika}:{kalan_saniye} kaldı")
                return redirect('turnuva_detay', turnuva_id=mac.turnuva.turnuva_id)
            
            # Geç kaldı mı?
            if now > baslama_penceresi_bitis:
                logger.warning(f"   ⏰ GEÇ KALINDI! Süre: {now - baslama_penceresi_bitis}")
                
                # Diğer oyuncu hazırsa otomatik hüsran
                if request.user == mac.oyuncu1 and mac.oyuncu2_hazir:
                    mac.oyuncu2_skor = 1000
                    mac.oyuncu1_skor = 0
                    turnuva_mac_bitir(mac, mac.oyuncu2)
                    messages.error(request, '⏰ Geç kaldınız! Rakibiniz maçı kazandı (Hüsran).')
                    logger.warning(f"   ❌ HÜSRAN: {request.user.username}")
                    return redirect('turnuva_detay', turnuva_id=mac.turnuva.turnuva_id)
                
                elif request.user == mac.oyuncu2 and mac.oyuncu1_hazir:
                    mac.oyuncu1_skor = 1000
                    mac.oyuncu2_skor = 0
                    turnuva_mac_bitir(mac, mac.oyuncu1)
                    messages.error(request, '⏰ Geç kaldınız! Rakibiniz maçı kazandı (Hüsran).')
                    logger.warning(f"   ❌ HÜSRAN: {request.user.username}")
                    return redirect('turnuva_detay', turnuva_id=mac.turnuva.turnuva_id)
        
        # Hazır olma işlemi
        if request.user == mac.oyuncu1:
            if mac.oyuncu1_hazir:
                messages.info(request, 'Zaten hazır oldunuz!')
                logger.info(f"   ♻️ Oyuncu 1 zaten hazır")
            else:
                mac.oyuncu1_hazir = True
                messages.success(request, '✅ Hazır oldunuz! Rakibiniz bekleniyor...')
                logger.info(f"   ✅ Oyuncu 1 hazır: {mac.oyuncu1.username}")
        else:
            if mac.oyuncu2_hazir:
                messages.info(request, 'Zaten hazır oldunuz!')
                logger.info(f"   ♻️ Oyuncu 2 zaten hazır")
            else:
                mac.oyuncu2_hazir = True
                messages.success(request, '✅ Hazır oldunuz! Rakibiniz bekleniyor...')
                logger.info(f"   ✅ Oyuncu 2 hazır: {mac.oyuncu2.username}")
        
        mac.save()
        
        # Her iki oyuncu da hazır mı?
        if mac.her_iki_oyuncu_hazir:
            logger.info(f"   🎮 HER İKİ OYUNCU HAZIR!")
            
            # Karşılaşma odasını başlat
            if mac.karsilasma_oda.oyun_durumu == 'bekleniyor':
                mac.karsilasma_oda.oyun_durumu = 'oynaniyor'
                mac.karsilasma_oda.soru_baslangic_zamani = timezone.now()
                mac.karsilasma_oda.save()
                logger.info(f"   🚀 MAÇ BAŞLATILDI!")
            
            messages.success(request, '🎮 Her iki oyuncu da hazır! Maç başlıyor...')
            return redirect('karsilasma_oyun', oda_id=mac.karsilasma_oda.oda_id)
        else:
            messages.success(request, '⏳ Hazır oldunuz! Rakibiniz bekleniyor...')
            return redirect('turnuva_mac_bekleme', mac_id=mac.mac_id)
    
    except TurnuvaMaci.DoesNotExist:
        logger.error(f"❌ Maç bulunamadı: {mac_id}")
        messages.error(request, 'Maç bulunamadı.')
        return redirect('turnuva_listesi')
    
    except Exception as e:
        logger.error(f"❌ Hazır olma hatası: {str(e)}", exc_info=True)
        messages.error(request, 'Bir hata oluştu. Lütfen tekrar deneyin.')
        return redirect('turnuva_listesi')


@login_required
def turnuva_mac_bekleme(request, mac_id):
    """Maç bekleme odası"""
    try:
        mac = get_object_or_404(
            TurnuvaMaci.objects.select_related('turnuva', 'oyuncu1', 'oyuncu2', 'karsilasma_oda'),
            mac_id=mac_id
        )

        logger.info(f"⏳ BEKLEME ODASI: {request.user.username}")

        # Yetki kontrolü
        if request.user not in [mac.oyuncu1, mac.oyuncu2]:
            messages.error(request, 'Bu maçın oyuncusu değilsiniz!')
            return redirect('turnuva_detay', turnuva_id=mac.turnuva.turnuva_id)

        # Her iki oyuncu da hazırsa maça git
        if mac.her_iki_oyuncu_hazir and mac.karsilasma_oda:
            logger.info("   ✅ Her iki oyuncu hazır! Maça yönlendiriliyor...")
            return redirect('karsilasma_oyun', oda_id=mac.karsilasma_oda.oda_id)

        # Durum bilgileri
        ben_hazir = (
            (request.user == mac.oyuncu1 and mac.oyuncu1_hazir) or
            (request.user == mac.oyuncu2 and mac.oyuncu2_hazir)
        )

        rakip_hazir = (
            (request.user == mac.oyuncu1 and mac.oyuncu2_hazir) or
            (request.user == mac.oyuncu2 and mac.oyuncu1_hazir)
        )

        rakip = mac.oyuncu2 if request.user == mac.oyuncu1 else mac.oyuncu1
        logger.info(f"   Ben: {ben_hazir}, Rakip ({rakip.username if rakip else '?'}): {rakip_hazir}")

        context = {
            'mac': mac,
            'turnuva': mac.turnuva,
            'ben_hazir': ben_hazir,
            'rakip_hazir': rakip_hazir,
        }
        return render(request, 'quiz/turnuva_mac_bekleme.html', context)

    except TurnuvaMaci.DoesNotExist:
        logger.error(f"❌ Maç bulunamadı: {mac_id}")
        messages.error(request, 'Maç bulunamadı.')
        return redirect('turnuva_listesi')

    except Exception as e:
        logger.error(f"❌ Bekleme odası hatası: {str(e)}", exc_info=True)
        messages.error(request, 'Bir hata oluştu.')
        return redirect('turnuva_listesi')


@login_required
def turnuva_mac_sonuc(request, mac_id):
    """Turnuva maç sonucu sayfası"""
    try:
        mac = get_object_or_404(
            TurnuvaMaci.objects.select_related(
                'turnuva', 'oyuncu1', 'oyuncu2', 'kazanan', 'karsilasma_oda'
            ),
            mac_id=mac_id
        )

        # Yetki kontrolü
        if request.user not in [mac.oyuncu1, mac.oyuncu2] and not request.user.is_staff:
            messages.error(request, 'Bu maç sonucunu görüntüleme yetkiniz yok.')
            return redirect('turnuva_detay', turnuva_id=mac.turnuva.turnuva_id)

        oyuncu1_skor = mac.oyuncu1_skor if mac.oyuncu1_skor is not None else 0
        oyuncu2_skor = mac.oyuncu2_skor if mac.oyuncu2_skor is not None else 0

        # Eğer skorlar maçta yoksa, odadan fallback
        if mac.karsilasma_oda:
            if mac.oyuncu1_skor is None:
                oyuncu1_skor = mac.karsilasma_oda.oyuncu1_skor
            if mac.oyuncu2_skor is None:
                oyuncu2_skor = mac.karsilasma_oda.oyuncu2_skor

        context = {
            'mac': mac,
            'turnuva': mac.turnuva,
            'oyuncu1': mac.oyuncu1,
            'oyuncu2': mac.oyuncu2,
            'oyuncu1_skor': oyuncu1_skor,
            'oyuncu2_skor': oyuncu2_skor,
            'kazanan': mac.kazanan,
            'berabere': bool(mac.tamamlandi and oyuncu1_skor == oyuncu2_skor),
        }

        return render(request, 'quiz/turnuva_mac_sonuc.html', context)

    except TurnuvaMaci.DoesNotExist:
        logger.error(f"❌ Maç bulunamadı: {mac_id}")
        messages.error(request, 'Maç bulunamadı.')
        return redirect('turnuva_listesi')

    except Exception as e:
        logger.error(f"❌ Maç sonucu hatası: {str(e)}", exc_info=True)
        messages.error(request, 'Maç sonucu yüklenirken bir hata oluştu.')
        return redirect('turnuva_listesi')