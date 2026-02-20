from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """Flat category — used inside ProductReadSerializer."""
    full_slug = serializers.SerializerMethodField()
    breadcrumb = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "full_slug", "theme", "breadcrumb"]

    def get_full_slug(self, obj):
        return obj.get_full_slug_path()

    def get_breadcrumb(self, obj):
        return obj.get_breadcrumb()


class CategoryTreeSerializer(serializers.Serializer):
    """Recursive tree serializer — uses pre-built _children_cache."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.SlugField()
    full_slug = serializers.SerializerMethodField()
    theme = serializers.CharField()
    children = serializers.SerializerMethodField()

    def get_full_slug(self, obj):
        return obj.get_full_slug_path()

    def get_children(self, obj):
        children = getattr(obj, "_children_cache", [])
        return CategoryTreeSerializer(children, many=True).data


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
            "stock",
            "avg_rating",
            "review_count",
        ]


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
            "stock",
        ]


class CategoryWriteSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "theme", "is_active"]

    def validate(self, data):
        instance = self.instance
        parent = data.get("parent")
        if instance and parent:
            current = parent
            while current is not None:
                if current.pk == instance.pk:
                    raise serializers.ValidationError(
                        {"parent": "A category cannot be its own ancestor."}
                    )
                current = current.parent
        return data
