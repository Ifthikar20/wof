from django.urls import path

from . import passwords, privacy, views

urlpatterns = [
    path("csrf", views.CsrfView.as_view()),
    path("signup", views.SignupView.as_view()),
    path("login", views.LoginView.as_view()),
    path("logout", views.LogoutView.as_view()),
    path("me", views.MeView.as_view()),
    path("me/export", privacy.ExportView.as_view()),
    path("me/delete", privacy.DeleteAccountView.as_view()),
    path("2fa/setup", views.TotpSetupView.as_view()),
    path("2fa/confirm", views.TotpConfirmView.as_view()),
    path("password", passwords.PasswordChangeView.as_view()),
    path("password/reset", passwords.PasswordResetRequestView.as_view()),
    path("password/reset/confirm", passwords.PasswordResetConfirmView.as_view()),
]
