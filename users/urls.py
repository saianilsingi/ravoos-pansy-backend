from django.urls import path
from .views import SignupView, LoginView, MeView
#Address imports
from .views import (
    AddressListCreateView,
    AddressUpdateView,
    AddressDeleteView,
)

urlpatterns = [
    path('signup/', SignupView.as_view()),
    path('login/', LoginView.as_view()),
    path('me/', MeView.as_view()),
]

#Address urls
urlpatterns += [
    path("addresses/", AddressListCreateView.as_view()),
    path("addresses/<int:pk>/", AddressUpdateView.as_view()),
    path("addresses/<int:pk>/delete/", AddressDeleteView.as_view()),
]
