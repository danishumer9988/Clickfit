from django import forms
from django.core.validators import validate_email
from .models import Contact, Order, Subscriber, ProductReview

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'phone', 'order_reference', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Your Name',
                'class': 'form-input'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Your Email',
                'class': 'form-input'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Your Phone (optional)',
                'class': 'form-input'
            }),
            'order_reference': forms.TextInput(attrs={
                'placeholder': 'Order ID (if applicable)',
                'class': 'form-input'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select'
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Your Message',
                'rows': 5,
                'class': 'form-input'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name.strip()) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        return name.strip()

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message.strip()) < 10:
            raise forms.ValidationError("Message must be at least 10 characters long.")
        return message.strip()

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'email', 'phone', 'address', 'payment_method']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Full Name',
                'class': 'form-input'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email Address',
                'class': 'form-input'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Phone Number',
                'class': 'form-input'
            }),
            'address': forms.Textarea(attrs={
                'placeholder': 'Delivery Address',
                'rows': 3,
                'class': 'form-input'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))

        if len(phone) < 10:
            raise forms.ValidationError("Please enter a valid phone number with at least 10 digits.")

        return phone

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if len(address.strip()) < 10:
            raise forms.ValidationError("Please provide a complete address.")
        return address.strip()

class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['email', 'name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email',
                'class': 'form-input'
            }),
            'name': forms.TextInput(attrs={
                'placeholder': 'Your Name (optional)',
                'class': 'form-input'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        validate_email(email)

        # Check if email already exists and is active
        if Subscriber.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError("This email is already subscribed to our newsletter.")
        return email

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['name', 'email', 'rating', 'title', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Your Name',
                'class': 'form-input'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Your Email',
                'class': 'form-input'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Review Title',
                'class': 'form-input'
            }),
            'comment': forms.Textarea(attrs={
                'placeholder': 'Your Review',
                'rows': 4,
                'class': 'form-input'
            }),
            'rating': forms.HiddenInput(),  # We'll handle rating with JavaScript
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if not rating or rating < 1 or rating > 5:
            raise forms.ValidationError("Please select a valid rating.")
        return rating

# Enhanced product search/filter form
class ProductFilterForm(forms.Form):
    CATEGORY_CHOICES = [
        ('', 'All Categories'),
        ('Menswear', 'Menswear'),
        ('Womenswear', 'Womenswear'),
        ('Electronics', 'Electronics'),
        ('Accessories', 'Accessories'),
    ]

    SORT_CHOICES = [
        ('', 'Default Sorting'),
        ('price_asc', 'Price: Low to High'),
        ('price_desc', 'Price: High to Low'),
        ('name_asc', 'Name: A to Z'),
        ('name_desc', 'Name: Z to A'),
        ('newest', 'Newest First'),
        ('rating', 'Highest Rated'),
    ]

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'this.form.submit()'
        })
    )

    price_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min Price',
            'class': 'form-input',
            'min': '0',
            'step': '0.01'
        })
    )

    price_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max Price',
            'class': 'form-input',
            'min': '0',
            'step': '0.01'
        })
    )

    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'this.form.submit()'
        })
    )

    in_stock = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox',
            'onchange': 'this.form.submit()'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        price_min = cleaned_data.get('price_min')
        price_max = cleaned_data.get('price_max')

        if price_min and price_max and price_min > price_max:
            raise forms.ValidationError("Minimum price cannot be greater than maximum price.")

        return cleaned_data

# Form for newsletter subscription (simplified version)
class NewsletterSubscriptionForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email for updates',
            'class': 'form-input'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        validate_email(email)
        return email