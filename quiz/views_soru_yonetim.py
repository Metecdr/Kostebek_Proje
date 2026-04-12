"""
Soru Yönetim Paneli Views
Superuser'lara özel soru ekleme, düzenleme, silme işlemleri.
"""
import json
import logging
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from quiz.models import Soru, Cevap, Konu, GununSorusu, GununSorusuCevap, SoruBildir

logger = logging.getLogger(__name__)


def superuser_required(view_func):
    """Sadece superuser erişebilir"""
    decorated = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='/giris/'
    )(view_func)
    return login_required(decorated)


# ==================== ANA PANEL ====================

@superuser_required
def soru_yonetim_anasayfa(request):
    """Soru yönetim paneli ana sayfası"""
    ders_filtre = request.GET.get('ders', '')
    sinav_filtre = request.GET.get('sinav', '')
    mod_filtre = request.GET.get('mod', '')
    arama = request.GET.get('q', '').strip()

    sorular = Soru.objects.prefetch_related('cevaplar').order_by('-id')

    if ders_filtre:
        sorular = sorular.filter(ders=ders_filtre)
    if sinav_filtre:
        sorular = sorular.filter(sinav_tipi=sinav_filtre)
    if mod_filtre == 'karsilasma':
        sorular = sorular.filter(karsilasmada_cikar=True)
    elif mod_filtre == 'bul_bakalim':
        sorular = sorular.filter(bul_bakalimda_cikar=True)
    if arama:
        sorular = sorular.filter(metin__icontains=arama)

    # İstatistikler
    toplam_soru = Soru.objects.count()
    ders_istatistikleri = (
        Soru.objects.values('ders')
        .annotate(sayi=Count('id'))
        .order_by('ders')
    )

    paginator = Paginator(sorular, 20)
    sayfa = request.GET.get('page', 1)
    sayfa_obj = paginator.get_page(sayfa)

    context = {
        'sorular': sayfa_obj,
        'toplam_soru': toplam_soru,
        'ders_istatistikleri': ders_istatistikleri,
        'ders_secenekleri': Soru.DERS_SECENEKLERI,
        'ders_filtre': ders_filtre,
        'sinav_filtre': sinav_filtre,
        'mod_filtre': mod_filtre,
        'arama': arama,
    }
    return render(request, 'quiz/soru_yonetim/anasayfa.html', context)


# ==================== SORU EKLEME ====================

