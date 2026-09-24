from django.urls import path

from . import views

urlpatterns = [
    path("verifications", views.VerificationQueueView.as_view()),
    path("verifications/<uuid:request_id>/decision", views.VerificationDecisionView.as_view()),
    path("reports", views.ReportQueueView.as_view()),
    path("comments/held", views.HeldCommentsView.as_view()),
    path("actions", views.ActionView.as_view()),
]
