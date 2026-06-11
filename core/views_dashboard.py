from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.shortcuts import render, redirect
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from core.models import User, FuelStation, FuelOrder, ActivityLog, Payment, Vehicle, Notification


# ─────────────────────────────────────────────
# GLOBAL CONTEXT MIXIN — injects notification count + admin info into every view
# ─────────────────────────────────────────────
class DashboardContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_notifications_count'] = Notification.objects.filter(is_read=False).count()
        if self.request.user.is_authenticated:
            context['admin_name'] = self.request.user.full_name or self.request.user.phone_number
            context['admin_initial'] = (self.request.user.full_name or 'A')[0].upper()
        return context


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

class DashboardLoginView(View):
    template_name = 'dashboard/login.html'

    def get(self, request):
        if request.user.is_authenticated and (request.user.is_staff or request.user.user_type == 'admin'):
            return redirect('dashboard_home')
        return render(request, self.template_name)

    def post(self, request):
        phone_number = request.POST.get('phone_number', '').strip()
        password     = request.POST.get('password', '').strip()

        if not phone_number or not password:
            return render(request, self.template_name, {
                'error': 'Please enter both phone number and password.',
                'phone_number': phone_number
            })

        user = authenticate(request, username=phone_number, password=password)

        if user is not None:
            if not user.is_active:
                return render(request, self.template_name, {
                    'error': 'This account is inactive.',
                    'phone_number': phone_number
                })
            if not (user.is_staff or user.user_type in ['admin', 'staff']):
                return render(request, self.template_name, {
                    'error': 'Access denied. Only administrators can access the dashboard.',
                    'phone_number': phone_number
                })

            login(request, user)
            ActivityLog.objects.create(
                user=user.full_name or user.phone_number,
                action='login',
                description=f'{user.full_name} logged into the admin dashboard.',
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'dashboard_home')
        else:
            return render(request, self.template_name, {
                'error': 'Invalid credentials. Please verify your phone number and password.',
                'phone_number': phone_number
            })


class DashboardLogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            ActivityLog.objects.create(
                user=request.user.full_name or request.user.phone_number,
                action='logout',
                description=f'{request.user.full_name} logged out from the admin dashboard.',
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
        logout(request)
        return redirect('dashboard_login')


# ─────────────────────────────────────────────
# OVERVIEW
# ─────────────────────────────────────────────

class DashboardHomeView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_users']     = User.objects.count()
        context['total_orders']    = FuelOrder.objects.count()
        context['active_stations'] = FuelStation.objects.filter(is_open=True).count()
        revenue_data = FuelOrder.objects.filter(status__in=['DELIVERED', 'ONGOING']).aggregate(Sum('total_price'))
        context['total_revenue']   = revenue_data['total_price__sum'] or 0.0
        context['recent_orders']   = FuelOrder.objects.all().order_by('-created_at')[:8]

        today = timezone.now().date()
        date_labels, orders_counts, revenue_trends = [], [], []
        for i in range(6, -1, -1):
            target_date = today - timedelta(days=i)
            date_labels.append(target_date.strftime('%b %d'))
            day_orders = FuelOrder.objects.filter(created_at__date=target_date)
            orders_counts.append(day_orders.count())
            day_revenue = day_orders.filter(status__in=['DELIVERED', 'ONGOING']).aggregate(Sum('total_price'))['total_price__sum'] or 0.0
            revenue_trends.append(float(day_revenue) / 1000.0)

        context['line_labels']      = date_labels
        context['line_data_orders'] = orders_counts
        context['line_data_revenue']= revenue_trends

        fuel_stats = FuelOrder.objects.values('fuel_type').annotate(total_qty=Sum('quantity')).order_by('-total_qty')
        context['bar_labels'] = [s['fuel_type'] for s in fuel_stats]
        context['bar_data']   = [float(s['total_qty']) for s in fuel_stats]

        status_stats = FuelOrder.objects.values('status').annotate(count=Count('id'))
        context['pie_labels'] = [s['status'] for s in status_stats]
        context['pie_data']   = [s['count'] for s in status_stats]

        context['active_page'] = 'dashboard'
        return context


# ─────────────────────────────────────────────
# OPERATIONAL
# ─────────────────────────────────────────────

class DashboardOrdersView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders']      = FuelOrder.objects.all().order_by('-created_at')
        context['active_page'] = 'orders'
        return context


class DashboardStationsView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/stations.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stations']    = FuelStation.objects.all().order_by('id')
        context['active_page'] = 'stations'
        return context


class DashboardPaymentsView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/payments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payments']      = Payment.objects.all().select_related('order', 'order__customer').order_by('-created_at')
        context['total_paid']    = Payment.objects.filter(status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_pending'] = Payment.objects.filter(status='PENDING').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_failed']  = Payment.objects.filter(status='FAILED').aggregate(Sum('amount'))['amount__sum'] or 0
        context['active_page']   = 'payments'
        return context


class DashboardVehiclesView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/vehicles.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicles']    = Vehicle.objects.all().select_related('owner').order_by('-registered_at')
        context['active_page'] = 'vehicles'
        return context


# ─────────────────────────────────────────────
# COMMUNITY
# ─────────────────────────────────────────────

class DashboardDeliveryAgentsView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/delivery_agents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agents']      = User.objects.filter(user_type='driver').order_by('-date_joined')
        context['active_page'] = 'delivery_agents'
        return context


class DashboardContactMessagesView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/contact_messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages']    = []
        context['active_page'] = 'contact_messages'
        return context


# ─────────────────────────────────────────────
# ADMINISTRATION
# ─────────────────────────────────────────────

class DashboardUsersView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/users.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users']       = User.objects.all().order_by('-date_joined')
        context['active_page'] = 'users'
        return context


class DashboardActivityLogsView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/activity_logs.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs']        = ActivityLog.objects.all().order_by('-created_at')
        context['active_page'] = 'activity_logs'
        return context


# ─────────────────────────────────────────────
# MY ACCOUNT
# ─────────────────────────────────────────────

class DashboardProfileView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'profile'
        return context


class DashboardSecurityView(DashboardContextMixin, LoginRequiredMixin, View):
    template_name = 'dashboard/security.html'

    def _base_context(self, request):
        return {
            'active_page': 'security',
            'login_logs': ActivityLog.objects.filter(
                user=request.user.full_name or request.user.phone_number,
                action__in=['login', 'logout']
            ).order_by('-created_at')[:10],
            'unread_notifications_count': Notification.objects.filter(is_read=False).count(),
            'admin_name': request.user.full_name or request.user.phone_number,
            'admin_initial': (request.user.full_name or 'A')[0].upper(),
        }

    def get(self, request):
        return render(request, self.template_name, self._base_context(request))

    def post(self, request):
        current_password  = request.POST.get('current_password', '')
        new_password      = request.POST.get('new_password', '')
        confirm_password  = request.POST.get('confirm_password', '')
        context = self._base_context(request)

        if not current_password or not new_password or not confirm_password:
            context['error'] = 'All three fields are required.'
            return render(request, self.template_name, context)

        if not request.user.check_password(current_password):
            context['error'] = 'Current password is incorrect.'
            return render(request, self.template_name, context)

        if new_password != confirm_password:
            context['error'] = 'New passwords do not match.'
            return render(request, self.template_name, context)

        if len(new_password) < 8:
            context['error'] = 'New password must be at least 8 characters long.'
            return render(request, self.template_name, context)

        import re
        if not re.search(r'[A-Z]', new_password):
            context['error'] = 'Password must include at least one uppercase letter.'
            return render(request, self.template_name, context)

        if not re.search(r'[0-9]', new_password):
            context['error'] = 'Password must include at least one number.'
            return render(request, self.template_name, context)

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)   # Keep user logged in after change

        ActivityLog.objects.create(
            user=request.user.full_name or request.user.phone_number,
            action='update',
            description=f'Password changed for account {request.user.full_name}.',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )

        context['success'] = 'Password updated successfully! You remain logged in.'
        context['login_logs'] = ActivityLog.objects.filter(
            user=request.user.full_name or request.user.phone_number,
            action__in=['login', 'logout']
        ).order_by('-created_at')[:10]
        return render(request, self.template_name, context)


class DashboardChangeEmailView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/change_email.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'change_email'
        return context


class DashboardNotificationsView(DashboardContextMixin, LoginRequiredMixin, View):
    template_name = 'dashboard/notifications.html'

    def get(self, request):
        notifications = Notification.objects.all().order_by('-created_at')
        context = {
            'notifications': notifications,
            'unread_count': notifications.filter(is_read=False).count(),
            'active_page': 'notifications',
            'unread_notifications_count': notifications.filter(is_read=False).count(),
            'admin_name': request.user.full_name or request.user.phone_number,
            'admin_initial': (request.user.full_name or 'A')[0].upper(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        action   = request.POST.get('action')
        notif_id = request.POST.get('notif_id')
        if action == 'mark_read' and notif_id:
            Notification.objects.filter(id=notif_id).update(is_read=True)
        elif action == 'mark_all_read':
            Notification.objects.filter(is_read=False).update(is_read=True)
        elif action == 'delete' and notif_id:
            Notification.objects.filter(id=notif_id).delete()
        elif action == 'delete_all_read':
            Notification.objects.filter(is_read=True).delete()
        return redirect('dashboard_notifications')


class DashboardSettingsView(DashboardContextMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'settings'
        return context
