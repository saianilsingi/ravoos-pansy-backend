from django.urls import path
from .views import CreatePaymentIntentView, VerifyPaymentView, RazorpayWebhookView

urlpatterns = [
    path("create-intent/", CreatePaymentIntentView.as_view()),
    path("verify/", VerifyPaymentView.as_view()),
    path("webhook/", RazorpayWebhookView.as_view()),
]