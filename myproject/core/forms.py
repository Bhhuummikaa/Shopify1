from django import forms
from .models import Addresses, Customers, FlaggedOrders, LineItems, Orders, Rules, Stores


class AddressForm(forms.ModelForm):
    class Meta:
        model = Addresses
        fields = '__all__'


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customers
        fields = '__all__'


class FlaggedOrderForm(forms.ModelForm):
    class Meta:
        model = FlaggedOrders
        fields = '__all__'


class LineItemForm(forms.ModelForm):
    class Meta:
        model = LineItems
        fields = '__all__'


class OrderForm(forms.ModelForm):
    class Meta:
        model = Orders
        fields = '__all__'


class RuleForm(forms.ModelForm):
    class Meta:
        model = Rules
        fields = '__all__'


class StoreForm(forms.ModelForm):
    class Meta:
        model = Stores
        fields = '__all__'


MODEL_CHOICES = [
    ('stores', 'Stores'),
    ('customers', 'Customers'),
    ('orders', 'Orders'),
    ('lineitems', 'Line Items'),
    ('addresses', 'Addresses'),
    ('rules', 'Rules'),
    ('flaggedorders', 'Flagged Orders'),
]

# class UploadFileForm(forms.Form):
#     model_name = forms.ChoiceField(choices=MODEL_CHOICES)
#     file = forms.FileField()
from django import forms

class UploadForm(forms.Form):
    file = forms.FileField(label='CSV File', widget=forms.FileInput(attrs={'accept': '.csv'}))