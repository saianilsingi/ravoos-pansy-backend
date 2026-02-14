from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .models import Payment
from .services import calculate_cart_total, create_razorpay_order
from users.models import Address
import razorpay
from django.db import transaction
from cart.models import CartItem
from orders.models import Order,OrderItem


class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        address_id = request.data.get("address_id")
        coupon_code = request.data.get("coupon")

        # Validate address
        try:
            address = Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            return Response({"error": "Invalid address"}, status=400)

        try:
            totals = calculate_cart_total(user, coupon_code)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        # Create Razorpay order
        razorpay_order = create_razorpay_order(totals["total"])

        # Create Payment record (temporary state)
        payment = Payment.objects.create(
            user=user,
            amount=totals["total"],
            address=address,
            coupon=totals["coupon"],
            razorpay_order_id=razorpay_order["id"],
        )

        return Response({
            "payment_id": payment.id,
            "razorpay_order_id": razorpay_order["id"],
            "amount": totals["total"],
            "currency": "INR",
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        })
    
import razorpay
from django.db import transaction
from cart.models import CartItem
from orders.models import Order, OrderItem


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        try:
            payment = Payment.objects.get(
                razorpay_order_id=razorpay_order_id,
                user=user,
                status="created"
            )
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=404)

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
        except razorpay.errors.SignatureVerificationError:
            payment.status = "failed"
            payment.save(update_fields=["status"])
            return Response({"error": "Payment verification failed"}, status=400)

        with transaction.atomic():
            payment.status = "paid"
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.save()

            cart_items = CartItem.objects.filter(user=user)
            if not cart_items.exists():
                return Response({"error": "Cart empty"}, status=400)

            order = Order.objects.create(
                user=user,
                subtotal=payment.amount,
                gst=0,
                discount=0,
                total=payment.amount,
                address_text=str(payment.address),
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                )

            cart_items.delete()

            payment.order = order
            payment.save(update_fields=["order"])

        return Response({
            "message": "Payment successful",
            "order_id": order.id,
        })