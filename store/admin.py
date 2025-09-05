from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from .models import Product, Order, Contact, Subscriber, ProductReview

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'in_stock', 'low_stock', 'rating', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at', 'stock']
    search_fields = ['name', 'description', 'sku']
    readonly_fields = ['created_at', 'updated_at', 'rating', 'review_count']
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'description', 'category', 'sku']
        }),
        ('Pricing & Inventory', {
            'fields': ['price', 'stock', 'is_active']
        }),
        ('Product Details', {
            'fields': ['image', 'weight', 'dimensions']
        }),
        ('Ratings', {
            'fields': ['rating', 'review_count']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    actions = ['activate_products', 'deactivate_products', 'clear_stock']

    def in_stock(self, obj):
        return obj.in_stock
    in_stock.boolean = True
    in_stock.short_description = 'In Stock'

    def low_stock(self, obj):
        return obj.low_stock
    low_stock.boolean = True
    low_stock.short_description = 'Low Stock'

    def activate_products(self, request, queryset):
        queryset.update(is_active=True)
    activate_products.short_description = "Activate selected products"

    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_products.short_description = "Deactivate selected products"

    def clear_stock(self, request, queryset):
        queryset.update(stock=0)
    clear_stock.short_description = "Clear stock for selected products"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'payment_method', 'status', 'final_total', 'timestamp', 'item_count']
    list_filter = ['status', 'payment_method', 'timestamp']
    search_fields = ['name', 'email', 'phone', 'address', 'id']
    readonly_fields = ['timestamp', 'updated_at', 'final_total']
    fieldsets = [
        ('Customer Information', {
            'fields': ['name', 'email', 'phone', 'address']
        }),
        ('Order Details', {
            'fields': ['payment_method', 'status', 'tracking_number', 'notes']
        }),
        ('Financial Information', {
            'fields': ['total', 'shipping_cost', 'tax_amount', 'discount_amount', 'final_total']
        }),
        ('Items', {
            'fields': ['items'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['timestamp', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    def item_count(self, obj):
        return obj.get_item_count()
    item_count.short_description = 'Items'

    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "Mark selected as Processing"

    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_as_shipped.short_description = "Mark selected as Shipped"

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = "Mark selected as Delivered"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
    mark_as_cancelled.short_description = "Mark selected as Cancelled"

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_resolved', 'timestamp', 'order_reference']
    list_filter = ['subject', 'is_resolved', 'timestamp']
    search_fields = ['name', 'email', 'message', 'order_reference']
    readonly_fields = ['timestamp']
    fieldsets = [
        ('Contact Information', {
            'fields': ['name', 'email', 'phone', 'order_reference']
        }),
        ('Message Details', {
            'fields': ['subject', 'message']
        }),
        ('Resolution Status', {
            'fields': ['is_resolved', 'resolved_at']
        }),
        ('Timestamps', {
            'fields': ['timestamp'],
            'classes': ['collapse']
        }),
    ]
    actions = ['mark_as_resolved', 'mark_as_unresolved']

    def mark_as_resolved(self, request, queryset):
        for contact in queryset:
            contact.resolve()
    mark_as_resolved.short_description = "Mark selected as resolved"

    def mark_as_unresolved(self, request, queryset):
        queryset.update(is_resolved=False, resolved_at=None)
    mark_as_unresolved.short_description = "Mark selected as unresolved"

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'subscribed_at', 'source']
    list_filter = ['is_active', 'subscribed_at', 'source']
    search_fields = ['email', 'name']
    readonly_fields = ['subscribed_at', 'unsubscribed_at']
    actions = ['activate_subscribers', 'deactivate_subscribers']

    def activate_subscribers(self, request, queryset):
        queryset.update(is_active=True, unsubscribed_at=None)
    activate_subscribers.short_description = "Activate selected subscribers"

    def deactivate_subscribers(self, request, queryset):
        for subscriber in queryset:
            subscriber.unsubscribe()
    deactivate_subscribers.short_description = "Deactivate selected subscribers"

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['product__name', 'name', 'email', 'title']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_reviews', 'disapprove_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_reviews.short_description = "Disapprove selected reviews"

# Dashboard customization
admin.site.site_header = "E-Commerce Store Administration"
admin.site.site_title = "E-Commerce Store Admin Portal"
admin.site.index_title = "Welcome to E-Commerce Store Admin"