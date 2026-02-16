from django.db.models import Avg, Count

from orders.models import OrderItem
from products.models import Product


def has_purchased_product(user, product_id):
    """
    EXISTS subquery — stops at first match, doesn't scan all orders.
    Only delivered orders count as verified purchases.
    """
    return OrderItem.objects.filter(
        order__user=user,
        order__status="delivered",
        product_id=product_id,
    ).exists()


def refresh_product_rating(product_id):
    """
    Recalculate and persist avg_rating and review_count from scratch.
    Single aggregate + single UPDATE — no Python-level loops.
    Always correct regardless of create/update/delete context.
    """
    from .models import Review

    stats = Review.objects.filter(product_id=product_id).aggregate(
        avg=Avg("rating"),
        count=Count("id"),
    )

    Product.objects.filter(id=product_id).update(
        avg_rating=stats["avg"] or 0,
        review_count=stats["count"],
    )
