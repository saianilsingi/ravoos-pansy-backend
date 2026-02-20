from django.urls import path
from .views import AdminOrderListView, AdminOrderDetailView

urlpatterns = [
    path("", AdminOrderListView.as_view()),
    path("<int:pk>/", AdminOrderDetailView.as_view()),
]
