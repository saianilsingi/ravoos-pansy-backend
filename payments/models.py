from django.db import models
from django.conf import settings
from orders.models import Order
from coupons.models import Coupon
from users.models import Address

User = settings.AUTH_USER_MODEL


class Payment(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    # Who is paying
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Order is created ONLY after payment success
    order = models.OneToOneField(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment"
    )

    # Financial breakdown — frozen at intent time (immutable truth)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="INR")

    # Snapshots — frozen at intent time, used at verification
    cart_snapshot = models.JSONField(default=list)
    address_snapshot = models.TextField(default="")

    # Checkout references
    address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    coupon_code = models.CharField(max_length=20, null=True, blank=True)

    # Gateway metadata
    gateway = models.CharField(max_length=20, default="razorpay")
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.status}"