@superuser_required
def soru_ekle(request):
    """Yeni soru ekle"""
    konular = Konu.objects.all().order_by('ders', 'isim')

    if request.method == 'POST':
        try:
            metin = request.POST.get('metin', '').strip()
            ders = request.POST.get('ders', '')
            sinav_tipi = request.POST.get('sinav_tipi', '')
            konu_id = request.POST.get('konu_id', 1)
            detayli_aciklama = request.POST.get('detayli_aciklama', '').strip()
            bul_bakalimda_cikar = request.POST.get('bul_bakalimda_cikar') == 'on'
            karsilasmada_cikar = request.POST.get('karsilasmada_cikar') == 'on'
            dogru_cevap_index = int(request.POST.get('dogru_cevap', 0))

            # Validasyon
            if not metin:
                messages.error(request, '❌ Soru metni boş bırakılamaz!')
                return render(request, 'quiz/soru_yonetim/soru_ekle.html', {
                    'ders_secenekleri': Soru.DERS_SECENEKLERI,
                    'konular': konular,
                    'post_data': request.POST,
                })

            # Cevapları topla
            cevaplar = []
            for i in range(1, 6):  # A, B, C, D, E (5 şık)
                cevap_metni = request.POST.get(f'cevap_{i}', '').strip()
                if cevap_metni:
                    cevaplar.append(cevap_metni)

            if len(cevaplar) < 2:
                messages.error(request, '❌ En az 2 şık girmelisiniz!')
                return render(request, 'quiz/soru_yonetim/soru_ekle.html', {
                    'ders_secenekleri': Soru.DERS_SECENEKLERI,
                    'konular': konular,
                    'post_data': request.POST,
                })

            if dogru_cevap_index < 0 or dogru_cevap_index >= len(cevaplar):
                messages.error(request, '❌ Geçerli bir doğru cevap seçin!')
                return render(request, 'quiz/soru_yonetim/soru_ekle.html', {
                    'ders_secenekleri': Soru.DERS_SECENEKLERI,
                    'konular': konular,
                    'post_data': request.POST,
                })

            # Konu al
            try:
                konu = Konu.objects.get(id=konu_id)
            except Konu.DoesNotExist:
                konu = Konu.objects.first()

            # Soruyu kaydet
            soru = Soru.objects.create(
                metin=metin,
                ders=ders,
                sinav_tipi=sinav_tipi,
                konu=konu,
                detayli_aciklama=detayli_aciklama,
                bul_bakalimda_cikar=bul_bakalimda_cikar,
                karsilasmada_cikar=karsilasmada_cikar,
            )

            for i, cevap_metni in enumerate(cevaplar):
                Cevap.objects.create(
                    soru=soru,
                    metin=cevap_metni,
                    dogru_mu=(i == dogru_cevap_index),
                )

            # Günün sorusu olarak ayarla
            if request.POST.get('gunun_sorusu_olarak_ayarla'):
                from datetime import date
                bonus_xp = max(5, min(50, int(request.POST.get('gunun_bonus_xp', 15) or 15)))
                GununSorusu.objects.update_or_create(
                    tarih=date.today(),
                    defaults={'soru': soru, 'bonus_xp': bonus_xp}
                )
                logger.info(f"☀️ Günün sorusu ayarlandı #{soru.id}")
                messages.success(request, f'✅ Soru #{soru.id} eklendi ve bugünün sorusu olarak ayarlandı!')
            else:
                logger.info(f"✅ Soru eklendi #{soru.id} - {ders} - {request.user.username}")
                messages.success(request, f'✅ Soru #{soru.id} başarıyla eklendi!')

            # Yeni soru ekle veya listeye dön
            if 'kaydet_ve_yeni' in request.POST:
                return redirect('soru_ekle')
            return redirect('soru_yonetim_anasayfa')

        except Exception as e:
            logger.error(f"Soru ekleme hatası: {e}", exc_info=True)
            messages.error(request, f'❌ Bir hata oluştu: {str(e)}')

    return render(request, 'quiz/soru_yonetim/soru_ekle.html', {
        'ders_secenekleri': Soru.DERS_SECENEKLERI,
        'konular': konular,
    })


# ==================== SORU DÜZENLEME ====================

@superuser_required
def soru_duzenle(request, soru_id):
    """Mevcut soruyu düzenle"""
    soru = get_object_or_404(Soru, id=soru_id)
    cevaplar = list(soru.cevaplar.all().order_by('id'))
    konular = Konu.objects.all().order_by('ders', 'isim')

    if request.method == 'POST':
        try:
            soru.metin = request.POST.get('metin', '').strip()
            soru.ders = request.POST.get('ders', '')
            soru.sinav_tipi = request.POST.get('sinav_tipi', '')
            soru.detayli_aciklama = request.POST.get('detayli_aciklama', '').strip()
            soru.bul_bakalimda_cikar = request.POST.get('bul_bakalimda_cikar') == 'on'
            soru.karsilasmada_cikar = request.POST.get('karsilasmada_cikar') == 'on'

            konu_id = request.POST.get('konu_id', 1)
            try:
                soru.konu = Konu.objects.get(id=konu_id)
            except Konu.DoesNotExist:
                pass

            if not soru.metin:
                messages.error(request, '❌ Soru metni boş bırakılamaz!')
            else:
                soru.save()

                # Cevapları güncelle
                dogru_cevap_index = int(request.POST.get('dogru_cevap', 0))
                soru.cevaplar.all().delete()

                for i in range(1, 6):
                    cevap_metni = request.POST.get(f'cevap_{i}', '').strip()
                    if cevap_metni:
                        Cevap.objects.create(
                            soru=soru,
                            metin=cevap_metni,
                            dogru_mu=(i - 1 == dogru_cevap_index),
                        )

                messages.success(request, f'✅ Soru #{soru.id} güncellendi!')
                return redirect('soru_yonetim_anasayfa')

        except Exception as e:
            logger.error(f"Soru düzenleme hatası: {e}", exc_info=True)
            messages.error(request, f'❌ Bir hata oluştu: {str(e)}')

    return render(request, 'quiz/soru_yonetim/soru_duzenle.html', {
        'soru': soru,
        'cevaplar': cevaplar,
        'ders_secenekleri': Soru.DERS_SECENEKLERI,
        'konular': konular,
    })


