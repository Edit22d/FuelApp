import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User, FuelStation, FuelOrder

class Command(BaseCommand):
    help = 'Seeds mock data for Fuel Connect backend (users, stations, orders)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # 1. Clean up existing data
        FuelOrder.objects.all().delete()
        FuelStation.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        # 2. Create Users (Customers)
        customers = []
        customer_data = [
            ("0771234567", "John Doe", "john@example.com", "Kampala, Central"),
            ("0772234567", "Jane Smith", "jane@example.com", "Ntinda, Kampala"),
            ("0773234567", "Robert Mukasa", "robert@example.com", "Jinja, Eastern"),
            ("0774234567", "Alice Kansiime", "alice@example.com", "Entebbe, Wakiso"),
        ]
        for phone, name, email, loc in customer_data:
            user = User.objects.create_user(
                phone_number=phone,
                full_name=name,
                email=email,
                user_type="customer",
                location=loc,
                fleet_size=random.randint(0, 15),
                company_name=f"{name.split()[1]} Logistics" if random.choice([True, False]) else None
            )
            user.set_password("password123")
            user.save()
            customers.append(user)

        # Create Users (Drivers)
        drivers = []
        driver_data = [
            ("0781234567", "David Okello", "david@example.com", "Heavy Truck", "UBA 998F", "DL-998877"),
            ("0782234567", "Sarah Namubiru", "sarah@example.com", "Boda Boda (Motorcycle)", "UED 456Y", "DL-112233"),
            ("0783234567", "Moses Katende", "moses@example.com", "Fuel Tanker", "UBF 772Z", "DL-554433"),
        ]
        for phone, name, email, v_type, v_num, l_num in driver_data:
            user = User.objects.create_user(
                phone_number=phone,
                full_name=name,
                email=email,
                user_type="driver",
                location="Kampala, Central",
                vehicle_type=v_type,
                vehicle_number=v_num,
                license_number=l_num
            )
            user.set_password("password123")
            user.save()
            drivers.append(user)

        # 3. Create Fuel Stations (matching kStations in mobile app)
        stations = []
        station_data = [
            {
                "name": "Shell Ntinda",
                "address": "Ntinda Road, Kampala",
                "rating": 4.6,
                "review_count": 342,
                "distance": "0.3 km",
                "image_url": "assets/images/Shel.png",
                "latitude": 0.3476,
                "longitude": 32.5825,
                "is_open": True,
                "price_per_litre": "UGX 4,850",
                "fuel_types": ["Petrol 95", "Petrol 98", "Diesel"],
                "phone": "+256 414 123456",
                "opening_hours": "24 Hours"
            },
            {
                "name": "TotalEnergies",
                "address": "Kampala Road, Kampala",
                "rating": 4.5,
                "review_count": 289,
                "distance": "0.7 km",
                "image_url": "assets/images/Totall.png",
                "latitude": 0.3460,
                "longitude": 32.5840,
                "is_open": True,
                "price_per_litre": "UGX 4,800",
                "fuel_types": ["Petrol 95", "Diesel", "Kerosene"],
                "phone": "+256 414 234567",
                "opening_hours": "6:00 AM - 10:00 PM"
            },
            {
                "name": "Stabex",
                "address": "Jinja Road, Kampala",
                "rating": 4.3,
                "review_count": 156,
                "distance": "1.1 km",
                "image_url": "assets/images/Stabe.png",
                "latitude": 0.3490,
                "longitude": 32.5810,
                "is_open": False,
                "price_per_litre": "UGX 4,780",
                "fuel_types": ["Petrol 95", "Diesel", "LPG"],
                "phone": "+256 414 345678",
                "opening_hours": "7:00 AM - 9:00 PM"
            },
            {
                "name": "Rubis",
                "address": "Bombo Road, Kampala",
                "rating": 4.4,
                "review_count": 198,
                "distance": "1.5 km",
                "image_url": "assets/images/Rubi.png",
                "latitude": 0.3510,
                "longitude": 32.5800,
                "is_open": True,
                "price_per_litre": "UGX 4,820",
                "fuel_types": ["Petrol 95", "Petrol 98", "Diesel", "Kerosene"],
                "phone": "+256 414 456789",
                "opening_hours": "24 Hours"
            },
            {
                "name": "City Oil",
                "address": "Entebbe Road, Kampala",
                "rating": 4.2,
                "review_count": 134,
                "distance": "2.0 km",
                "image_url": "assets/images/cityoil.png",
                "latitude": 0.3445,
                "longitude": 32.5790,
                "is_open": True,
                "price_per_litre": "UGX 4,790",
                "fuel_types": ["Petrol 95", "Diesel", "Kerosene"],
                "phone": "+256 414 567890",
                "opening_hours": "6:00 AM - 11:00 PM"
            }
        ]

        for s_data in station_data:
            station = FuelStation.objects.create(**s_data)
            stations.append(station)

        # 4. Create Fuel Orders (historical data to populate charts)
        statuses = ["DELIVERED", "PENDING", "ONGOING", "CANCELLED"]
        status_weights = [0.65, 0.15, 0.12, 0.08]

        fuel_type_prices = {
            "Petrol 95": 4800,
            "Petrol 98": 4900,
            "Diesel": 4700,
            "Kerosene": 3800,
            "LPG": 5500,
            "V-Power": 5200
        }

        # Generate orders for the last 10 days
        for day_offset in range(10):
            # Sort from oldest to newest for historical graphing
            order_date = timezone.now() - timedelta(days=9 - day_offset)
            
            # Create between 2 to 7 orders per day
            num_orders_per_day = random.randint(3, 7)
            for _ in range(num_orders_per_day):
                customer = random.choice(customers)
                station = random.choice(stations)
                
                # Pick a fuel type available at the station
                available_fuels = station.fuel_types
                if not available_fuels:
                    available_fuels = ["Petrol 95"]
                fuel_type = random.choice(available_fuels)
                
                quantity = round(random.uniform(10.0, 100.0), 1)
                price_per_litre = fuel_type_prices.get(fuel_type, 4800)
                total_price = quantity * price_per_litre
                
                status = random.choices(statuses, weights=status_weights)[0]
                
                order = FuelOrder.objects.create(
                    customer=customer,
                    station=station,
                    fuel_type=fuel_type,
                    quantity=quantity,
                    total_price=total_price,
                    status=status
                )
                
                # Manually adjust created_at & updated_at for historical representation
                FuelOrder.objects.filter(pk=order.pk).update(created_at=order_date, updated_at=order_date)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded database: {User.objects.count()} Users, "
            f"{FuelStation.objects.count()} Stations, {FuelOrder.objects.count()} Orders."
        ))
