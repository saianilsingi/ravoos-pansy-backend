from django.urls import path
from .views import (
    ProductReviewListView,
    CanReviewView,
    ReviewCreateView,
    ReviewUpdateView,
    ReviewDeleteView,
    AdminReviewListView,
    AdminReviewDeleteView,
)

urlpatterns = [
    path("products/<int:product_id>/reviews/", ProductReviewListView.as_view()),
    path("products/<int:product_id>/reviews/can-review/", CanReviewView.as_view()),
    path("products/<int:product_id>/reviews/create/", ReviewCreateView.as_view()),
    path("reviews/<int:pk>/", ReviewUpdateView.as_view()),
    path("reviews/<int:pk>/delete/", ReviewDeleteView.as_view()),

    # Admin
    path("admin/reviews/", AdminReviewListView.as_view()),
    path("admin/reviews/<int:pk>/delete/", AdminReviewDeleteView.as_view()),
]
