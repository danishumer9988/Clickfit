# store/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # Products
    path('products/', views.products, name='products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('get-cart-count/', views.get_cart_count, name='get_cart_count'),

    # Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('success/', views.success, name='success'),

    # Contact
    path('contact/', views.contact, name='contact'),
    path('contact/success/', views.contact_success, name='contact_success'),

    # Newsletter
    path('subscribe/', views.subscribe, name='subscribe'),
]
