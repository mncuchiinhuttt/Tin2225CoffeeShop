from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Voucher 
from django.utils import timezone

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class VoucherForm(forms.Form):
    code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter voucher code'
    }))

    def clean_code(self):
        code = self.cleaned_data['code']
        try:
            voucher = Voucher.objects.get(
                code=code,
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )
            if voucher.usage_limit and voucher.times_used >= voucher.usage_limit:
                raise forms.ValidationError("This voucher has reached its usage limit.")
            return code
        except Voucher.DoesNotExist:
            raise forms.ValidationError("Invalid or expired voucher code.")