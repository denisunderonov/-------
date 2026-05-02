"""Формы CRUD для моделей приложения shop."""
from django import forms

from .models import Product, Promotion


class ProductForm(forms.ModelForm):
    """Форма создания и редактирования товара."""

    class Meta:
        model = Product
        fields = [
            'title',
            'description',
            'size',
            'price',
            'condition',
            'status',
            'storage_tier',
            'seller',
            'category',
            'brand',
            'warehouse_received_at',
            'photo',
            'quality_report',
            'source_url',
        ]
        widgets = {
            'warehouse_received_at': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['warehouse_received_at'].input_formats = ['%Y-%m-%dT%H:%M']


class PromotionForm(forms.ModelForm):
    """Форма создания и редактирования акции."""

    class Meta:
        model = Promotion
        fields = ['title', 'discount_percent', 'starts_at', 'ends_at']
        widgets = {
            'starts_at': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'},
            ),
            'ends_at': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['starts_at'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['ends_at'].input_formats = ['%Y-%m-%dT%H:%M']
