from decimal import Decimal
from django.conf import settings
from cart.models import CartItem
from coupons.models import Coupon
from orders.models import Order, OrderItem
import razorpay


def get_razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def create_razorpay_order(amount):
    data = {
        "amount": int(amount * 100),
        "currency": "INR",
        "payment_capture": 1,
    }
    client = get_razorpay_client()
    return client.order.create(data=data)


def verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    client = get_razorpay_client()
    client.utility.verify_payment_signature({
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    })


def verify_webhook_signature(body, signature, webhook_secret):
    client = get_razorpay_client()
    client.utility.verify_webhook_signature(body, signature, webhook_secret)


def calculate_cart_total(user, coupon_code=None):
    cart_items = CartItem.objects.filter(user=user).select_related("product")

    if not cart_items.exists():
        raise ValueError("Cart is empty")

    subtotal = Decimal("0")
    cart_snapshot = []
    for item in cart_items:
        subtotal += item.product.price * item.quantity
        cart_snapshot.append({
            "product_id": item.product.id,
            "name": item.product.name,
            "price": str(item.product.price),
            "quantity": item.quantity,
        })

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
        "cart_snapshot": cart_snapshot,
    }


def format_address(address):
    return (
        f"{address.full_name}, {address.street}, "
        f"{address.city}, {address.state} - {address.pincode}"
    )


def fulfill_payment(payment):
    """
    Creates Order + OrderItems from a Payment's frozen snapshot data.
    Clears the user's cart and links the Order to the Payment.

    MUST be called inside transaction.atomic() with the Payment row
    already locked via select_for_update().

    Returns the created Order.
    """
    order = Order.objects.create(
        user=payment.user,
        subtotal=payment.subtotal,
        gst=payment.gst,
        discount=payment.discount,
        total=payment.amount,
        address_text=payment.address_snapshot,
    )

    for item in payment.cart_snapshot:
        OrderItem.objects.create(
            order=order,
            product_id=item["product_id"],
            quantity=item["quantity"],
            price=item["price"],
        )

    payment.order = order
    payment.save(update_fields=["order"])

    CartItem.objects.filter(user=payment.user).delete()

    return order
