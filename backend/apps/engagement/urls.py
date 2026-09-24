from django.urls import path

from . import views

urlpatterns = [
    path("stories/<slug:slug>/like", views.LikeView.as_view()),
    path("stories/<slug:slug>/comments", views.CommentListView.as_view()),
    path("boards", views.BoardListView.as_view()),
    path("boards/<uuid:board_id>", views.BoardDetailView.as_view()),
    path("boards/<uuid:board_id>/saves", views.BoardSaveView.as_view()),
    path("boards/<uuid:board_id>/saves/<slug:slug>", views.BoardSaveView.as_view()),
    path("founders/<str:handle>/follow", views.FollowView.as_view()),
    path("reports", views.ReportView.as_view()),
]
