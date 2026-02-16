from django.db import IntegrityError, transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from products.models import Product
from cart.models import CartItem
from .models import WishlistItem
from .serializers import WishlistReadSerializer


class WishlistListView(APIView):
    """GET /api/wishlist/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            return Response(
                {"error": "Admin cannot access wishlist"},
                status=status.HTTP_403_FORBIDDEN
            )

        items = (
            WishlistItem.objects
            .filter(user=request.user)
            .select_related("product", "product__category")
        )
        serializer = WishlistReadSerializer(items, many=True)
        return Response(serializer.data)


class WishlistToggleView(APIView):
    """POST /api/wishlist/toggle/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_staff:
            return Response(
                {"error": "Admin cannot use wishlist"},
                status=status.HTTP_403_FORBIDDEN
            )

        product_id = request.data.get("product_id")

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Try to remove first — if it exists, it's a toggle-off
        deleted, _ = WishlistItem.objects.filter(
            user=request.user, product=product
        ).delete()

        if deleted:
            return Response({"status": "removed"})

        # Not found → create (toggle-on)
        try:
            with transaction.atomic():
                WishlistItem.objects.create(
                    user=request.user, product=product
                )
        except IntegrityError:
            # Race condition: another request created it simultaneously
            # Treat as already added
            return Response({"status": "added"})

        return Response({"status": "added"}, status=status.HTTP_201_CREATED)


class WishlistRemoveView(APIView):
    """DELETE /api/wishlist/<pk>/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        if request.user.is_staff:
            return Response(
                {"error": "Admin cannot use wishlist"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            WishlistItem.objects.get(id=pk, user=request.user).delete()
        except WishlistItem.DoesNotExist:
            return Response(
                {"error": "Wishlist item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({"message": "Removed from wishlist"})


class WishlistMoveToCartView(APIView):
    """POST /api/wishlist/<pk>/move-to-cart/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.is_staff:
            return Response(
                {"error": "Admin cannot use wishlist"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            item = WishlistItem.objects.select_related("product").get(
                id=pk, user=request.user
            )
        except WishlistItem.DoesNotExist:
            return Response(
                {"error": "Wishlist item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        product = item.product

        if product.stock == 0:
            return Response(
                {"error": "This product is out of stock"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Add to cart (same pattern as AddToCartView)
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user, product=product
            )

            desired_quantity = (cart_item.quantity + 1) if not created else 1
            if desired_quantity > product.stock:
                return Response(
                    {"error": f"Only {product.stock} available"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.quantity = desired_quantity
            cart_item.save()

            # Remove from wishlist
            item.delete()

        return Response({"message": "Moved to cart"})
