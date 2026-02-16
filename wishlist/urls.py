from django.urls import path
from .views import (
    WishlistListView,
    WishlistToggleView,
    WishlistRemoveView,
    WishlistMoveToCartView,
)

urlpatterns = [
    path("wishlist/", WishlistListView.as_view()),
    path("wishlist/toggle/", WishlistToggleView.as_view()),
    path("wishlist/<int:pk>/", WishlistRemoveView.as_view()),
    path("wishlist/<int:pk>/move-to-cart/", WishlistMoveToCartView.as_view()),
]
