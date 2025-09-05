from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
import logging

from .models import Product, Order, Contact, Subscriber
from .forms import ContactForm, OrderForm, SubscriberForm

# Set up logger
logger = logging.getLogger(__name__)

def index(request):
    products = Product.objects.filter(is_active=True)[:4]  # Show 4 active products on homepage
    return render(request, 'store/index.html', {'products': products})

def products(request):
    category = request.GET.get('category', '')
    products = Product.objects.filter(is_active=True)

    if category:
        products = products.filter(category=category)

    return render(request, 'store/products.html', {
        'products': products,
        'category': category
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    return render(request, 'store/product_detail.html', {'product': product})

def cart(request):
    cart_items = request.session.get('cart', [])
    total = 0

    # Validate cart items against current stock and prices
    validated_cart = []
    for item in cart_items:
        try:
            product = Product.objects.get(id=item['id'], is_active=True)

            # Check if product is still available
            if product.stock is not None and item['quantity'] > product.stock:
                item['quantity'] = product.stock
                messages.warning(request, f"Quantity adjusted for {product.name} due to limited stock")

            # Update with current price
            item['price'] = str(product.price)
            item['current_stock'] = product.stock
            validated_cart.append(item)

            total += float(item['price']) * item['quantity']
        except Product.DoesNotExist:
            # Remove items for products that no longer exist
            messages.warning(request, f"{item['name']} is no longer available and was removed from your cart")
            continue

    # Update session with validated cart
    request.session['cart'] = validated_cart
    request.session['cart_count'] = sum(item['quantity'] for item in validated_cart)
    request.session.modified = True

    return render(request, 'store/cart.html', {
        'cart_items': validated_cart,
        'total': total
    })

def checkout(request):
    cart_items = request.session.get('cart', [])

    if not cart_items:
        messages.error(request, "Your cart is empty. Please add some products before checkout.")
        return redirect('cart')

    # Revalidate cart before checkout
    validated_cart = []
    total = 0
    for item in cart_items:
        try:
            product = Product.objects.get(id=item['id'], is_active=True)

            # Check stock
            if product.stock is not None and item['quantity'] > product.stock:
                messages.error(request, f"Only {product.stock} items available for {product.name}")
                return redirect('cart')

            # Update with current price
            item['price'] = str(product.price)
            validated_cart.append(item)
            total += float(item['price']) * item['quantity']
        except Product.DoesNotExist:
            messages.error(request, f"{item['name']} is no longer available")
            return redirect('cart')

    # Update session with validated cart
    request.session['cart'] = validated_cart
    request.session.modified = True

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            # Get cart items from session
            order.items = json.dumps(validated_cart)

            # Calculate total
            order.total = total

            # Set initial status
            order.status = 'pending'

            order.save()

            # Update product stock
            for item in validated_cart:
                product = Product.objects.get(id=item['id'])
                if product.stock is not None:
                    product.stock -= item['quantity']
                    product.save()

            # Send email notification to admin
            subject = f'New Order #{order.id}'
            message = f'''
            New order received:
            
            Order ID: {order.id}
            Customer: {order.name}
            Email: {order.email}
            Phone: {order.phone}
            Address: {order.address}
            Payment Method: {order.payment_method}
            Total: ${order.total:.2f}
            
            Items:
            '''
            for item in validated_cart:
                message += f"{item['name']} - ${float(item['price']):.2f} x {item['quantity']}\n"

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.EMAIL_HOST_USER],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Email sending failed: {e}")

            # Send confirmation email to customer
            try:
                customer_subject = f'Order Confirmation #{order.id}'
                customer_message = f'''
                Thank you for your order!
                
                Order ID: {order.id}
                Total: ${order.total:.2f}
                
                We'll process your order shortly and notify you when it ships.
                
                Items ordered:
                '''
                for item in validated_cart:
                    customer_message += f"{item['name']} - ${float(item['price']):.2f} x {item['quantity']}\n"

                customer_message += f'''
                
                Shipping Address:
                {order.address}
                '''

                send_mail(
                    customer_subject,
                    customer_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [order.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Customer confirmation email failed: {e}")

            # Clear cart
            request.session['cart'] = []
            request.session['cart_count'] = 0
            request.session.modified = True

            # Store order ID in session for success page
            request.session['last_order_id'] = order.id

            return redirect('success')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = OrderForm()

    return render(request, 'store/checkout.html', {
        'form': form,
        'cart_items': validated_cart,
        'total': total
    })

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()

            # Send email notification
            subject = f'New Contact Message from {contact.name}'
            message = f"""
New contact message:

Name: {contact.name}
Email: {contact.email}
Message: {contact.message}
"""

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.EMAIL_HOST_USER],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Contact email sending failed: {e}")

            messages.success(request, "✅ Your message has been sent successfully!")
            return redirect('contact_success')
        else:
            messages.error(request, "❌ Please correct the errors in the form.")
    else:
        form = ContactForm()

    return render(request, 'store/contact.html', {'form': form})

def contact_success(request):
    return render(request, 'store/contact_success.html')

@csrf_exempt
@require_POST
def subscribe(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')

        if email:
            # Check if subscriber already exists
            subscriber, created = Subscriber.objects.get_or_create(
                email=email,
                defaults={'email': email}
            )

            if created:
                # Send email notification for new subscriber
                subject = 'New Newsletter Subscriber'
                message = f'''
                New newsletter subscriber:
                
                Email: {subscriber.email}
                '''

                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [settings.EMAIL_HOST_USER],
                        fail_silently=False,
                    )
                except Exception as e:
                    logger.error(f"Subscription email sending failed: {e}")

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Email is required'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

def success(request):
    order_id = request.session.get('last_order_id', None)
    context = {}

    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            context['order'] = order
        except Order.DoesNotExist:
            messages.warning(request, "Order details not found")
            pass

    return render(request, 'store/success.html', context)

@csrf_exempt
@require_POST
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        if not product_id:
            return JsonResponse({'success': False, 'error': 'Product ID is required'})

        product = get_object_or_404(Product, id=product_id, is_active=True)

        # Check stock availability
        if product.stock is not None and quantity > product.stock:
            return JsonResponse({
                'success': False,
                'error': f'Only {product.stock} items available in stock'
            })

        # Initialize cart if it doesn't exist
        if 'cart' not in request.session:
            request.session['cart'] = []

        cart = request.session['cart']

        # Check if product already in cart
        item_found = False
        for item in cart:
            if str(item['id']) == str(product_id):
                # Check if adding quantity would exceed stock
                new_quantity = item['quantity'] + quantity
                if product.stock is not None and new_quantity > product.stock:
                    return JsonResponse({
                        'success': False,
                        'error': f'Only {product.stock} items available in stock'
                    })

                item['quantity'] = new_quantity
                item_found = True
                break

        if not item_found:
            cart.append({
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'image': product.image.url if product.image else '',
                'quantity': quantity
            })

        request.session['cart'] = cart
        request.session['cart_count'] = sum(int(item['quantity']) for item in cart)
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'cart_count': request.session['cart_count'],
            'message': f'{product.name} added to cart'
        })

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def update_cart(request):
    try:
        data = json.loads(request.body)
        cart_data = data.get('cart', [])

        # Validate cart data
        validated_cart = []
        for item in cart_data:
            if 'id' in item and 'quantity' in item:
                quantity = int(item['quantity'])

                # Skip items with zero quantity
                if quantity <= 0:
                    continue

                # Check stock availability
                product = get_object_or_404(Product, id=item['id'], is_active=True)

                if product.stock is not None and quantity > product.stock:
                    return JsonResponse({
                        'success': False,
                        'error': f'Only {product.stock} items available for {product.name}'
                    })

                validated_cart.append({
                    'id': item['id'],
                    'name': product.name,
                    'price': str(product.price),
                    'image': product.image.url if product.image else '',
                    'quantity': quantity
                })

        request.session['cart'] = validated_cart
        request.session['cart_count'] = sum(item['quantity'] for item in validated_cart)
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'cart_count': request.session['cart_count'],
            'message': 'Cart updated successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f"Update cart error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def remove_from_cart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')

        if not product_id:
            return JsonResponse({'success': False, 'error': 'Product ID is required'})

        cart = request.session.get('cart', [])

        # Filter out the item to remove
        updated_cart = [item for item in cart if str(item['id']) != str(product_id)]

        request.session['cart'] = updated_cart
        request.session['cart_count'] = sum(item['quantity'] for item in updated_cart)
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'cart_count': request.session['cart_count'],
            'message': 'Item removed from cart'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f"Remove from cart error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

def get_cart_count(request):
    cart_count = request.session.get('cart_count', 0)
    return JsonResponse({'cart_count': cart_count})
