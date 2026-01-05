from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import User
from .models import Address

# users/serializers.py
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            email=data['email'],
            password=data['password']
        )
        if not user:
            raise serializers.ValidationError("Invalid credentials")

        token, _ = Token.objects.get_or_create(user=user)

        return {
            "token": token.key,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": "admin" if user.is_staff else "user"
            }
        }

## Address/serializers.py
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "full_name",
            "phone",
            "street",
            "city",
            "state",
            "pincode",
            "landmark",
            "is_default"
        ]