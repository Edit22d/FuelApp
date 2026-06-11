from rest_framework import serializers
from .models import User, FuelStation, FuelOrder

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'company_name', 
            'fleet_size', 'is_email_verified', 'auth_provider', 'user_type', 
            'location', 'vehicle_type', 'vehicle_number', 'license_number'
        ]
        read_only_fields = ['id', 'is_email_verified', 'auth_provider']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'full_name', 'email', 'phone_number', 'password', 'confirm_password',
            'user_type', 'location', 'company_name', 'fleet_size',
            'vehicle_type', 'vehicle_number', 'license_number'
        ]
        extra_kwargs = {
            'email': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class FuelStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelStation
        fields = '__all__'


class FuelOrderSerializer(serializers.ModelSerializer):
    station_details = FuelStationSerializer(source='station', read_only=True)
    customer_details = UserSerializer(source='customer', read_only=True)

    class Meta:
        model = FuelOrder
        fields = [
            'id', 'customer', 'customer_details', 'station', 'station_details', 
            'fuel_type', 'quantity', 'quantity_unit', 'total_price', 
            'currency', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['customer', 'total_price', 'currency']

    def create(self, validated_data):
        station = validated_data['station']
        
        # Calculate price based on station price per litre
        price_str = station.price_per_litre.replace('UGX', '').replace(',', '').strip()
        try:
            price_per_litre = float(price_str)
        except ValueError:
            price_per_litre = 4800.0  # fallback price
            
        quantity = float(validated_data['quantity'])
        validated_data['total_price'] = price_per_litre * quantity
        validated_data['currency'] = 'UGX'
        
        return super().create(validated_data)
