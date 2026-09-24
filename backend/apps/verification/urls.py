from django.urls import path

from . import views

urlpatterns = [
    path("", views.MyVerificationView.as_view()),
    path("/confirm-email", views.ConfirmEmailView.as_view()),
]
