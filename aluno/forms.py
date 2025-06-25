from django import forms
from .models import ProdutoAdmin

class ProdutoAdminForm(forms.ModelForm):
    class Meta:
        model = ProdutoAdmin
        fields = ['status']
        widgets = {
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }