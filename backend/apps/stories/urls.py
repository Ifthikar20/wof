from django.urls import path

from . import views

urlpatterns = [
    path("stories", views.FeedView.as_view()),
    path("stories/<slug:slug>", views.StoryDetailView.as_view()),
    path("stories/<slug:slug>/publish", views.PublishView.as_view()),
    path("stories/<slug:slug>/revisions", views.RevisionListView.as_view()),
    path("me/stories", views.MyStoriesView.as_view()),
    path("founders/<str:handle>", views.FounderView.as_view()),
    path("tags", views.TagListView.as_view()),
    path("media/uploads", views.UploadView.as_view()),
    path("media/<uuid:media_id>", views.UploadCompleteView.as_view()),
    path("media/<uuid:media_id>/complete", views.UploadCompleteView.as_view()),
]
