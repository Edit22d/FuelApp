from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, LoginView, MeView, ProfileUpdateView, 
    ForgotPasswordView, ResetPasswordView, LogoutView, AppInfoView,
    FuelStationListView, FuelStationDetailView,
    FuelOrderListCreateView, FuelOrderCancelView
)

urlpatterns = [
    # Authentication & Profile endpoints
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', LoginView.as_view(), name='auth_login'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('auth/me/', MeView.as_view(), name='auth_me'),
    path('auth/profile/update/', ProfileUpdateView.as_view(), name='auth_profile_update_1'),
    path('auth/update-profile/', ProfileUpdateView.as_view(), name='auth_profile_update_2'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='auth_forgot_password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='auth_reset_password'),
    path('auth/app-info/', AppInfoView.as_view(), name='auth_app_info_1'),
    path('auth/info/', AppInfoView.as_view(), name='auth_app_info_2'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Fuel Stations endpoints
    path('stations/', FuelStationListView.as_view(), name='stations_list'),
    path('stations/<int:pk>/', FuelStationDetailView.as_view(), name='station_detail'),
    
    # Fuel Orders endpoints
    path('orders/', FuelOrderListCreateView.as_view(), name='orders_list_create'),
    path('orders/<int:pk>/cancel/', FuelOrderCancelView.as_view(), name='order_cancel'),
]
