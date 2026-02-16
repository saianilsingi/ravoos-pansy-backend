from django.db import IntegrityError, transaction
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from products.permissions import IsAdmin
from .models import Review
from .serializers import ReviewReadSerializer, ReviewWriteSerializer, AdminReviewReadSerializer
from .permissions import IsReviewAuthor
from .services import has_purchased_product, refresh_product_rating


class ReviewPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class ProductReviewListView(ListAPIView):
    """GET /api/products/<product_id>/reviews/"""
    serializer_class = ReviewReadSerializer
    pagination_class = ReviewPagination

    def get_queryset(self):
        return (
            Review.objects
            .filter(product_id=self.kwargs["product_id"])
            .select_related("user")
        )


class CanReviewView(APIView):
    """GET /api/products/<product_id>/reviews/can-review/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        already_reviewed = Review.objects.filter(
            user=request.user, product_id=product_id
        ).exists()

        if already_reviewed:
            return Response({"can_review": False, "reason": "already_reviewed"})

        purchased = has_purchased_product(request.user, product_id)
        if not purchased:
            return Response({"can_review": False, "reason": "not_purchased"})

        return Response({"can_review": True, "reason": None})


class ReviewCreateView(CreateAPIView):
    """POST /api/products/<product_id>/reviews/"""
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewWriteSerializer

    def create(self, request, *args, **kwargs):
        product_id = self.kwargs["product_id"]
        user = request.user

        if not has_purchased_product(user, product_id):
            return Response(
                {"error": "You can only review products you have purchased and received"},
                status=403,
            )

        if Review.objects.filter(user=user, product_id=product_id).exists():
            return Response(
                {"error": "You have already reviewed this product"},
                status=400,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                review = serializer.save(user=user, product_id=product_id)
                refresh_product_rating(product_id)
        except IntegrityError:
            return Response(
                {"error": "You have already reviewed this product"},
                status=400,
            )

        read_serializer = ReviewReadSerializer(review, context={"request": request})
        return Response(read_serializer.data, status=201)


class ReviewUpdateView(UpdateAPIView):
    """PUT /api/reviews/<pk>/"""
    permission_classes = [IsAuthenticated, IsReviewAuthor]
    serializer_class = ReviewWriteSerializer
    queryset = Review.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            review = serializer.save()
            refresh_product_rating(review.product_id)

        read_serializer = ReviewReadSerializer(review, context={"request": request})
        return Response(read_serializer.data)


class ReviewDeleteView(DestroyAPIView):
    """DELETE /api/reviews/<pk>/delete/"""
    permission_classes = [IsAuthenticated, IsReviewAuthor]
    queryset = Review.objects.all()

    def perform_destroy(self, instance):
        product_id = instance.product_id
        with transaction.atomic():
            instance.delete()
            refresh_product_rating(product_id)


class AdminReviewListView(ListAPIView):
    """GET /api/admin/reviews/"""
    permission_classes = [IsAdmin]
    serializer_class = AdminReviewReadSerializer
    pagination_class = ReviewPagination

    queryset = (
        Review.objects
        .select_related("user", "product")
        .order_by("-created_at")
    )


class AdminReviewDeleteView(DestroyAPIView):
    """DELETE /api/admin/reviews/<pk>/delete/"""
    permission_classes = [IsAdmin]
    queryset = Review.objects.all()

    def perform_destroy(self, instance):
        product_id = instance.product_id
        with transaction.atomic():
            instance.delete()
            refresh_product_rating(product_id)
