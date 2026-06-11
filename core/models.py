from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

class User(AbstractUser):
    # Disable username field, using phone_number as identifier
    username = None
    phone_number = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, blank=True, null=True)
    company_name = models.CharField(max_length=150, blank=True, null=True)
    fleet_size = models.IntegerField(default=0)
    is_email_verified = models.BooleanField(default=False)
    auth_provider = models.CharField(max_length=50, default='email')
    user_type = models.CharField(max_length=20, default='customer') # customer, driver, admin
    location = models.CharField(max_length=255, blank=True, null=True)
    
    # Driver specific fields
    vehicle_type = models.CharField(max_length=100, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"


class FuelStation(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=4.5)
    review_count = models.IntegerField(default=0)
    distance = models.CharField(max_length=50, default='1.0 km')
    image_url = models.CharField(max_length=255, default='assets/images/Shel.png')
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    is_open = models.BooleanField(default=True)
    price_per_litre = models.CharField(max_length=50, default='UGX 4,800')
    fuel_types = models.JSONField(default=list)  # e.g., ["Petrol 95", "Diesel"]
    phone = models.CharField(max_length=50, default='+256 414 123456')
    opening_hours = models.CharField(max_length=100, default='24 Hours')

    def __str__(self):
        return self.name


class FuelOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ONGOING', 'Ongoing'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    # Use database cascade or set null, cascade makes sense for test project
    # We can use ForeignKey with on_delete=models.CASCADE
    station = models.ForeignKey(FuelStation, on_delete=models.CASCADE, related_name='orders')
    fuel_type = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)  # Liters
    quantity_unit = models.CharField(max_length=20, default='Liters')
    total_price = models.DecimalField(max_digits=12, decimal_places=2)  # Price
    currency = models.CharField(max_length=10, default='UGX')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.fuel_type} ({self.status})"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Mobile Money', 'Mobile Money'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Card', 'Card'),
        ('Cash', 'Cash'),
    ]
    STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    order = models.OneToOneField(FuelOrder, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='Mobile Money')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PAID')
    transaction_id = models.CharField(max_length=100, unique=True)
    payer_name = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.transaction_id} — {self.status}"


class Vehicle(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]
    TYPE_CHOICES = [
        ('Heavy Truck', 'Heavy Truck'),
        ('Fuel Tanker', 'Fuel Tanker'),
        ('Boda Boda (Motorcycle)', 'Boda Boda (Motorcycle)'),
        ('Pickup Truck', 'Pickup Truck'),
        ('Saloon Car', 'Saloon Car'),
        ('Van', 'Van'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registered_vehicles')
    vehicle_type = models.CharField(max_length=100, choices=TYPE_CHOICES, default='Saloon Car')
    vehicle_number = models.CharField(max_length=50, unique=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    make_model = models.CharField(max_length=150, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle_number} ({self.vehicle_type})"


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('other', 'Other'),
    ]

    user = models.CharField(max_length=200)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, default='other')
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.action.upper()}] {self.user} — {self.description[:60]}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type.upper()}] {self.title}"
