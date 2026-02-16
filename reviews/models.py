from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from products.models import Product

User = settings.AUTH_USER_MODEL


class Review(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="one_review_per_user_per_product",
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_range",
            ),
        ]
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["product", "-created_at"],
                name="review_product_recent",
            ),
        ]

    def __str__(self):
        return f"{self.user} → {self.product} ({self.rating}★)"
