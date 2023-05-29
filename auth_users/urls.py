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
from django.urls import path
from .import views

app_name = 'auth_users'
urlpatterns = [
    path('login/', views.signin_page, name = 'signin_page'),
    path('logout/', views.signout_page, name = 'signout_page'),
    path('register/', views.register_page, name = 'register'),
    
    path('change-password/', views.change_password, name = "change_password"),
    path('password-reset/', views.password_reset_request, name ="password_reset"),
    
    path('dashboard/', views.dashboard, name = 'dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name = 'admin_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name = 'staff_dashboard'),
    path('user-dashboard/', views.user_dashboard, name = 'user_dashboard'),
    
    path('profile/', views.profile, name= 'profile'),
    path('edit-profile-image', views.edit_profile_image, name = "edit_profile_image"),
    path('edit-profile-detail', views.edit_profile_detail, name = "edit_profile_detail"),
    
    path('view-users/', views.view_user, name = 'view_user'),
    path('delete-user/<str:id>', views.delete_User, name = 'delete_user'),
    
]

