from django.urls import path
from .views import (
    CheckoutView,
    OrderListView,
    OrderDetailView,
    OrderDeleteView,
    OrderDeleteAllView,
    OrderStatusUpdateView
)

urlpatterns = [
    path("checkout/", CheckoutView.as_view()),
    path("", OrderListView.as_view()),
    path("<int:pk>/", OrderDetailView.as_view()),
    path("<int:pk>/delete/", OrderDeleteView.as_view()),
    path("delete-all/", OrderDeleteAllView.as_view()),
    path("<int:pk>/status/", OrderStatusUpdateView.as_view()),
]
