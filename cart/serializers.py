from rest_framework import serializers
from .models import CartItem
from products.serializers import ProductReadSerializer, ProductWriteSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductReadSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "quantity"
        ]
