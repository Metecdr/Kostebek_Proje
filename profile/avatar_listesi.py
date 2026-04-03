# Avatar Sistemi - Ücretsiz ve premium avatarlar

VARSAYILAN_AVATAR = '🦔'

# Herkesin ücretsiz kullanabileceği avatarlar
UCRETSIZ_AVATARLAR = [
    {'id': 'kirpi',   'emoji': '🦔', 'isim': 'Kirpi'},
    {'id': 'kurt',    'emoji': '🐺', 'isim': 'Kurt'},
    {'id': 'tilki',   'emoji': '🦊', 'isim': 'Tilki'},
    {'id': 'kurbaga', 'emoji': '🐸', 'isim': 'Kurbağa'},
    {'id': 'ayi',     'emoji': '🐻', 'isim': 'Ayı'},
    {'id': 'kaplan',  'emoji': '🐯', 'isim': 'Kaplan'},
    {'id': 'aslan',   'emoji': '🦁', 'isim': 'Aslan'},
    {'id': 'panda',   'emoji': '🐼', 'isim': 'Panda'},
    {'id': 'baykus',  'emoji': '🦉', 'isim': 'Baykuş'},
    {'id': 'penguen', 'emoji': '🐧', 'isim': 'Penguen'},
    {'id': 'koala',   'emoji': '🐨', 'isim': 'Koala'},
    {'id': 'rakun',   'emoji': '🦝', 'isim': 'Rakun'},
]

# Ücretsiz avatar emojileri (hızlı kontrol için)
UCRETSIZ_EMOJI_SETI = {a['emoji'] for a in UCRETSIZ_AVATARLAR}


def avatar_gecerli_mi(emoji, satin_alinan_emojiler=None):
    """Avatar kullanıcı tarafından kullanılabilir mi?"""
    if emoji in UCRETSIZ_EMOJI_SETI:
        return True
    if satin_alinan_emojiler and emoji in satin_alinan_emojiler:
        return True
    return False
