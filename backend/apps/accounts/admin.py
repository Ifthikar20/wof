from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "handle", "role", "is_suspended", "totp_enabled", "date_joined")
    list_filter = ("role", "is_suspended", "totp_enabled")
    search_fields = ("email", "handle", "display_name")
    readonly_fields = (
        "id",
        "password",
        "totp_secret",
        "totp_last_used_step",
        "last_login",
        "date_joined",
        "failed_login_count",
        "locked_until",
    )
    exclude = ("user_permissions", "groups")
