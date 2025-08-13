from django.contrib import admin
from .models import (
    NewsletterSubscriber, ContactMessage, Product, Service, Order, OrderItem,
    CartItem, Cart, Notification, Wishlist, Transaction
)
from django.utils.html import format_html

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message', 'submitted_at')
    search_fields = ('name', 'email', 'message')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'category', 'created_at', 'ordered_in_orders')
    search_fields = ('name', 'description')
    list_filter = ('category', 'created_at')

    def ordered_in_orders(self, obj):
        order_items = OrderItem.objects.filter(product=obj)
        if order_items.exists():
            order_ids = set(item.order.id for item in order_items)
            return ", ".join(str(order_id) for order_id in order_ids)
        return "No Orders"

    ordered_in_orders.short_description = "Order IDs"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'name', 'email', 'phone',
        'total_price', 'payment_method', 'transaction_id', 'created_at', 'order_details'
    )
    readonly_fields = ['order_details']
    search_fields = ['id', 'name', 'phone', 'email', 'items__product__name', 'transaction_id']
    list_filter = ['created_at', 'city', 'province', 'payment_method']

    def order_details(self, obj):
        items = obj.items.all()
        return format_html("<br>".join([
            f"<b>{item.product.name}</b> (ID: {item.product.id}) x {item.quantity}"
            for item in items
        ]))

    order_details.short_description = "Order Details"

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title',)
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'amount', 'status', 'created_at')
    search_fields = ('transaction_id',)
    list_filter = ('status',)
