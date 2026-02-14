from django.urls import path
from .views import (
    AdminCouponListCreateView,
    AdminCouponUpdateView,
    AdminCouponDeleteView,
    ValidateCouponView,
)

urlpatterns = [
    path("admin/coupons/", AdminCouponListCreateView.as_view()),
    path("admin/coupons/<int:pk>/", AdminCouponUpdateView.as_view()),
    path("admin/coupons/<int:pk>/delete/", AdminCouponDeleteView.as_view()),
    path("coupons/validate/", ValidateCouponView.as_view()),
]
