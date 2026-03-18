from django.utils import timezone


class SonAktifMiddleware:
    """
    Her request'te kullanıcının son_aktif alanını günceller.
    Çevrimiçi durumu takibi için kullanılır.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Sadece giriş yapmış kullanıcılar için
        if request.user.is_authenticated:
            try:
                profil = request.user.profil
                simdi = timezone.now()

                # ✅ Her 2 dakikada bir güncelle (performans için)
                # Her request'te DB'ye yazma - sadece 2 dk geçmişse yaz
                if (
                    not profil.son_aktif or
                    (simdi - profil.son_aktif).seconds > 120
                ):
                    profil.son_aktif = simdi
                    profil.save(update_fields=['son_aktif'])

            except Exception:
                pass  # Hata olursa sessizce geç

        return response