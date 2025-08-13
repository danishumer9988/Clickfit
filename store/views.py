from django.views.decorators.http import require_POST
from .models import Product, Cart, CartItem, Order, OrderItem, NewsletterSubscriber, ContactMessage, Notification, Wishlist, Service, Transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.template.loader import get_template, render_to_string
from xhtml2pdf import pisa
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .forms import CheckoutForm
import random
from django.core.cache import cache
from userauth.models import Profile


def ensure_profile(user):
    Profile.objects.get_or_create(user=user)


def home(request):
    return render(request, 'store/home.html')


def about(request):
    return render(request, 'store/about.html')


def blog(request):
    return render(request, 'store/blog.html')


def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            if NewsletterSubscriber.objects.filter(email=email).exists():
                messages.warning(request, 'This email is already subscribed.')
            else:
                NewsletterSubscriber.objects.create(email=email)

                if request.user.is_authenticated:
                    ensure_profile(request.user)
                    Notification.objects.create(
                        user=request.user,
                        message="Thank you for subscribing to the newsletter."
                    )

                messages.success(request, 'Thank you for subscribing!')
        else:
            messages.error(request, 'Please provide a valid email.')
        return redirect(request.META.get('HTTP_REFERER', 'home'))


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if name and email and message:
            ContactMessage.objects.create(name=name, email=email, message=message)

            if request.user.is_authenticated:
                ensure_profile(request.user)
                Notification.objects.create(
                    user=request.user,
                    message="Your contact message has been submitted successfully."
                )

            messages.success(request, 'Your message has been sent successfully!')
        else:
            messages.error(request, 'Please fill out all fields.')

    return render(request, 'store/contact.html')


def product_list(request):
    category = request.GET.get('category')
    if category:
        products = Product.objects.filter(category=category).order_by('-created_at')
    else:
        products = Product.objects.all().order_by('-created_at')

    return render(request, 'store/product_list.html', {'products': products})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})


@login_required(login_url='/userauth/login/')
def view_cart(request):
    ensure_profile(request.user)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    cart_total = sum(item.subtotal() for item in cart_items)

    return render(request, 'store/view_cart.html', {
        'cart_items': cart_items,
        'cart_total': cart_total
    })


@login_required(login_url='/userauth/login/')
def add_to_cart(request, product_id):
    ensure_profile(request.user)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity

    cart_item.save()

    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


@login_required(login_url='/userauth/login/')
def update_cart(request):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)

        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                product_id = key.split('_')[1]
                try:
                    quantity = int(value)
                    cart_item = CartItem.objects.get(cart=cart, product_id=product_id)

                    if quantity > 0:
                        cart_item.quantity = quantity
                        cart_item.save()
                    else:
                        cart_item.delete()

                except (ValueError, CartItem.DoesNotExist):
                    continue

    return redirect('view_cart')


@login_required(login_url='/userauth/login/')
def remove_from_cart(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()
    return redirect('view_cart')


@login_required(login_url='/userauth/login/')
def receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/receipt.html', {'order': order})


@login_required(login_url='/userauth/login/')
def download_receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    template = get_template('store/receipt_pdf.html')
    html = template.render({'order': order})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{order.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    return response


@login_required(login_url='/userauth/login/')
@transaction.atomic
def checkout(request):
    ensure_profile(request.user)
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items.exists():
        return redirect('view_cart')

    cart_total = sum(item.subtotal() for item in cart_items)
    jazzcash_account_number = "03193421756"

    if request.method == 'POST':
        form = CheckoutForm(request.POST)

        if form.is_valid():
            cd = form.cleaned_data
            payment_method = cd.get('payment_method', 'COD')

            otp = random.randint(100000, 999999)

            request.session['order_data'] = {
                'name': cd['name'], 'email': cd['email'], 'phone': cd['phone'],
                'address': cd['address'], 'city': cd['city'], 'province': cd['province'],
                'postal_code': cd['postal_code'], 'cart_total': str(cart_total),
                'payment_method': payment_method
            }

            request.session['otp'] = str(otp)

            subject = 'Your Order OTP Verification'
            message = f"Hello {cd['name']},\n\nYour OTP is: {otp}\n\nThank you for shopping with us!"
            send_mail(subject, message, settings.EMAIL_HOST_USER, [cd['email']])

            return redirect('verify_otp')
    else:
        form = CheckoutForm()

    return render(request, 'store/checkout.html', {
        'form': form, 'cart_items': cart_items, 'cart_total': cart_total,
        'jazzcash_account_number': jazzcash_account_number
    })


@login_required(login_url='/userauth/login/')
@transaction.atomic
def verify_otp(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    order_data = request.session.get('order_data', {})
    cart_total = order_data.get('cart_total')

    if not cart_items.exists() or not order_data:
        return redirect('view_cart')

    # ✅ Collect product IDs
    product_ids = [item.product.id for item in cart_items]

    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        session_otp = request.session.get('otp')

        if user_otp == session_otp:
            payment_method = order_data.get('payment_method', 'COD')
            transaction_id = order_data.get('transaction_id', None)
            status = 'Pending Verification' if payment_method == 'JAZZCASH' else 'Pending'

            order = Order.objects.create(
                user=request.user, total_price=cart_total,
                name=order_data['name'], phone=order_data['phone'], email=order_data['email'],
                address=order_data['address'], city=order_data['city'], province=order_data['province'],
                postal_code=order_data['postal_code'], payment_method=payment_method,
                transaction_id=transaction_id, status=status
            )

            for item in cart_items:
                OrderItem.objects.create(order=order, product=item.product, product_id=item.product.id,  quantity=item.quantity, price=item.product.price)

            cart_items.delete()
            del request.session['otp']
            del request.session['order_data']

            subject = f'New Order - #{order.id}'
            message = render_to_string('store/email_receipt.html', {'order': order})
            email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [settings.SHOP_OWNER_EMAIL])
            email.content_subtype = 'html'
            email.send(fail_silently=True)

            return render(request, 'store/receipt.html', {'order': order})
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'store/verify_otp.html', {
        'cart_items': cart_items, 'cart_total': cart_total
    })


@login_required(login_url='/userauth/login/')
def notification_page(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/notifications.html', {'notifications': notifications})


@require_POST
@login_required(login_url='/userauth/login/')
def mark_all_read(request):
    request.user.notification_set.all().delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required(login_url='/userauth/login/')
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})


@login_required(login_url='/userauth/login/')
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.user != request.user:
        messages.error(request, "Unauthorized action.")
        return redirect('profile')

    if order.status != 'Cancelled':
        order.status = 'Cancelled'
        order.save()
        messages.success(request, 'Order cancelled successfully!')
    else:
        messages.info(request, 'Order is already cancelled.')

    return redirect('profile')


@login_required(login_url='/userauth/login/')
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'store/wishlist.html', {'wishlist_items': wishlist_items})


@login_required(login_url='/userauth/login/')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('product_list')


@login_required
def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
    return redirect('wishlist')


def privacy_policy(request):
    return render(request, 'store/privacy_policy.html')


def terms(request):
    return render(request, 'store/terms_and_conditions.html')


def refund_policy(request):
    return render(request, 'store/refund_policy.html')


def shipping_policy(request):
    return render(request, 'store/shipping_policy.html')


def faq(request):
    return render(request, 'store/FAQ.html')


def services_view(request):
    services = Service.objects.all()
    return render(request, 'store/services.html', {'services': services})


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug)
    return render(request, 'store/service_detail.html', {'service': service})
