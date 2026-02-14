from django.urls import path
from .views import CreatePaymentIntentView, VerifyPaymentView

urlpatterns = [
    path("create-intent/", CreatePaymentIntentView.as_view()),
    path("verify/", VerifyPaymentView.as_view()),
]