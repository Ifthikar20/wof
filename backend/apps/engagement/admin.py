from django.contrib import admin

from .models import Board, Comment, Report


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "story", "status", "spam_flags", "created_at")
    list_filter = ("status",)
    search_fields = ("body", "author__handle")
    readonly_fields = ("id", "story", "author", "body", "spam_flags", "created_at")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("target_type", "target_id", "reason", "status", "reporter", "created_at")
    list_filter = ("status", "reason", "target_type")
    readonly_fields = (
        "id",
        "reporter",
        "target_type",
        "target_id",
        "reason",
        "details",
        "created_at",
    )


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_private", "created_at")
