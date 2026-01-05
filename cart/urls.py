from django.urls import path
from .views import (
    CartListView,
    AddToCartView,
    UpdateCartItemView,
    RemoveCartItemView,
    ClearCartView,
)

urlpatterns = [
    path("", CartListView.as_view()),
    path("add/", AddToCartView.as_view()),
    path("update/", UpdateCartItemView.as_view()),
    path("remove/<int:pk>/", RemoveCartItemView.as_view()),
    path("clear/", ClearCartView.as_view()),
]
