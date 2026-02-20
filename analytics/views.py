from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count, F, Value
from django.db.models.functions import Coalesce, TruncDay
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from products.permissions import IsAdmin
from payments.models import Payment
from orders.models import Order, OrderItem
from products.models import Product
from wishlist.models import WishlistItem
from coupons.models import Coupon
from users.models import User


ZERO = Value(Decimal("0"))


def safe_growth(last, previous):
    """Calculate growth percentage with safe division."""
    if previous == 0:
        return 100.0 if last > 0 else 0.0
    return float(((last - previous) / previous) * 100)


class OverviewView(APIView):
    """GET /api/admin/analytics/overview/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        today = now.date()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        paid_qs = Payment.objects.filter(status="paid")

        # Single aggregate for overall + paid count
        totals = paid_qs.aggregate(
            total_revenue=Coalesce(Sum("amount"), ZERO),
            total_paid_orders=Count("id"),
        )

        total_revenue = totals["total_revenue"]
        total_paid_orders = totals["total_paid_orders"]

        # AOV with safe division
        average_order_value = (
            total_revenue / total_paid_orders
            if total_paid_orders > 0
            else Decimal("0")
        )

        # Today's revenue
        revenue_today = paid_qs.filter(
            created_at__date=today
        ).aggregate(total=Coalesce(Sum("amount"), ZERO))["total"]

        # Growth: last 30 vs previous 30
        revenue_last_30 = paid_qs.filter(
            created_at__gte=thirty_days_ago
        ).aggregate(total=Coalesce(Sum("amount"), ZERO))["total"]

        revenue_prev_30 = paid_qs.filter(
            created_at__gte=sixty_days_ago,
            created_at__lt=thirty_days_ago,
        ).aggregate(total=Coalesce(Sum("amount"), ZERO))["total"]

        # Order counts
        order_counts = Order.objects.aggregate(total=Count("id"))
        orders_today = Order.objects.filter(
            created_at__date=today
        ).aggregate(total=Count("id"))["total"]

        orders_last_30 = Order.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()

        orders_prev_30 = Order.objects.filter(
            created_at__gte=sixty_days_ago,
            created_at__lt=thirty_days_ago,
        ).count()

        return Response({
            "total_revenue": total_revenue,
            "revenue_today": revenue_today,
            "total_orders": order_counts["total"],
            "orders_today": orders_today,
            "total_users": User.objects.filter(is_staff=False).count(),
            "total_products": Product.objects.filter(is_active=True).count(),
            "low_stock_products": Product.objects.filter(
                is_active=True, stock__lte=5
            ).count(),

            "total_paid_orders": total_paid_orders,
            "average_order_value": round(average_order_value, 2),

            "revenue_last_30_days": revenue_last_30,
            "revenue_previous_30_days": revenue_prev_30,
            "revenue_growth_percentage": round(
                safe_growth(revenue_last_30, revenue_prev_30), 2
            ),

            "orders_last_30_days": orders_last_30,
            "orders_previous_30_days": orders_prev_30,
            "orders_growth_percentage": round(
                safe_growth(orders_last_30, orders_prev_30), 2
            ),
        })


class RevenueChartView(APIView):
    """GET /api/admin/analytics/revenue-chart/?days=30"""
    permission_classes = [IsAdmin]

    def get(self, request):
        days = min(int(request.query_params.get("days", 30)), 365)
        start_date = timezone.now() - timedelta(days=days)

        data = (
            Payment.objects
            .filter(status="paid", created_at__gte=start_date)
            .annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(revenue=Coalesce(Sum("amount"), ZERO))
            .order_by("date")
        )

        return Response([
            {"date": entry["date"].strftime("%Y-%m-%d"), "revenue": entry["revenue"]}
            for entry in data
        ])


class OrdersByStatusView(APIView):
    """GET /api/admin/analytics/orders-by-status/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        data = (
            Order.objects
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        return Response(list(data))


class TopProductsView(APIView):
    """GET /api/admin/analytics/top-products/?limit=5"""
    permission_classes = [IsAdmin]

    def get(self, request):
        limit = min(int(request.query_params.get("limit", 5)), 50)

        data = (
            OrderItem.objects
            .filter(order__payment__status="paid", product__isnull=False)
            .values("product_id", "product__name")
            .annotate(
                total_quantity_sold=Sum("quantity"),
                revenue_generated=Sum(F("quantity") * F("price")),
            )
            .order_by("-total_quantity_sold")[:limit]
        )

        return Response([
            {
                "product_id": entry["product_id"],
                "name": entry["product__name"],
                "total_quantity_sold": entry["total_quantity_sold"],
                "revenue_generated": entry["revenue_generated"],
            }
            for entry in data
        ])


class WishlistStatsView(APIView):
    """GET /api/admin/analytics/wishlist-stats/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        total = WishlistItem.objects.count()

        most_wishlisted = (
            WishlistItem.objects
            .values("product_id", "product__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return Response({
            "total_wishlist_items": total,
            "most_wishlisted_products": [
                {
                    "product_id": entry["product_id"],
                    "name": entry["product__name"],
                    "count": entry["count"],
                }
                for entry in most_wishlisted
            ],
        })


class CouponAnalyticsView(APIView):
    """GET /api/admin/analytics/coupons/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        # Total revenue for percentage calculation
        total_revenue = Payment.objects.filter(status="paid").aggregate(
            total=Coalesce(Sum("amount"), ZERO)
        )["total"]

        # Single grouped query for all coupon metrics
        coupon_summary = (
            Payment.objects
            .filter(status="paid", coupon__isnull=False)
            .values("coupon_id", "coupon__code")
            .annotate(
                times_used=Count("id"),
                total_discount_given=Coalesce(Sum("discount"), ZERO),
                revenue_generated=Coalesce(Sum("amount"), ZERO),
                revenue_after_discount=Coalesce(Sum("subtotal"), ZERO),
            )
            .order_by("-revenue_generated")
        )

        usage_summary = []
        used_coupon_ids = set()

        for entry in coupon_summary:
            used_coupon_ids.add(entry["coupon_id"])
            times_used = entry["times_used"]
            revenue = entry["revenue_generated"]

            usage_summary.append({
                "coupon_id": entry["coupon_id"],
                "coupon_code": entry["coupon__code"],
                "times_used": times_used,
                "total_discount_given": entry["total_discount_given"],
                "revenue_generated": revenue,
                "average_order_value": round(
                    revenue / times_used if times_used > 0 else Decimal("0"), 2
                ),
                "revenue_after_discount": entry["revenue_after_discount"],
                "percentage_of_total_revenue": round(
                    float(revenue / total_revenue * 100)
                    if total_revenue > 0
                    else 0.0,
                    2,
                ),
                "revenue_per_use": round(
                    revenue / times_used if times_used > 0 else Decimal("0"), 2
                ),
            })

        # Unused coupons — coupons never attached to a paid payment
        unused_coupons = list(
            Coupon.objects
            .exclude(id__in=used_coupon_ids)
            .values("id", "code")
        )

        return Response({
            "total_coupons": Coupon.objects.count(),
            "active_coupons": Coupon.objects.filter(is_active=True).count(),
            "coupon_usage_summary": usage_summary,
            "unused_coupons": [
                {"coupon_id": c["id"], "coupon_code": c["code"]}
                for c in unused_coupons
            ],
            "top_performing_coupons": [
                {"coupon_code": c["coupon_code"], "revenue_generated": c["revenue_generated"]}
                for c in usage_summary[:5]
            ],
        })