# ==================== SORU SİLME ====================

@superuser_required
def soru_sil(request, soru_id):
    """Soruyu sil"""
    soru = get_object_or_404(Soru, id=soru_id)
    if request.method == 'POST':
        soru_metin = soru.metin[:50]
        soru.delete()
        messages.success(request, f'🗑️ Soru silindi: "{soru_metin}..."')
        return redirect('soru_yonetim_anasayfa')
    return render(request, 'quiz/soru_yonetim/soru_sil_onay.html', {'soru': soru})


# ==================== TOPLU METIN PARSE ====================

@superuser_required
def toplu_metin_ekle(request):
    """
    Belirli formatta metin yapıştır → otomatik parse et → önizle → kaydet
    Format:
    SORU: Soru metni buraya...
    A) Birinci şık
    B) İkinci şık
    C) Üçüncü şık
    D) Dördüncü şık
    E) Beşinci şık (isteğe bağlı)
    DOGRU: B
    ACIKLAMA: Açıklama metni (isteğe bağlı)
    ---
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX: metin parse et, önizleme döndür
        try:
            data = json.loads(request.body)
            metin_blok = data.get('metin', '')
            ders = data.get('ders', '')
            sinav_tipi = data.get('sinav_tipi', '')

            parsed = _parse_toplu_metin(metin_blok)
            return JsonResponse({'success': True, 'sorular': parsed, 'ders': ders, 'sinav_tipi': sinav_tipi})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    elif request.method == 'POST':
        # Onaylanan soruları kaydet
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else None
            if not data:
                sorular_json = request.POST.get('sorular_json', '[]')
                sorular = json.loads(sorular_json)
                ders = request.POST.get('ders', '')
                sinav_tipi = request.POST.get('sinav_tipi', '')
                bul_bakalimda_cikar = request.POST.get('bul_bakalimda_cikar') == 'on'
                karsilasmada_cikar = request.POST.get('karsilasmada_cikar') == 'on'
            else:
                sorular = data.get('sorular', [])
                ders = data.get('ders', '')
                sinav_tipi = data.get('sinav_tipi', '')
                bul_bakalimda_cikar = data.get('bul_bakalimda_cikar', True)
                karsilasmada_cikar = data.get('karsilasmada_cikar', True)

            konu_id = data.get('konu_id') if data else request.POST.get('konu_id')
            try:
                konu = Konu.objects.get(id=konu_id) if konu_id else Konu.objects.first()
            except Konu.DoesNotExist:
                konu = Konu.objects.first()
            eklenen = 0

            for s in sorular:
                if not s.get('metin') or not s.get('cevaplar'):
                    continue
                soru = Soru.objects.create(
                    metin=s['metin'],
                    ders=ders,
                    sinav_tipi=sinav_tipi,
                    konu=konu,
                    detayli_aciklama=s.get('aciklama', ''),
                    bul_bakalimda_cikar=bul_bakalimda_cikar,
                    karsilasmada_cikar=karsilasmada_cikar,
                )
                for i, cevap in enumerate(s['cevaplar']):
                    Cevap.objects.create(
                        soru=soru,
                        metin=cevap['metin'],
                        dogru_mu=cevap['dogru'],
                    )
                eklenen += 1

            if request.content_type == 'application/json':
                return JsonResponse({'success': True, 'eklenen': eklenen})

            messages.success(request, f'✅ {eklenen} soru başarıyla eklendi!')
            return redirect('soru_yonetim_anasayfa')

        except Exception as e:
            logger.error(f"Toplu ekleme hatası: {e}", exc_info=True)
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': str(e)})
            messages.error(request, f'❌ Hata: {str(e)}')

    return render(request, 'quiz/soru_yonetim/toplu_metin_ekle.html', {
        'ders_secenekleri': Soru.DERS_SECENEKLERI,
    })


def _parse_toplu_metin(metin_blok):
    """
    İki format desteklenir:

    FORMAT 1 - Çok satırlı:
        SORU: Soru metni...
        A) Şık A
        B) Şık B
        DOGRU: B
        ACIKLAMA: Açıklama
        ---

    FORMAT 2 - Tek/karma satır (şıklar soru metninin içinde inline):
        SORU: Uzun paragraf... A) şık B) şık DOGRU: B ACIKLAMA: açıklama
        ---
    """
    import re
    sorular = []
    bloklar = [b.strip() for b in metin_blok.split('---') if b.strip()]

    for blok in bloklar:
        blok = blok.strip()
        if not blok:
            continue

        soru_metin = ''
        cevaplar = []
        dogru_harf = ''
        aciklama = ''

        # ---- 1) DOGRU: ve ACIKLAMA: etiketlerini bul ----
        dogru_m = re.search(r'DOGRU\s*:\s*([A-Ea-e])', blok, re.IGNORECASE)
        aciklama_m = re.search(r'ACIKLAMA\s*:', blok, re.IGNORECASE)

        if dogru_m:
            dogru_harf = dogru_m.group(1).upper()
        if aciklama_m:
            aciklama = blok[aciklama_m.end():].strip()
            # Eğer DOGRU: aciklamadan SONRA geliyorsa kes
            if dogru_m and dogru_m.start() > aciklama_m.start():
                aciklama = blok[aciklama_m.end():dogru_m.start()].strip()

        # ---- 2) SORU: etiketini bul ----
        soru_m = re.search(r'SORU\s*:\s*', blok, re.IGNORECASE)
        if not soru_m:
            continue
        sonrasi = blok[soru_m.end():]

        # ---- 3) Şıkları bul ----
        # "A)" veya "A." şeklinde başlayan kısımları bul
        # Sınır: sonraki şık harfi, DOGRU:, ACIKLAMA: veya metin sonu
        sik_re = re.compile(r'\b([A-Ea-e])\s*[).][ \t]')
        sik_pozisyonlari = [(m.start(), m.group(1).upper()) for m in sik_re.finditer(sonrasi)]

        # Eğer hiç şık bulunamazsa çok satırlı formatı dene
        if not sik_pozisyonlari:
            satirlar = blok.split('\n')
            soru_devam = False
            for satir in satirlar:
                satir = satir.strip()
                if not satir:
                    continue
                upper_s = satir.upper()
                if upper_s.startswith('SORU:'):
                    soru_metin = satir[5:].strip()
                    soru_devam = True
                elif upper_s.startswith('DOGRU:'):
                    dogru_harf = satir[6:].strip().upper()
                    soru_devam = False
                elif upper_s.startswith('ACIKLAMA:'):
                    aciklama = satir[9:].strip()
                    soru_devam = False
                elif (len(satir) > 2 and satir[0].upper() in 'ABCDE'
                      and satir[1] in ').'):
                    harf = satir[0].upper()
                    cevap_metin = satir[2:].strip()
                    cevaplar.append({'harf': harf, 'metin': cevap_metin, 'dogru': False})
                    soru_devam = False
                elif soru_devam:
                    soru_metin += '\n' + satir
            for c in cevaplar:
                c['dogru'] = (c['harf'] == dogru_harf)
        else:
            # Soru metni = SORU:'dan ilk şık başlangıcına kadar
            ilk_sik_pos = sik_pozisyonlari[0][0]
            soru_metin = sonrasi[:ilk_sik_pos].strip()

            # Her şık: şu anki pozisyondan sonraki şık/DOGRU/ACIKLAMA'ya kadar
            durdurucular = []
            for pos, _ in sik_pozisyonlari[1:]:
                durdurucular.append(pos)
            # DOGRU: ve ACIKLAMA: da durdurucu
            for pat in [r'DOGRU\s*:', r'ACIKLAMA\s*:']:
                m2 = re.search(pat, sonrasi, re.IGNORECASE)
                if m2:
                    durdurucular.append(m2.start())
            durdurucular.append(len(sonrasi))

            for i, (pos, harf) in enumerate(sik_pozisyonlari):
                # Bu şıktan sonraki en yakın durdurucu
                bitis = min(d for d in durdurucular if d > pos)
                # Şık metnini al (harf ve ) karakterinden sonrası)
                sik_baslangic = pos + 2  # harf + ")" veya "."  + boşluk = 3 char ama değişken
                # regex match'ten sonraki konumu bul
                m3 = sik_re.search(sonrasi, pos)
                if m3:
                    sik_baslangic = m3.end()
                cevap_metin = sonrasi[sik_baslangic:bitis].strip()
                if cevap_metin:
                    cevaplar.append({
                        'harf': harf,
                        'metin': cevap_metin,
                        'dogru': (harf == dogru_harf),
                    })

        if soru_metin and cevaplar:
            sorular.append({
                'metin': soru_metin.strip(),
                'cevaplar': cevaplar,
                'aciklama': aciklama.strip(),
                'dogru_harf': dogru_harf,
            })

    return sorular


# ==================== AJAX: DERS'E GÖRE KONULAR ====================

@superuser_required
def konular_by_ders(request):
    """AJAX - Seçilen derse göre konu listesi döner"""
    ders = request.GET.get('ders', '')
    if not ders:
        return JsonResponse({'konular': []})
    konular = list(
        Konu.objects.filter(ders=ders).order_by('sira', 'isim').values('id', 'isim')
    )
    return JsonResponse({'konular': konular})


# ==================== GÜNÜN SORUSU YÖNETİMİ ====================

@superuser_required
def gunun_sorusu_yonetim(request):
    """Günün sorusunu ayarla (admin)"""
    from datetime import date
    bugunun_sorusu = GununSorusu.objects.filter(tarih=date.today()).first()

    if request.method == 'POST':
        soru_id = request.POST.get('soru_id')
        bonus_xp = int(request.POST.get('bonus_xp', 15))
        try:
            soru = Soru.objects.get(id=soru_id)
            GununSorusu.objects.update_or_create(
                tarih=date.today(),
                defaults={'soru': soru, 'bonus_xp': bonus_xp}
            )
            messages.success(request, f'✅ Günün sorusu güncellendi: #{soru.id}')
        except Soru.DoesNotExist:
            messages.error(request, '❌ Soru bulunamadı.')
        return redirect('gunun_sorusu_yonetim')

    son_sorular = Soru.objects.order_by('-id')[:50]
    return render(request, 'quiz/soru_yonetim/gunun_sorusu_yonetim.html', {
        'bugunun_sorusu': bugunun_sorusu,
        'son_sorular': son_sorular,
    })


# ==================== SORU BİLDİR ====================

@login_required
def soru_bildir(request, soru_id):
    """Hatalı/yanlış soru bildirimi"""
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)

    soru = get_object_or_404(Soru, id=soru_id)
    sebep_kodu = request.POST.get('sebep_kodu', 'diger')
    aciklama = request.POST.get('aciklama', '').strip()[:300]

    # Aynı kullanıcı aynı soruyu 24 saatte bir kez bildirebilir
    from django.utils import timezone
    from datetime import timedelta
    son_bildirim = SoruBildir.objects.filter(
        kullanici=request.user,
        soru=soru,
        tarih__gte=timezone.now() - timedelta(hours=24)
    ).exists()

    if son_bildirim:
        return JsonResponse({'ok': False, 'hata': 'Bu soruyu zaten bildirdiniz.'})

    SoruBildir.objects.create(
        kullanici=request.user,
        soru=soru,
        sebep_kodu=sebep_kodu,
        aciklama=aciklama,
    )
    return JsonResponse({'ok': True})


@superuser_required
def soru_bildirimleri_listesi(request):
    """Admin - tüm bildirimleri listele"""
    bildirimler = SoruBildir.objects.select_related('soru', 'kullanici').order_by('-tarih')
    return render(request, 'quiz/soru_yonetim/soru_bildirimleri.html', {
        'bildirimler': bildirimler,
    })


@superuser_required
def soru_bildirim_incele(request, bildirim_id):
    """Bildirimi incelendi olarak işaretle"""
    bildirim = get_object_or_404(SoruBildir, id=bildirim_id)
    bildirim.incelendi = True
    bildirim.save()
    return JsonResponse({'ok': True})
