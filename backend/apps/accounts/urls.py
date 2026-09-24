from django.urls import path

from . import views

urlpatterns = [
    path("csrf", views.CsrfView.as_view()),
    path("signup", views.SignupView.as_view()),
    path("login", views.LoginView.as_view()),
    path("logout", views.LogoutView.as_view()),
    path("me", views.MeView.as_view()),
    path("2fa/setup", views.TotpSetupView.as_view()),
    path("2fa/confirm", views.TotpConfirmView.as_view()),
]
