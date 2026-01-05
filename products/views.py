from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
from .models import Product, Category
from .serializers import CategorySerializer, ProductWriteSerializer, ProductReadSerializer
from .permissions import IsAdmin

class CategoryListView(ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer

class ProductListView(ListAPIView):
    serializer_class = ProductReadSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category = self.request.query_params.get("category")
        search = self.request.query_params.get("search")

        if category:
            queryset = queryset.filter(category__slug=category)

        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductReadSerializer


#admin apis

class AdminProductCreateView(CreateAPIView):
    permission_classes = [IsAdmin]
    queryset = Product.objects.all()
    serializer_class = ProductWriteSerializer

class AdminProductUpdateView(UpdateAPIView):
    permission_classes = [IsAdmin]
    queryset = Product.objects.all()
    serializer_class = ProductWriteSerializer

class AdminProductDeleteView(DestroyAPIView):
    permission_classes = [IsAdmin]
    queryset = Product.objects.all()
