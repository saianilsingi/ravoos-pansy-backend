import warnings
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from products.models import Product
from products.permissions import IsAdmin
from cart.models import CartItem
from users.models import Address
from coupons.models import Coupon
from .models import Order, OrderItem
from .serializers import OrderSerializer, AdminOrderSerializer

#CHECKOUT VIEW
class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        warnings.warn(
            "CheckoutView is deprecated. Use /api/payments/create-intent/ "
            "followed by /api/payments/verify/ for payment-backed checkout.",
            DeprecationWarning,
            stacklevel=2,
        )
        user = request.user
        address_id = request.data.get("address_id")
        coupon_code = request.data.get("coupon")

        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        # Address
        try:
            address = Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            return Response({"error": "Invalid address"}, status=400)

        # Subtotal
        subtotal = Decimal("0")
        for item in cart_items:
            subtotal += item.product.price * item.quantity

        # GST (5%)
        gst = subtotal * Decimal("0.05")

        # Coupon
        discount = Decimal("0")
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                discount = coupon.discount_amount
            except Coupon.DoesNotExist:
                return Response({"error": "Invalid coupon"}, status=400)

        total = subtotal + gst - discount
        if total < 0:
            total = Decimal("0")

        # Create Order
        address_text = (
            f"{address.full_name}, {address.street}, "
            f"{address.city}, {address.state} - {address.pincode}"
        )

        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            gst=gst,
            discount=discount,
            total=total,
            address_text=address_text,
        )

        # Create Order Items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )

        # Clear cart
        cart_items.delete()

        return Response({
            "order_id": order.id,
            "subtotal": subtotal,
            "gst": gst,
            "discount": discount,
            "total": total,
        })
    
#ORDER HISTORY APIs
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

#Order Detail (Bill)
class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        serializer = OrderSerializer(order)
        return Response(serializer.data)

#Delete One Order
class OrderDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.status not in ["delivered", "cancelled"]:
            return Response(
                {"error": "Order can be deleted only after delivery or cancellation"},
                status=400
            )

        order.delete()
        return Response({"message": "Order deleted successfully"})


#Delete All Orders
class OrderDeleteAllView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        Order.objects.filter(user=request.user).delete()
        return Response({"message": "All orders deleted"})
    

class OrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        new_status = request.data.get("status")

        allowed_statuses = [
            "placed",
            "packing",
            "shipped",
            "out_for_delivery",
            "delivered",
            "cancelled",
        ]

        if new_status not in allowed_statuses:
            return Response({"error": "Invalid status"}, status=400)

        # Restore stock when cancelling an order (prevent double-restore)
        if new_status == "cancelled" and order.status != "cancelled":
            with transaction.atomic():
                order.status = new_status
                order.save(update_fields=["status"])

                for item in order.items.select_related("product").all():
                    if item.product_id:
                        Product.objects.filter(id=item.product_id).update(
                            stock=F("stock") + item.quantity
                        )
        else:
            order.status = new_status
            order.save(update_fields=["status"])

        return Response({
            "message": "Order status updated",
            "order_id": order.id,
            "status": order.status
        })


class AdminOrderPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 50


class AdminOrderListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = Order.objects.select_related("user").prefetch_related(
            "items__product"
        ).order_by("-created_at")

        status_filter = request.query_params.get("status")
        if status_filter and status_filter in dict(Order.STATUS_CHOICES):
            queryset = queryset.filter(status=status_filter)

        paginator = AdminOrderPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminOrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminOrderDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, pk):
        try:
            order = Order.objects.select_related("user").prefetch_related(
                "items__product"
            ).get(id=pk)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        serializer = AdminOrderSerializer(order)
        return Response(serializer.data)
