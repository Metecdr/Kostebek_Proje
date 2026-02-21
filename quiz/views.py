from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from profile.models import OyunModuIstatistik
from profile.rozet_kontrol import rozet_kontrol_yap
import logging

logger = logging.getLogger(__name__)


@login_required
def quiz_anasayfa(request):
    """Quiz ana sayfa - Oyun modları seçimi"""
    try:
        profil = request.user.profil
        cache_key = f'karsilasma_ist_{profil.id}'
        karsilasma_ist = cache.get(cache_key)
        
        if karsilasma_ist is None:
            karsilasma_ist = OyunModuIstatistik.objects.filter(profil=profil, oyun_modu='karsilasma').first()
            cache.set(cache_key, karsilasma_ist, 60)
        
        context = {'profil': profil, 'karsilasma_ist': karsilasma_ist}
    except AttributeError as e:
        logger.error(f"Quiz anasayfa profil hatası: {e}", exc_info=True)
        messages.error(request, 'Profil bilgilerinize erişilemiyor.')
        from django.shortcuts import redirect
        return redirect('profil')
    except Exception as e:
        logger.error(f"Quiz anasayfa beklenmeyen hata: {e}", exc_info=True)
        context = {}
    
    return render(request, 'quiz/anasayfa.html', context)