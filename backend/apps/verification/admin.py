from django.contrib import admin, messages

from . import services
from .models import Company, FounderProfile, VerificationRequest


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "created_at")
    search_fields = ("name", "domain")


@admin.register(FounderProfile)
class FounderProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "title", "status", "verified_at", "expires_at")
    list_filter = ("status",)
    search_fields = ("user__email", "user__handle", "company__domain")
    readonly_fields = ("user", "company", "verified_at", "expires_at", "status")
    actions = ["revoke"]

    @admin.action(description="Revoke founder status")
    def revoke(self, request, queryset):
        for profile in queryset:
            services.revoke(profile, request.user, "revoked via admin", request=request)
        self.message_user(request, f"Revoked {queryset.count()} founder(s).", messages.WARNING)


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    """The founder-verification review queue."""

    list_display = ("work_email", "company_name", "role_title", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("work_email", "company_domain", "user__handle")
    readonly_fields = [
        f.name
        for f in VerificationRequest._meta.fields
        if f.name not in ("decision_reason", "email_token_hash")
    ]
    exclude = ("email_token_hash",)
    actions = ["approve", "reject", "needs_info"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def _decide(self, request, queryset, decision):
        done = 0
        for req in queryset:
            try:
                services.decide(req, request.user, decision, req.decision_reason, request=request)
                done += 1
            except services.VerificationError as exc:
                self.message_user(request, f"{req}: {exc}", messages.ERROR)
        self.message_user(request, f"{decision}: {done} request(s).")

    @admin.action(description="Approve selected")
    def approve(self, request, queryset):
        self._decide(request, queryset, "approve")

    @admin.action(description="Reject selected")
    def reject(self, request, queryset):
        self._decide(request, queryset, "reject")

    @admin.action(description="Request more info")
    def needs_info(self, request, queryset):
        self._decide(request, queryset, "needs_info")
