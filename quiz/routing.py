from django.urls import re_path
from quiz.consumers import KarsilasmaConsumer

websocket_urlpatterns = [
    re_path(r'ws/karsilasma/(?P<oda_id>[^/]+)/$', KarsilasmaConsumer.as_asgi()),
]
