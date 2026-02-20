from rest_framework.generics import (
    ListAPIView, ListCreateAPIView, RetrieveAPIView,
    CreateAPIView, UpdateAPIView, DestroyAPIView,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product, Category
from .serializers import (
    CategorySerializer,
    CategoryTreeSerializer,
    CategoryWriteSerializer,
    ProductWriteSerializer,
    ProductReadSerializer,
)
from .permissions import IsAdmin


class CategoryListView(ListAPIView):
    """GET /api/categories/ — flat list of active categories."""
    queryset = Category.objects.filter(is_active=True).select_related("parent")
    serializer_class = CategorySerializer


class CategoryTreeView(APIView):
    """GET /api/categories/tree/ — fully nested tree."""

    def get(self, request):
        roots = Category.get_tree()
        serializer = CategoryTreeSerializer(roots, many=True)
        return Response(serializer.data)


class ProductListView(ListAPIView):
    """
    GET /api/products/?category=clothes/men/shirts&search=...
    Accepts full slug path — filters by category + all descendants.
    """
    serializer_class = ProductReadSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True
        ).select_related("category", "category__parent")

        category_path = self.request.query_params.get("category")
        search = self.request.query_params.get("search")

        if category_path:
            category = Category.resolve_slug_path(category_path)
            if category:
                descendant_ids = category.get_descendant_ids()
                queryset = queryset.filter(category_id__in=descendant_ids)
            else:
                queryset = queryset.none()

        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset


class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.filter(
        is_active=True
    ).select_related("category", "category__parent")
    serializer_class = ProductReadSerializer


# Admin APIs

class AdminProductListCreateView(ListCreateAPIView):
    permission_classes = [IsAdmin]
    queryset = Product.objects.select_related(
        "category", "category__parent"
    ).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductWriteSerializer
        return ProductReadSerializer


class AdminProductUpdateView(UpdateAPIView):
    permission_classes = [IsAdmin]
    queryset = Product.objects.all()
    serializer_class = ProductWriteSerializer


class AdminProductDeleteView(DestroyAPIView):
    permission_classes = [IsAdmin]
    queryset = Product.objects.all()


class AdminCategoryCreateView(CreateAPIView):
    permission_classes = [IsAdmin]
    queryset = Category.objects.all()
    serializer_class = CategoryWriteSerializer


class AdminCategoryUpdateView(UpdateAPIView):
    permission_classes = [IsAdmin]
    queryset = Category.objects.all()
    serializer_class = CategoryWriteSerializer


class AdminCategoryDeleteView(DestroyAPIView):
    permission_classes = [IsAdmin]
    queryset = Category.objects.all()

    def perform_destroy(self, instance):
        from rest_framework.exceptions import ValidationError

        if instance.children.exists():
            raise ValidationError(
                {"error": "Cannot delete category with child categories. Delete or reassign children first."}
            )
        if Product.objects.filter(category=instance).exists():
            raise ValidationError(
                {"error": "Cannot delete category with existing products. Reassign products first."}
            )
