from django.urls import path

from . import views, webhooks

urlpatterns = [
    path("subscribe", views.SubscribeView.as_view()),
    path("confirm", views.ConfirmView.as_view()),
    path("unsubscribe", views.unsubscribe_view),
    path("issues", views.IssueArchiveView.as_view()),
    path("issues/<int:number>", views.IssueDetailView.as_view()),
    path("webhooks/postmark", webhooks.postmark_webhook),
]
