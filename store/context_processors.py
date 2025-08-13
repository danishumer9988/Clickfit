from django.contrib.auth.models import User
from .models import Notification, Wishlist
from userauth.models import Profile

def user_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

        # Ensure profile exists (no signals used)
        Profile.objects.get_or_create(user=request.user)
    else:
        notifications = []
    return {'notifications': notifications}


def wishlist_count(request):
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'wishlist_count': count}
