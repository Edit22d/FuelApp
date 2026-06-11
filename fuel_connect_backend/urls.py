from django.contrib import admin
from django.urls import path, include
from core.views_dashboard import (
    # Auth
    DashboardLoginView, DashboardLogoutView,
    # Overview
    DashboardHomeView,
    # Operational
    DashboardOrdersView, DashboardStationsView,
    DashboardPaymentsView, DashboardVehiclesView,
    # Community
    DashboardDeliveryAgentsView, DashboardContactMessagesView,
    # Administration
    DashboardUsersView, DashboardActivityLogsView,
    # My Account
    DashboardProfileView, DashboardSecurityView, DashboardChangeEmailView,
    DashboardNotificationsView, DashboardSettingsView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/v1/', include('core.urls')),

    # ── Auth ──
    path('dashboard/login/',  DashboardLoginView.as_view(),  name='dashboard_login'),
    path('dashboard/logout/', DashboardLogoutView.as_view(), name='dashboard_logout'),

    # ── Overview ──
    path('dashboard/', DashboardHomeView.as_view(), name='dashboard_home'),

    # ── Operational ──
    path('dashboard/orders/',   DashboardOrdersView.as_view(),   name='dashboard_orders'),
    path('dashboard/stations/', DashboardStationsView.as_view(), name='dashboard_stations'),
    path('dashboard/payments/', DashboardPaymentsView.as_view(), name='dashboard_payments'),
    path('dashboard/vehicles/', DashboardVehiclesView.as_view(), name='dashboard_vehicles'),

    # ── Community ──
    path('dashboard/delivery-agents/',  DashboardDeliveryAgentsView.as_view(),  name='dashboard_delivery_agents'),
    path('dashboard/contact-messages/', DashboardContactMessagesView.as_view(), name='dashboard_contact_messages'),

    # ── Administration ──
    path('dashboard/users/',         DashboardUsersView.as_view(),        name='dashboard_users'),
    path('dashboard/activity-logs/', DashboardActivityLogsView.as_view(), name='dashboard_activity_logs'),

    # ── My Account ──
    path('dashboard/profile/',       DashboardProfileView.as_view(),      name='dashboard_profile'),
    path('dashboard/security/',      DashboardSecurityView.as_view(),     name='dashboard_security'),
    path('dashboard/change-email/',  DashboardChangeEmailView.as_view(),  name='dashboard_change_email'),
    path('dashboard/notifications/', DashboardNotificationsView.as_view(),name='dashboard_notifications'),
    path('dashboard/settings/',      DashboardSettingsView.as_view(),     name='dashboard_settings'),
]
