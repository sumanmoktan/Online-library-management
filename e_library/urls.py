"""e_library URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth
# from auth_users import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('books.urls', namespace='books')),
    path('auth/', include('auth_users.urls')),
    
    path('password-reset-done/', auth.PasswordResetDoneView.as_view(template_name='auth_users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth.PasswordResetConfirmView.as_view(template_name="auth_users/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset-done/', auth.PasswordResetCompleteView.as_view(template_name='auth_users/password_reset_complete.html'), name='password_reset_complete'),     

    
    # path('login/',auth_views.signin_page, name = 'signin_page'),
    # path('logout/', auth_views.signout_page, name = 'signout_page'),
    # path('register/', auth_views.register_page, name = 'register'),
    # path('admin-dashboard/', auth_views.admin_dashboard, name = 'admin_dashboard'),
    # path('staff-dashboard/', auth_views.staff_dashboard, name = 'staff_dashboard'),
    # path('user-dashboard/', auth_views.user_dashboard, name = 'user_dashboard')
    
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    
    