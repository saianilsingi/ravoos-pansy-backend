from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from products.models import Product
from .models import CartItem
from .serializers import CartItemSerializer
from rest_framework import status

#Get Cart Items
class CartListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            return Response(
                {"error": "Admin cannot access cart"},
                status=status.HTTP_403_FORBIDDEN
            )

        items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)


#Add to Cart
class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_staff:
            return Response(
                {"error": "Admin cannot add to cart"},
                status=status.HTTP_403_FORBIDDEN
            )

        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product
        )

        cart_item.quantity = cart_item.quantity + quantity if not created else quantity
        cart_item.save()

        return Response(
            {"message": "Added to cart"},
            status=status.HTTP_200_OK
        )


#Update Quantity
class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        if request.user.is_staff:
            return Response(
                {"error": "Admin cannot update cart"},
                status=status.HTTP_403_FORBIDDEN
            )

        item_id = request.data.get("item_id")
        quantity = request.data.get("quantity")

        if item_id is None or quantity is None:
            return Response(
                {"error": "item_id and quantity are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
        except ValueError:
            return Response(
                {"error": "Quantity must be a number"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart_item = CartItem.objects.get(
                id=item_id,
                user=request.user
            )
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if quantity <= 0:
            cart_item.delete()
            return Response(
                {"message": "Item removed from cart"},
                status=status.HTTP_200_OK
            )

        cart_item.quantity = quantity
        cart_item.save()

        return Response(
            {"message": "Cart updated successfully"},
            status=status.HTTP_200_OK
        )



#Remove Item
class RemoveCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        if request.user.is_staff:
            return Response(
                {"error": "Admin cannot remove cart items"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            CartItem.objects.get(id=pk, user=request.user).delete()
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"message": "Item removed"},
            status=status.HTTP_200_OK
        )


#Clear Cart (used after checkout)
class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        if request.user.is_staff:
            return Response(
                {"error": "Admin cannot clear cart"},
                status=status.HTTP_403_FORBIDDEN
            )

        CartItem.objects.filter(user=request.user).delete()
        return Response(
            {"message": "Cart cleared"},
            status=status.HTTP_200_OK
        )

