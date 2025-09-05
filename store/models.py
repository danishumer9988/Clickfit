from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import json

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Menswear', 'Menswear'),
        ('Womenswear', 'Womenswear'),
        ('Electronics', 'Electronics'),
        ('Accessories', 'Accessories'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='products/')
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # New fields for enhanced product management
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text="Weight in kg")
    dimensions = models.CharField(max_length=50, blank=True, null=True, help_text="Format: LxWxH in cm")
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0,
                                 validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['price']),
            models.Index(fields=['stock']),
        ]

    def __str__(self):
        return f"{self.name} (SKU: {self.sku or 'N/A'})"

    def clean(self):
        if self.stock < 0:
            raise ValidationError({'stock': 'Stock cannot be negative.'})

    def save(self, *args, **kwargs):
        # Generate SKU if not provided
        if not self.sku:
            category_prefix = self.category[:3].upper()
            self.sku = f"{category_prefix}-{self.id or 'NEW'}"
        super().save(*args, **kwargs)

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def low_stock(self):
        return 0 < self.stock <= 10

class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    items = models.TextField()  # JSON string of cart items
    total = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # New fields for enhanced order management
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    shipping_cost = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    final_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['email']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"Order #{self.id} by {self.name} - {self.status}"

    def save(self, *args, **kwargs):
        # Calculate final total
        self.final_total = self.total + self.shipping_cost + self.tax_amount - self.discount_amount
        super().save(*args, **kwargs)

    def get_items(self):
        """Return parsed cart items"""
        try:
            return json.loads(self.items)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_item_count(self):
        """Return total number of items in order"""
        items = self.get_items()
        return sum(item.get('quantity', 0) for item in items)

    def can_be_cancelled(self):
        return self.status in ['pending', 'confirmed']

class Contact(models.Model):
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('product', 'Product Question'),
        ('order', 'Order Issue'),
        ('return', 'Return/Exchange'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='general')
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # New fields for better contact management
    phone = models.CharField(max_length=15, blank=True, null=True)
    order_reference = models.CharField(max_length=50, blank=True, null=True, help_text="Order ID if related to an order")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'

    def __str__(self):
        return f"Message from {self.name} - {self.get_subject_display()}"

    def resolve(self):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # New fields for better subscriber management
    name = models.CharField(max_length=100, blank=True, null=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=50, blank=True, null=True, help_text="How did they subscribe?")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'

    def __str__(self):
        return self.email

    def unsubscribe(self):
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()

# New model for product reviews
class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'email']  # Prevent multiple reviews from same email

    def __str__(self):
        return f"Review for {self.product.name} by {self.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product rating when review is approved
        if self.is_approved:
            self.update_product_rating()

    def update_product_rating(self):
        approved_reviews = self.product.reviews.filter(is_approved=True)
        if approved_reviews.exists():
            avg_rating = approved_reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.product.rating = round(avg_rating, 1)
            self.product.review_count = approved_reviews.count()
            self.product.save()