from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('profile', '0016_duyuru_modeli'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailDogrulamaToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('olusturma_tarihi', models.DateTimeField(auto_now_add=True)),
                ('kullanici', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='email_dogrulama_token',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Kullanıcı'
                )),
            ],
            options={
                'verbose_name': 'Email Doğrulama Token',
                'verbose_name_plural': 'Email Doğrulama Tokenları',
            },
        ),
    ]
