from rest_framework import serializers
from products.serializers import ProductReadSerializer
from .models import WishlistItem


class WishlistReadSerializer(serializers.ModelSerializer):
    product = ProductReadSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "created_at"]


class WishlistWriteSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=WishlistItem._meta.get_field("product").related_model.objects.all()
    )

    class Meta:
        model = WishlistItem
        fields = ["product"]
