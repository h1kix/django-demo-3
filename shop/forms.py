from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'manufacturer', 'supplier', 'unit', 'price', 'discount', 'quantity', 'image']

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Цена не может быть отрицательной')
        return price

    def clean_quantity(self):
        q = self.cleaned_data.get('quantity')
        if q is not None and q < 0:
            raise forms.ValidationError('Количество не может быть отрицательным')
        return q
