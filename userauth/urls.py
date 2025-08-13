from django.urls import path
from userauth import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('verify_signup_otp/', views.verify_signup_otp, name='verify_signup_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('update_profile/', views.update_profile, name='update_profile'),
]
