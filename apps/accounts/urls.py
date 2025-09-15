# ===== apps/accounts/urls.py =====
from django.urls import path
from . import views

# API URLs (for API endpoints)
api_urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='api_register'),
    path('login/', views.login_view, name='api_login'),
    path('logout/', views.logout_view, name='api_logout'),
    path('profile/', views.ProfileView.as_view(), name='api_profile'),
]

# Web URLs (for template views)
web_urlpatterns = [
    path('', views.home_page, name='home'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('logout/', views.logout_page, name='logout'),
    path('profile/', views.profile_page, name='profile'),
    # Email verification URLs
    path('verify-email/<str:email>/', views.verify_email, name='verify_email'),
    path('resend-verification/<str:email>/', views.resend_verification, name='resend_verification'),
    # Password reset URLs
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:email>/', views.reset_password, name='reset_password'),
    path('resend-reset-code/<str:email>/', views.resend_reset_code, name='resend_reset_code'),
]

urlpatterns = api_urlpatterns

