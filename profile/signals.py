from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import OgrenciProfili 

# Yeni kullanıcı oluşturulduğunda bu fonksiyon çalışır
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Eğer kullanıcı YENİ oluşturulduysa (created=True)
    if created:
        # OgrenciProfili oluştur ve kullanıcıya bağla. 
        # (models.py'de related_name='profil' tanımladığımız için bu isim kullanılır)
        OgrenciProfili.objects.create(kullanici=instance)

# Kullanıcı güncellendiğinde (kaydedildiğinde) profilin de kaydedilmesini sağlar
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Hata veren satır: Artık 'ogrenciprofili' yerine 'profil' kullanıyoruz.
    instance.profil.save()