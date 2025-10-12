from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User 
from django.core.exceptions import ValidationError 
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import F, Count, Case, When, IntegerField
from .models import OgrenciProfili
from .forms import ProfilDuzenleForm
from quiz.models import KullaniciCevap, Konu
from utils.rewards import unvan_kontrol # Rozet kontrolü


# --- YARDIMCI VE ROZET FONKSİYONLARI (Aynı Kalır) ---
def unvan_kontrol(profil, kazanilan_puan):
    # ... (Fonksiyon gövdesi aynı kalır) ...
    guncel_unvanlar = profil.unvanlar.split(',')
    yeni_unvan = None
    if profil.toplam_puan + kazanilan_puan >= 500 and "Uzman Köstebek" not in guncel_unvanlar:
        yeni_unvan = "Uzman Köstebek"
    elif profil.toplam_puan + kazanilan_puan >= 200 and "Deneyimli Köstebek" not in guncel_unvanlar:
        yeni_unvan = "Deneyimli Köstebek"
    elif profil.toplam_puan + kazanilan_puan >= 50 and "Acemi Köstebek" not in guncel_unvanlar:
        yeni_unvan = "Acemi Köstebek"
    if yeni_unvan:
        if profil.unvanlar == "Yeni Köstebek":
            profil.unvanlar = yeni_unvan
        else:
            profil.unvanlar += f",{yeni_unvan}"


# --- OTURUM YÖNETİMİ (Aynı Kalır) ---
def anasayfa(request):
    if request.user.is_authenticated:
        return redirect('profil')
    return redirect('kayit')

def kayit_view(request):
    # ... (kod aynı kalır) ...
    if request.method == 'POST':
        kullanici_adi = request.POST.get('username')
        sifre = request.POST.get('password')
        email_adresi = request.POST.get('email')
        
        try:
            if User.objects.filter(username=kullanici_adi).exists():
                raise ValidationError("Bu kullanıcı adı zaten alınmıştır.")
            if User.objects.filter(email=email_adresi).exists():
                raise ValidationError("Bu e-posta adresi zaten kullanılmaktadır.")

            User.objects.create_user(username=kullanici_adi, email=email_adresi, password=sifre)
            return redirect('giris')
        
        except ValidationError as ve:
            return render(request, 'kayit.html', {'hata': ve.message})
        except Exception:
            return render(request, 'kayit.html', {'hata': 'Beklenmeyen bir hata oluştu.'})
            
    return render(request, 'kayit.html', {})

def giris_view(request):
    if request.method == 'POST':
        kullanici_adi = request.POST.get('username')
        sifre = request.POST.get('password')

        user = authenticate(request, username=kullanici_adi, password=sifre)
        
        if user is not None:
            login(request, user)
            return redirect('profil')
        else:
            return render(request, 'giris.html', {'hata': 'Kullanıcı adı veya şifre yanlış.'})
            
    return render(request, 'giris.html', {})

@login_required(login_url='giris')
def cikis_view(request):
    logout(request)
    return redirect('giris')


# --- PROFİL VE İSTATİSTİK İŞLEMLERİ ---

@login_required(login_url='giris')
def profil_view(request):
    profil = get_object_or_404(OgrenciProfili, kullanici=request.user)
    
    context = {
        'profil': profil,
        'kullanici': request.user,
        'basari_orani': profil.basari_orani()
    }
    return render(request, 'profil.html', context)


@login_required(login_url='giris')
def liderlik_view(request):
    """Tüm kullanıcıları puana ve alana göre sıralar."""
    # models.py'deki alan tercihlerini doğrudan çekiyoruz
    ALAN_TERCIHLERI = [('sayisal', 'Sayısal'), ('esit_agirlik', 'Eşit Ağırlık'), ('sozel', 'Sözel'), ('dil', 'Dil')]
    
    # URL'den tip ve alan parametrelerini al
    sirala_tipi = request.GET.get('tip', 'toplam') 
    alan_filtresi = request.GET.get('alan', 'genel') 
    
    liderler_query = OgrenciProfili.objects.all()

    # Filtreleme Mantığı: 'genel' değilse, seçilen alana göre filtrele
    if alan_filtresi != 'genel':
        liderler_query = liderler_query.filter(alan=alan_filtresi)

    # Sıralama Mantığı
    if sirala_tipi == 'haftalik':
        liderler = liderler_query.order_by('-haftalik_puan', '-toplam_puan')[:20]
    else:
        liderler = liderler_query.order_by('-toplam_puan')[:20]

    context = {
        'liderler': liderler,
        'sirala_tipi': sirala_tipi,
        'alan_filtresi': alan_filtresi,
        'alan_tercihleri': ALAN_TERCIHLERI, # HTML'e göndermek için
    }
    return render(request, 'liderlik_tablosu.html', context)


@login_required(login_url='giris')
def profil_duzenle_view(request):
    # ... (kod aynı kalır) ...
    profil = get_object_or_404(OgrenciProfili, kullanici=request.user)

    if request.method == 'POST':
        form = ProfilDuzenleForm(request.POST, instance=profil)
        if form.is_valid():
            form.save() 
            return redirect('profil') 
    else:
        form = ProfilDuzenleForm(instance=profil)
        
    context = {
        'form': form,
        'profil': profil
    }
    return render(request, 'profil_duzenle.html', context)


@login_required(login_url='giris')
def konu_istatistik_view(request):
    # ... (kod aynı kalır) ...
    from django.db.models import Count, Case, When, IntegerField, F
    
    cevaplar = KullaniciCevap.objects.filter(kullanici=request.user, soru__isnull=False)

    if not cevaplar.exists():
        return render(request, 'konu_istatistik.html', {'konu_istatistikleri': []})

    konu_istatistikleri = cevaplar.values(
        konu_adi=F('soru__konu__isim'),
        konu_id=F('soru__konu__id')
    ).annotate(
        toplam_cozulen = Count('id'),
        toplam_dogru = Count(Case(When(dogru=True, then=1), output_field=IntegerField())),
        toplam_yanlis = F('toplam_cozulen') - F('toplam_dogru')
    ).annotate(
        basari_orani = (F('toplam_dogru') * 100.0) / F('toplam_cozulen')
    ).order_by('basari_orani')

    context = {
        'konu_istatistikleri': konu_istatistikleri,
    }
    
    return render(request, 'konu_istatistik.html', context)