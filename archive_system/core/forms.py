from django import forms
from .models import Document, Profile


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'category', 'security_level', 'file']

        # Делаем красоту (добавляем CSS классы к полям)
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название документа'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'security_level': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Название',
            'category': 'Категория',
            'security_level': 'Уровень секретности',
            'file': 'Файл документа',
        }

# 👇 НОВАЯ ФОРМА ДЛЯ АВАТАРКИ
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']