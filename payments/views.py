import json
import logging

from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

import razorpay

from .models import Payment
from .services import (
    InsufficientStockError,
    calculate_cart_total,
    create_razorpay_order,
    verify_razorpay_signature,
    verify_webhook_signature,
    format_address,
    fulfill_payment,
)
from users.models import Address

logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        address_id = request.data.get("address_id")
        coupon_code = request.data.get("coupon")

        # Validate address belongs to the user
        try:
            address = Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            return Response({"error": "Invalid address"}, status=400)

        # Calculate totals and build cart snapshot
        try:
            totals = calculate_cart_total(user, coupon_code)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        # Create Razorpay order (server-side)
        razorpay_order = create_razorpay_order(totals["total"])

        # Freeze all financial data and snapshots into Payment
        payment = Payment.objects.create(
            user=user,
            amount=totals["total"],
            subtotal=totals["subtotal"],
            gst=totals["gst"],
            discount=totals["discount"],
            address=address,
            address_snapshot=format_address(address),
            coupon=totals["coupon"],
            coupon_code=coupon_code if coupon_code else None,
            cart_snapshot=totals["cart_snapshot"],
            razorpay_order_id=razorpay_order["id"],
        )

        return Response({
            "payment_id": payment.id,
            "razorpay_order_id": razorpay_order["id"],
            "amount": str(totals["total"]),
            "currency": "INR",
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        })


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({"error": "Missing payment parameters"}, status=400)

        # Verify signature before touching the database
        try:
            verify_razorpay_signature(
                razorpay_order_id, razorpay_payment_id, razorpay_signature
            )
        except razorpay.errors.SignatureVerificationError:
            Payment.objects.filter(
                razorpay_order_id=razorpay_order_id,
                user=request.user,
                status="created",
            ).update(status="failed")
            return Response({"error": "Payment verification failed"}, status=400)

        try:
            with transaction.atomic():
                try:
                    payment = (
                        Payment.objects
                        .select_for_update()
                        .get(razorpay_order_id=razorpay_order_id, user=request.user)
                    )
                except Payment.DoesNotExist:
                    return Response({"error": "Payment not found"}, status=404)

                # Idempotency: already processed and order exists
                if payment.status == "paid" and payment.order_id:
                    return Response({
                        "message": "Payment already verified",
                        "order_id": payment.order_id,
                        "subtotal": str(payment.subtotal),
                        "gst": str(payment.gst),
                        "discount": str(payment.discount),
                        "total": str(payment.amount),
                    })

                if payment.status == "failed":
                    return Response({"error": "Payment has failed"}, status=400)

                # Mark as paid and store Razorpay IDs
                payment.status = "paid"
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.save(update_fields=[
                    "status", "razorpay_payment_id", "razorpay_signature"
                ])

                # Create Order + OrderItems + deduct stock
                order = fulfill_payment(payment)

        except InsufficientStockError:
            # atomic() rolled back everything — mark payment as failed separately
            Payment.objects.filter(
                razorpay_order_id=razorpay_order_id,
                user=request.user,
            ).update(status="failed")
            return Response(
                {"error": "One or more items went out of stock. Payment will be refunded."},
                status=409,
            )

        return Response({
            "message": "Payment successful",
            "order_id": order.id,
            "subtotal": str(payment.subtotal),
            "gst": str(payment.gst),
            "discount": str(payment.discount),
            "total": str(payment.amount),
        })


@method_decorator(csrf_exempt, name="dispatch")
class RazorpayWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        body = request.body.decode("utf-8")
        signature = request.META.get("HTTP_X_RAZORPAY_SIGNATURE", "")
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

        # Verify HMAC signature
        try:
            verify_webhook_signature(body, signature, webhook_secret)
        except razorpay.errors.SignatureVerificationError:
            logger.warning("Webhook signature verification failed")
            return Response({"error": "Invalid signature"}, status=400)

        payload = json.loads(body)
        event = payload.get("event", "")

        # Only handle payment.captured
        if event != "payment.captured":
            return Response({"status": "ignored"})

        payment_entity = payload["payload"]["payment"]["entity"]
        razorpay_order_id = payment_entity["order_id"]
        razorpay_payment_id = payment_entity["id"]

        try:
            with transaction.atomic():
                try:
                    payment = (
                        Payment.objects
                        .select_for_update()
                        .get(razorpay_order_id=razorpay_order_id)
                    )
                except Payment.DoesNotExist:
                    logger.warning(
                        "Webhook received for unknown order: %s", razorpay_order_id
                    )
                    return Response({"status": "not_found"}, status=200)

                # Idempotency: already processed and order exists
                if payment.status == "paid" and payment.order_id:
                    return Response({"status": "already_processed"})

                if payment.status == "failed":
                    logger.warning(
                        "Webhook for previously failed payment: %s", razorpay_order_id
                    )
                    return Response({"status": "payment_failed"}, status=400)

                # Mark as paid
                payment.status = "paid"
                payment.razorpay_payment_id = razorpay_payment_id
                payment.save(update_fields=["status", "razorpay_payment_id"])

                # Create Order + OrderItems + deduct stock
                fulfill_payment(payment)

        except InsufficientStockError:
            # atomic() rolled back — mark payment as failed separately
            Payment.objects.filter(
                razorpay_order_id=razorpay_order_id,
            ).update(status="failed")
            logger.error(
                "Stock insufficient during webhook fulfillment: %s", razorpay_order_id
            )
            return Response({"status": "stock_unavailable"}, status=409)

        return Response({"status": "ok"})
