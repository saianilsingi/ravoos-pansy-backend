from django.urls import path
from .views import (
    OverviewView,
    RevenueChartView,
    OrdersByStatusView,
    TopProductsView,
    WishlistStatsView,
    CouponAnalyticsView,
)

urlpatterns = [
    path("overview/", OverviewView.as_view()),
    path("revenue-chart/", RevenueChartView.as_view()),
    path("orders-by-status/", OrdersByStatusView.as_view()),
    path("top-products/", TopProductsView.as_view()),
    path("wishlist-stats/", WishlistStatsView.as_view()),
    path("coupons/", CouponAnalyticsView.as_view()),
]
