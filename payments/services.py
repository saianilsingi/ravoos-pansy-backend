from decimal import Decimal
from django.conf import settings
from cart.models import CartItem
from coupons.models import Coupon
from users.models import Address
import razorpay

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def calculate_cart_total(user, coupon_code=None):
    cart_items = CartItem.objects.filter(user=user)

    if not cart_items.exists():
        raise ValueError("Cart is empty")

    subtotal = Decimal("0")
    for item in cart_items:
        subtotal += item.product.price * item.quantity

    gst = subtotal * Decimal("0.05")

    discount = Decimal("0")
    coupon = None
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            discount = coupon.discount_amount
        except Coupon.DoesNotExist:
            raise ValueError("Invalid coupon")

    total = subtotal + gst - discount
    if total < 0:
        total = Decimal("0")

    return {
        "subtotal": subtotal,
        "gst": gst,
        "discount": discount,
        "total": total,
        "coupon": coupon,
    }


def create_razorpay_order(amount):
    # Razorpay expects amount in paise
    data = {
        "amount": int(amount * 100),
        "currency": "INR",
        "payment_capture": 1,
    }
    return razorpay_client.order.create(data=data)