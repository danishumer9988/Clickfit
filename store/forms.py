from django import forms
from captcha.fields import CaptchaField
from .models import Transaction

class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)
    city = forms.CharField(max_length=50)
    province = forms.CharField(max_length=50)
    postal_code = forms.CharField(max_length=20)

    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect,
        initial='COD'
    )

    captcha = CaptchaField()

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')

        if payment_method == 'JAZZCASH':
            if not transaction_id:
                raise forms.ValidationError("Transaction ID is required for JazzCash/Easypaisa payment.")

            try:
                transaction = Transaction.objects.get(transaction_id=transaction_id)
                if transaction.status == 'USED':
                    raise forms.ValidationError("This transaction ID has already been used. Please enter a valid ID.")
            except Transaction.DoesNotExist:
                raise forms.ValidationError("Invalid transaction ID. Please enter a valid ID.")

        return cleaned_data
