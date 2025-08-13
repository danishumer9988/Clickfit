from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default.png')
    phone = models.CharField(max_length=15, blank=True)
    otp = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return self.user.username


class UserSignupLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    plain_password = models.CharField(max_length=128)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    city = models.CharField(max_length=100, default="Unknown", blank=True)
    country = models.CharField(max_length=100, default="Unknown", blank=True)
    browser = models.CharField(max_length=100, default="Unknown", blank=True)
    os = models.CharField(max_length=100, default="Unknown", blank=True)
    device = models.CharField(max_length=100, default="Unknown", blank=True)
    signup_date = models.DateTimeField()


    def __str__(self):
        return f"Signup Log: {self.user.username}"


