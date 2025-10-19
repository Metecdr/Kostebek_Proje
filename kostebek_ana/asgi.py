# asgi.py

import os
from django.core.asgi import get_asgi_application

# 1. Adım: Django'ya ayar dosyasının nerede olduğunu SÖYLE.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kostebek_ana.settings')

# 2. Adım: Önce Django'nun normal web dünyasını (HTTP) hazırlamasını bekle.
# Bu komut, Django'nun "uyanmasını" ve ayarlarını yüklemesini sağlar.
http_asgi_app = get_asgi_application()

# 3. Adım: Django artık uyanık olduğuna göre, GÜVENLE Channels'ın diğer parçalarını import et.
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import quiz.routing

# 4. Adım: Gelen trafiği doğru yerlere yönlendir.
application = ProtocolTypeRouter({
    # Normal web sayfası istekleri için, artık hazır olan Django'nun standart sistemini kullan.
    "http": http_asgi_app,
    
    # Gerçek zamanlı bağlantı istekleri için, Channels'ın özel sistemini kullan.
    "websocket": AuthMiddlewareStack(
        URLRouter(
            quiz.routing.websocket_urlpatterns
        )
    ),
})