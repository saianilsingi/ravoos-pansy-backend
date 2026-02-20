from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "subtotal",
            "gst",
            "discount",
            "total",
            "status",
            "created_at",
            "items",
        ]


class AdminOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name", read_only=True, default="Deleted Product"
    )

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "price"]


class AdminOrderSerializer(serializers.ModelSerializer):
    items = AdminOrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "user_name",
            "user_email",
            "subtotal",
            "gst",
            "discount",
            "total",
            "address_text",
            "status",
            "created_at",
            "items",
        ]
