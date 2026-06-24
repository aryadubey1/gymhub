from django import forms
from django.core.validators import RegexValidator
from .models import Member, Payment, Membership, Plan


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['name', 'phone', 'address', 'dob', 'profile_photo', 'status', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].validators = [
            RegexValidator(r'^\d{10}$', 'Phone must be exactly 10 digits')
        ]


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Amount'}),
            'method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError('Amount must be positive')
        return amount


class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['plan', 'start_date']
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class RenewWithPaymentForm(forms.Form):
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.none(),  # overridden in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Plan'
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Start Date'
    )
    amount = forms.DecimalField(
        max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Amount'}),
        label='Amount (₹)'
    )
    method = forms.ChoiceField(
        choices=Payment.METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Payment Method'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'}),
        label='Notes'
    )

    def __init__(self, *args, **kwargs):
        gym = kwargs.pop('gym', None)
        super().__init__(*args, **kwargs)
        if gym:
            self.fields['plan'].queryset = Plan.objects.unscoped().filter(gym=gym, is_active=True)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError('Amount must be positive')
        return amount


class MemberWithMembershipForm(forms.ModelForm):
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.none(),  # overridden in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Plan'
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Start Date'
    )

    class Meta:
        model = Member
        fields = ['name', 'phone', 'address', 'dob', 'profile_photo', 'status', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }

    def __init__(self, *args, **kwargs):
        gym = kwargs.pop('gym', None)
        super().__init__(*args, **kwargs)
        if gym:
            self.fields['plan'].queryset = Plan.objects.unscoped().filter(gym=gym, is_active=True)
        self.fields['phone'].validators = [
            RegexValidator(r'^\d{10}$', 'Phone must be exactly 10 digits')
        ]