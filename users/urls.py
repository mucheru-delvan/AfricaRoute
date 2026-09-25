from django.urls import path

from .views import RegisterView, MeView, DispatchView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("dispatch/", DispatchView.as_view(), name="dispatch"),
]