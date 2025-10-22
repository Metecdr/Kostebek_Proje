from django import forms
from .models import OgrenciProfili

class ProfilDuzenleForm(forms.ModelForm):
    class Meta:
        model = OgrenciProfili
        fields = ['ad', 'soyad', 'hedef_puan', 'alan']
        
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adınız'}),
            'soyad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soyadınız'}),
            'hedef_puan': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Hedef puanınız', 'min': 0, 'max': 1000}),
            'alan': forms.Select(attrs={'class': 'form-select'})
        }
        
        labels = {
            'ad': 'Ad',
            'soyad': 'Soyad',
            'hedef_puan': 'Hedef Puan',
            'alan': 'Alan'
        }