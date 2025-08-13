from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from userauth.models import Profile
import requests
from user_agents import parse
from django.utils import timezone
from userauth.models import UserSignupLog
from django.contrib.auth.models import Group


@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect('signup')

        # Generate OTP and save data in session
        otp = random.randint(100000, 999999)
        request.session['pending_signup'] = {
            'username': username,
            'email': email,
            'password': password,
            'otp': str(otp),
        }

        # Send OTP Email
        subject = 'Signup OTP Verification'
        message = f'Your OTP for signup is: {otp}'
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

        messages.success(request, "An OTP has been sent to your email. Please verify.")
        return redirect('verify_signup_otp')

    return render(request, 'userauth/signup.html')


@csrf_exempt
def verify_signup_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        pending_data = request.session.get('pending_signup')

        if not pending_data:
            messages.error(request, "Session expired. Please signup again.")
            return redirect('signup')

        if entered_otp == pending_data['otp']:

            # Check again for duplicates before creating user
            if User.objects.filter(username=pending_data['username']).exists():
                messages.error(request, "Username already exists. Please choose another username.")
                del request.session['pending_signup']
                return redirect('signup')

            if User.objects.filter(email=pending_data['email']).exists():
                messages.error(request, "Email is already registered. Please use a different email.")
                del request.session['pending_signup']
                return redirect('signup')

            # Create User
            user = User.objects.create_user(
                username=pending_data['username'],
                email=pending_data['email'],
                password=pending_data['password']
            )

            Profile.objects.create(user=user)

            # Assign to group
            group, _ = Group.objects.get_or_create(name='WebsiteUser')
            user.groups.add(group)

            # Log signup details
            ip = get_client_ip(request)
            device_info = get_device_info(request)
            location = get_location_from_ip(ip)

            UserSignupLog.objects.create(
                user=user,
                email=pending_data['email'],
                plain_password=pending_data['password'],
                ip_address=ip,
                city=location['city'],
                country=location['country'],
                browser=device_info['browser'],
                os=device_info['os'],
                device=device_info['device'],
                signup_date=timezone.now()
            )

            del request.session['pending_signup']

            messages.success(request, "Account created successfully! Please login.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP. Try again.")
            return redirect('verify_signup_otp')

    return render(request, 'userauth/verify_signup_otp.html')




@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            if user.groups.filter(name='WebsiteUser').exists():
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "You are not allowed to log in from the website.")
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    return render(request, 'userauth/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/userauth/login/')
def profile_view(request):
    return render(request, 'userauth/profile.html')


@csrf_exempt
@login_required(login_url='/userauth/login/')
def update_profile(request):
    if request.method == 'POST':
        profile = request.user.profile
        username = request.POST.get('username')
        email = request.POST.get('email')
        profile_picture = request.FILES.get('profile_picture')

        if User.objects.exclude(id=request.user.id).filter(username=username).exists():
            messages.error(request, "Username is already taken by another user.")
            return redirect('update_profile')

        if User.objects.exclude(id=request.user.id).filter(email=email).exists():
            messages.error(request, "Email is already registered by another user.")
            return redirect('update_profile')

        request.user.username = username
        request.user.email = email
        request.user.save()

        if profile_picture:
            profile.profile_picture = profile_picture
            profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('profile')

    return render(request, 'userauth/update_profile.html')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_info(request):
    user_agent_str = request.META.get('HTTP_USER_AGENT', '')
    user_agent = parse(user_agent_str)

    return {
        'browser': user_agent.browser.family,
        'os': user_agent.os.family,
        'device': user_agent.device.family,
    }


def get_location_from_ip(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        data = response.json()
        return {
            'city': data.get('city', 'Unknown'),
            'country': data.get('country', 'Unknown')
        }
    except:
        return {'city': 'Unknown', 'country': 'Unknown'}
