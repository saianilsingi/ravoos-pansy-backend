from django.urls import path
from .views import (
    CategoryListView,
    CategoryTreeView,
    ProductListView,
    ProductDetailView,
    AdminProductListCreateView,
    AdminProductUpdateView,
    AdminProductDeleteView,
    AdminCategoryCreateView,
    AdminCategoryUpdateView,
    AdminCategoryDeleteView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view()),
    path("categories/tree/", CategoryTreeView.as_view()),
    path("products/", ProductListView.as_view()),
    path("products/<int:pk>/", ProductDetailView.as_view()),

    # Admin — Products
    path("admin/products/", AdminProductListCreateView.as_view()),
    path("admin/products/<int:pk>/", AdminProductUpdateView.as_view()),
    path("admin/products/<int:pk>/delete/", AdminProductDeleteView.as_view()),

    # Admin — Categories
    path("admin/categories/", AdminCategoryCreateView.as_view()),
    path("admin/categories/<int:pk>/", AdminCategoryUpdateView.as_view()),
    path("admin/categories/<int:pk>/delete/", AdminCategoryDeleteView.as_view()),
]
