import random
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, FuelOrder, ActivityLog, Payment, Vehicle, Notification


class Command(BaseCommand):
    help = 'Seeds extended data: ActivityLogs, Payments, Vehicles, Notifications'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding extended data...')

        # ── 1. Activity Logs ──────────────────────────────────────────────────
        ActivityLog.objects.all().delete()

        drivers  = list(User.objects.filter(user_type='driver'))
        customers= list(User.objects.filter(user_type='customer'))
        all_users= list(User.objects.all())

        log_templates = [
            ('login',  '{name} logged into the admin dashboard.'),
            ('logout', '{name} signed out of the admin dashboard.'),
            ('create', 'New fuel order #{oid} placed by {name}.'),
            ('update', 'Order #{oid} status updated to DELIVERED by {name}.'),
            ('delete', 'Cancelled order #{oid} removed from the system.'),
            ('create', 'New fuel station registered by {name}.'),
            ('update', 'User profile updated for {name}.'),
            ('login',  '{name} accessed the dashboard from a new device.'),
            ('update', 'Password changed for account {name}.'),
            ('create', 'Vehicle {plate} registered under {name}.'),
        ]

        orders = list(FuelOrder.objects.all()[:20])
        plates = ['UBA 998F', 'UED 456Y', 'UBF 772Z', 'UCC 100A', 'UAB 331G']
        ips    = ['127.0.0.1', '192.168.1.10', '10.0.0.5', '172.16.0.3', '192.168.0.25']

        for i in range(40):
            tpl   = random.choice(log_templates)
            action, desc_tpl = tpl
            user  = random.choice(all_users)
            order = random.choice(orders) if orders else None
            name  = user.full_name or user.phone_number
            oid   = order.id if order else 99
            plate = random.choice(plates)

            desc  = desc_tpl.format(name=name, oid=oid, plate=plate)
            ts    = timezone.now() - timedelta(hours=random.randint(1, 240))

            log = ActivityLog.objects.create(
                user=name,
                action=action,
                description=desc,
                ip_address=random.choice(ips),
            )
            # Backdate
            ActivityLog.objects.filter(pk=log.pk).update(created_at=ts)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {ActivityLog.objects.count()} activity logs created'))

        # ── 2. Payments ───────────────────────────────────────────────────────
        Payment.objects.all().delete()

        methods = ['Mobile Money', 'Mobile Money', 'Mobile Money', 'Bank Transfer', 'Card', 'Cash']
        statuses= ['PAID', 'PAID', 'PAID', 'PAID', 'PENDING', 'FAILED', 'REFUNDED']

        delivered_orders = list(FuelOrder.objects.filter(status='DELIVERED'))
        other_orders     = list(FuelOrder.objects.exclude(status='DELIVERED'))

        # Delivered orders → PAID
        for order in delivered_orders:
            Payment.objects.create(
                order=order,
                amount=order.total_price,
                payment_method=random.choice(methods),
                status='PAID',
                transaction_id=f'TXN-{uuid.uuid4().hex[:10].upper()}',
                payer_name=order.customer.full_name,
            )

        # Other orders → mixed statuses
        for order in other_orders[:10]:
            st = random.choice(['PENDING', 'FAILED'])
            Payment.objects.create(
                order=order,
                amount=order.total_price,
                payment_method=random.choice(methods),
                status=st,
                transaction_id=f'TXN-{uuid.uuid4().hex[:10].upper()}',
                payer_name=order.customer.full_name,
            )

        self.stdout.write(self.style.SUCCESS(f'  ✓ {Payment.objects.count()} payment records created'))

        # ── 3. Vehicles ───────────────────────────────────────────────────────
        Vehicle.objects.all().delete()

        vehicle_data = [
            ('Heavy Truck',            'UBA 998F',  'DL-998877', 'Isuzu FVZ 2021',        'ACTIVE'),
            ('Boda Boda (Motorcycle)', 'UED 456Y',  'DL-112233', 'Bajaj Boxer 2020',       'ACTIVE'),
            ('Fuel Tanker',            'UBF 772Z',  'DL-554433', 'Hino 500 Tanker 2019',   'ACTIVE'),
            ('Pickup Truck',           'UCC 100A',  'DL-667788', 'Toyota Hilux 2022',       'ACTIVE'),
            ('Saloon Car',             'UAB 331G',  'DL-223344', 'Toyota Corolla 2020',     'INACTIVE'),
            ('Van',                    'UBA 223H',  'DL-445566', 'Toyota HiAce 2018',       'ACTIVE'),
            ('Heavy Truck',            'UCA 551B',  'DL-778899', 'Mercedes Actros 2020',    'SUSPENDED'),
            ('Fuel Tanker',            'UBB 990C',  'DL-334455', 'Man TGS Tanker 2021',     'ACTIVE'),
        ]

        all_drivers = list(User.objects.filter(user_type='driver'))
        all_customers = list(User.objects.filter(user_type='customer'))
        all_owners = all_drivers + all_customers

        if not all_owners:
            all_owners = list(User.objects.all())

        for vtype, vnum, lic, make, st in vehicle_data:
            owner = random.choice(all_owners)
            ts    = timezone.now() - timedelta(days=random.randint(30, 365))
            v = Vehicle.objects.create(
                owner=owner,
                vehicle_type=vtype,
                vehicle_number=vnum,
                license_number=lic,
                make_model=make,
                status=st,
            )
            Vehicle.objects.filter(pk=v.pk).update(registered_at=ts)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {Vehicle.objects.count()} vehicles registered'))

        # ── 4. Notifications ──────────────────────────────────────────────────
        Notification.objects.all().delete()

        notif_data = [
            ('success', 'New Order Received',         'Order #FC-001 has been placed by John Doe for 45L of Petrol 95 at Shell Ntinda.', False),
            ('warning', 'Low Fuel Stock Alert',        'Shell Ntinda station reports Diesel stock below minimum threshold (< 500L).', False),
            ('info',    'System Maintenance Scheduled','Scheduled maintenance window: June 10, 2026 02:00–04:00 AM (EAT). Dashboard may be briefly unavailable.', False),
            ('success', 'Payment Confirmed',           'Payment TXN-A1B2C3D4E5 of UGX 216,000 received via Mobile Money for Order #FC-007.', False),
            ('danger',  'Failed Login Attempt',        'Multiple failed login attempts detected from IP 41.210.76.34. Consider reviewing access logs.', False),
            ('success', 'New Delivery Agent Onboarded','Moses Katende (0783234567) has completed registration and is now active as a delivery agent.', True),
            ('info',    'Weekly Report Ready',         'Your weekly performance report for May 26–Jun 1 is ready. View it in the analytics section.', True),
            ('warning', 'Order Cancellation',          'Order #FC-012 was cancelled by customer Alice Kansiime. Reason: Changed mind.', True),
            ('success', 'Station Opened',              'Stabex Jinja Road station has resumed operations and is now marked as OPEN.', True),
            ('info',    'New User Registration',       'Robert Mukasa (robert@example.com) has successfully registered as a customer on the platform.', True),
            ('danger',  'Payment Failed',              'Payment for Order #FC-019 failed (FAILED). Customer Jane Smith may need to retry.', False),
            ('warning', 'High Order Volume',           'Order volume today is 47% above average. Consider increasing delivery agent capacity.', False),
        ]

        for ntype, title, msg, is_read in notif_data:
            ts = timezone.now() - timedelta(hours=random.randint(1, 168))
            n  = Notification.objects.create(
                title=title, message=msg, type=ntype, is_read=is_read
            )
            Notification.objects.filter(pk=n.pk).update(created_at=ts)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {Notification.objects.count()} notifications created'))

        self.stdout.write(self.style.SUCCESS('\n✅ Extended seed data complete!'))
