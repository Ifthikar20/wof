from django.contrib import admin

from .models import Media, Story, StoryRevision, Tag


class RevisionInline(admin.TabularInline):
    model = StoryRevision
    fields = ("number", "content_hash", "chain_hash", "created_by", "created_at")
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "published_at", "like_count", "featured_at")
    list_filter = ("status", "tags")
    search_fields = ("title", "slug", "author__handle")
    # Staff cannot silently rewrite a founder's words: content fields are read-only here.
    # Moderation happens through status changes, which are audited.
    readonly_fields = (
        "id",
        "author",
        "slug",
        "title",
        "dek",
        "body_markdown",
        "body_html",
        "revision_number",
        "content_hash",
        "like_count",
        "save_count",
        "comment_count",
        "published_at",
        "created_at",
        "updated_at",
        "cover",
        "status",
    )
    fields = readonly_fields + ("featured_at", "tags")
    inlines = [RevisionInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = [f.name for f in Media._meta.fields]

    def has_add_permission(self, request):
        return False
