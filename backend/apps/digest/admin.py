from django.contrib import admin, messages
from django.utils import timezone

from apps.audit import services as audit

from .models import DigestIssue, DigestItem, Subscription


class ItemInline(admin.TabularInline):
    model = DigestItem
    extra = 0
    autocomplete_fields = ()
    raw_id_fields = ("story",)


@admin.register(DigestIssue)
class DigestIssueAdmin(admin.ModelAdmin):
    list_display = ("number", "subject", "status", "week_of", "send_at", "sent_at")
    list_filter = ("status",)
    inlines = [ItemInline]
    readonly_fields = ("status", "sent_at", "approved_by")
    actions = ["approve_and_schedule"]

    @admin.action(description="Approve & schedule (sends at 'send at' or next run)")
    def approve_and_schedule(self, request, queryset):
        for issue in queryset.filter(status=DigestIssue.Status.DRAFT):
            issue.status = DigestIssue.Status.SCHEDULED
            issue.approved_by = request.user
            issue.send_at = issue.send_at or timezone.now()
            issue.save()
            audit.record("digest.approved", actor=request.user, target=issue, request=request)
        self.message_user(request, "Scheduled.", messages.SUCCESS)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "confirmed_at", "created_at")
    list_filter = ("status",)
    search_fields = ("email",)
    readonly_fields = (
        "id",
        "email",
        "user",
        "confirmed_at",
        "unsubscribed_at",
        "confirmation_sent_at",
        "created_at",
    )
