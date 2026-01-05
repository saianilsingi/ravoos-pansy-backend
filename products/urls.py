from django.urls import path
from .views import (
    CategoryListView,
    ProductListView,
    ProductDetailView,
    AdminProductCreateView,
    AdminProductUpdateView,
    AdminProductDeleteView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view()),
    path("products/", ProductListView.as_view()),
    path("products/<int:pk>/", ProductDetailView.as_view()),

    # Admin
    path("admin/products/", AdminProductCreateView.as_view()),
    path("admin/products/<int:pk>/", AdminProductUpdateView.as_view()),
    path("admin/products/<int:pk>/delete/", AdminProductDeleteView.as_view()),
]
