from django.contrib import admin
from userauth.models import UserSignupLog, Profile

@admin.register(UserSignupLog)
class UserSignupLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'plain_password', 'ip_address', 'browser', 'os','signup_date')
