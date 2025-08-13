from django.urls import path
from . import views

urlpatterns = [
    # Static Pages
    path('', views.home, name='home'),                         # http://127.0.0.1:8000/
    path('about/', views.about, name='about'),                 # http://127.0.0.1:8000/about/
    path('blog/', views.blog, name='blog'),                    # http://127.0.0.1:8000/blog/
    path('contact/', views.contact, name='contact'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/', views.view_cart, name='view_cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('receipt/<int:order_id>/', views.receipt, name='order_receipt'),
    path('download-receipt/<int:order_id>/', views.download_receipt, name='download_receipt'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),

    # Notifications
    path('notifications/', views.notification_page, name='notifications'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),

    # Policies & Info
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms, name='terms'),
    path('refund-policy/', views.refund_policy, name='refund_policy'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('faq/', views.faq, name='faq'),

    # Services
    path('services/', views.services_view, name='services'),
    path('services/<slug:slug>/', views.service_detail, name='service_detail'),
]
