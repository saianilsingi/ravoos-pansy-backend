from rest_framework import serializers
from .models import Category, Product

#Category serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "theme"]

#READ serializer (for GET)
class ProductReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "category",
            "image",
        ]

#WRITE serializer (for POST / PUT)
class ProductWriteSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "category",
            "image",
        ]


