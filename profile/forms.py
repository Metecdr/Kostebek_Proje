from django import forms
from .models import OgrenciProfili

# Sadece OgrenciProfili modelindeki 'alan' bilgisini düzenlemeye yarayan form
class ProfilDuzenleForm(forms.ModelForm):
    class Meta:
        model = OgrenciProfili
        # YENİ ALANLAR EKLENDİ
        fields = ['ad', 'soyad', 'hedef_puan', 'alan']
        
        # Form elemanlarına Bootstrap sınıfları ekleme
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control'}),
            'soyad': forms.TextInput(attrs={'class': 'form-control'}),
            'hedef_puan': forms.NumberInput(attrs={'class': 'form-control'}),
            'alan': forms.Select(attrs={'class': 'form-select'})
        }