from rest_framework import serializers

from .domains import (
    email_domain,
    has_mx_record,
    is_free_email_domain,
    registrable_suffix_match,
    valid_evidence_url,
)
from .models import VerificationRequest


class VerificationSubmitSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=120)
    company_domain = serializers.CharField(max_length=253)
    work_email = serializers.EmailField(max_length=254)
    role_title = serializers.CharField(max_length=80)
    linkedin_url = serializers.URLField(required=False, allow_blank=True, max_length=300)
    crunchbase_url = serializers.URLField(required=False, allow_blank=True, max_length=300)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate_company_domain(self, value):
        value = value.strip().lower().removeprefix("https://").removeprefix("http://")
        value = value.split("/")[0].removeprefix("www.")
        if "." not in value or " " in value:
            raise serializers.ValidationError("Enter a domain like acme.com.")
        return value

    def validate(self, attrs):
        work_email = attrs["work_email"].strip().lower()
        attrs["work_email"] = work_email
        domain = email_domain(work_email)
        if is_free_email_domain(domain) or is_free_email_domain(attrs["company_domain"]):
            raise serializers.ValidationError(
                {"work_email": "Use your company email address, not a personal mailbox."}
            )
        if not registrable_suffix_match(domain, attrs["company_domain"]):
            raise serializers.ValidationError(
                {"work_email": "Work email must be on your company's domain."}
            )
        if not has_mx_record(domain):
            raise serializers.ValidationError({"work_email": "This domain cannot receive email."})

        evidence = 0
        for field in ("linkedin_url", "crunchbase_url"):
            url = attrs.get(field) or ""
            if url:
                if not valid_evidence_url(field, url):
                    raise serializers.ValidationError({field: "Must be an https link to the site."})
                evidence += 1
        if evidence == 0:
            raise serializers.ValidationError(
                {"linkedin_url": "Provide a LinkedIn or Crunchbase link as evidence."}
            )
        return attrs


class VerificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationRequest
        fields = [
            "id",
            "company_name",
            "company_domain",
            "work_email",
            "role_title",
            "linkedin_url",
            "crunchbase_url",
            "status",
            "decision_reason",
            "created_at",
        ]
        read_only_fields = fields


class ModeratorVerificationSerializer(VerificationRequestSerializer):
    user_handle = serializers.CharField(source="user.handle", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta(VerificationRequestSerializer.Meta):
        fields = VerificationRequestSerializer.Meta.fields + [
            "user_handle",
            "user_email",
            "notes",
            "email_verified_at",
        ]
        read_only_fields = fields


class DecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject", "needs_info"])
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128)
