from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User, FuelStation, FuelOrder
from .serializers import UserSerializer, UserRegisterSerializer, FuelStationSerializer, FuelOrderSerializer

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            user_data = UserSerializer(user).data
            return Response({
                "tokens": tokens,
                "user": user_data,
                "message": "Registration successful"
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone_number = request.data.get("phone_number", "").strip()
        password = request.data.get("password", "").strip()

        if not phone_number or not password:
            return Response({
                "detail": "Both phone number and password are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate custom user using phone_number
        user = authenticate(request, username=phone_number, password=password)

        if user is not None:
            if not user.is_active:
                return Response({
                    "detail": "This account is inactive."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            tokens = get_tokens_for_user(user)
            user_data = UserSerializer(user).data
            return Response({
                "tokens": tokens,
                "user": user_data,
                "message": "Login successful"
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "detail": "Invalid phone number or password."
            }, status=status.HTTP_401_UNAUTHORIZED)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        response = super().put(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Profile updated successfully",
            "data": response.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        response = super().patch(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Profile updated successfully",
            "data": response.data
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # In a real app, send OTP/Reset Link here
        return Response({
            "success": True,
            "message": "OTP sent successfully"
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        confirm_new_password = request.data.get("confirm_new_password")

        if not all([email, token, new_password, confirm_new_password]):
            return Response({"detail": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_new_password:
            return Response({"detail": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            return Response({
                "success": True,
                "message": "Password reset successful"
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found with this email."}, status=status.HTTP_404_NOT_FOUND)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Clients discard token locally. Refresh token can be blacklisted if enabled.
        # Since we want to support it cleanly, we just return success.
        return Response({
            "success": True,
            "message": "Logged out successfully"
        }, status=status.HTTP_200_OK)


class AppInfoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "total_users": User.objects.count(),
            "total_orders": FuelOrder.objects.count(),
            "active_stations": FuelStation.objects.filter(is_open=True).count(),
            "app_version": "1.0.0",
            "support_email": "support@fuelconnect.com",
            "support_phone": "+256 414 999999"
        }, status=status.HTTP_200_OK)


# ==========================================
# FUEL STATION ENDPOINTS
# ==========================================

class FuelStationListView(generics.ListAPIView):
    queryset = FuelStation.objects.all()
    serializer_class = FuelStationSerializer
    permission_classes = [permissions.AllowAny]  # Let users see stations without logging in


class FuelStationDetailView(generics.RetrieveAPIView):
    queryset = FuelStation.objects.all()
    serializer_class = FuelStationSerializer
    permission_classes = [permissions.AllowAny]


# ==========================================
# FUEL ORDER ENDPOINTS
# ==========================================

class FuelOrderListCreateView(generics.ListCreateAPIView):
    serializer_class = FuelOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users only see their own orders, admins see all
        user = self.request.user
        if user.is_staff or user.user_type == 'admin':
            return FuelOrder.objects.all().order_by('-created_at')
        return FuelOrder.objects.filter(customer=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class FuelOrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            # Users can cancel their own orders, admin can cancel any
            if request.user.is_staff or request.user.user_type == 'admin':
                order = FuelOrder.objects.get(pk=pk)
            else:
                order = FuelOrder.objects.get(pk=pk, customer=request.user)
            
            if order.status in ['DELIVERED', 'CANCELLED']:
                return Response({
                    "detail": f"Cannot cancel an order that is already {order.status.lower()}."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            order.status = 'CANCELLED'
            order.save()
            return Response({
                "success": True,
                "message": "Order cancelled successfully.",
                "data": FuelOrderSerializer(order).data
            }, status=status.HTTP_200_OK)
            
        except FuelOrder.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
