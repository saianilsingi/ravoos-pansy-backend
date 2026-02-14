from rest_framework.generics import ListCreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from products.permissions import IsAdmin
from .models import Coupon
from .serializers import CouponSerializer


class AdminCouponListCreateView(ListCreateAPIView):
    permission_classes = [IsAdmin]
    queryset = Coupon.objects.all().order_by("-created_at")
    serializer_class = CouponSerializer


class AdminCouponUpdateView(UpdateAPIView):
    permission_classes = [IsAdmin]
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer


class AdminCouponDeleteView(DestroyAPIView):
    permission_classes = [IsAdmin]
    queryset = Coupon.objects.all()


class ValidateCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code", "").strip()
        if not code:
            return Response({"error": "Coupon code is required"}, status=400)

        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
        except Coupon.DoesNotExist:
            return Response({"error": "Invalid or expired coupon"}, status=400)

        return Response({
            "code": coupon.code,
            "discount_amount": str(coupon.discount_amount),
        })
