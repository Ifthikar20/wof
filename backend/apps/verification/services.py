from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.audit import services as audit
from apps.common.hashing import new_token, sha256_hex

from .models import Company, FounderProfile, VerificationRequest


class VerificationError(Exception):
    pass


def send_work_email_token(req: VerificationRequest) -> None:
    raw, digest = new_token()
    req.email_token_hash = digest
    req.email_token_expires_at = timezone.now() + settings.VERIFICATION_TOKEN_TTL
    req.save(update_fields=["email_token_hash", "email_token_expires_at"])
    link = f"{settings.SITE_URL}/verify/confirm?token={raw}"
    send_mail(
        subject="Confirm your work email - Wall of Founders",
        message=(
            f"Someone (hopefully you) asked to verify {req.work_email} as a founder of "
            f"{req.company_name} on Wall of Founders.\n\nConfirm within 24 hours:\n{link}\n\n"
            "If this wasn't you, ignore this email - nothing will happen."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[req.work_email],
    )


def submit(user, data: dict, request=None) -> VerificationRequest:
    req = _create_request(user, data, request)
    send_work_email_token(req)  # after commit: the row exists before the link does
    return req


@transaction.atomic
def _create_request(user, data: dict, request=None) -> VerificationRequest:
    # Supersede anything still open so a user cannot stack parallel requests.
    VerificationRequest.objects.filter(
        user=user, status__in=VerificationRequest.OPEN_STATUSES
    ).update(status=VerificationRequest.Status.WITHDRAWN, email_token_hash="")
    req = VerificationRequest.objects.create(user=user, **data)
    audit.record(
        "verification.submitted",
        actor=user,
        target=req,
        request=request,
        metadata={"domain": req.company_domain},
    )
    return req


@transaction.atomic
def confirm_email(user, raw_token: str, request=None) -> VerificationRequest:
    digest = sha256_hex(raw_token or "")
    req = (
        VerificationRequest.objects.select_for_update()
        .filter(user=user, email_token_hash=digest, status=VerificationRequest.Status.EMAIL_PENDING)
        .first()
    )
    if req is None:
        raise VerificationError("Invalid or already-used link.")
    if req.email_token_expires_at is None or req.email_token_expires_at < timezone.now():
        raise VerificationError("This link has expired. Please request a new one.")
    req.email_token_hash = ""  # single use
    req.email_verified_at = timezone.now()
    req.status = VerificationRequest.Status.UNDER_REVIEW
    req.save(update_fields=["email_token_hash", "email_verified_at", "status"])
    audit.record("verification.email_confirmed", actor=user, target=req, request=request)
    return req


@transaction.atomic
def decide(
    req: VerificationRequest, reviewer, decision: str, reason: str = "", request=None
) -> VerificationRequest:
    req = VerificationRequest.objects.select_for_update().get(pk=req.pk)
    if req.status not in (
        VerificationRequest.Status.UNDER_REVIEW,
        VerificationRequest.Status.NEEDS_INFO,
    ):
        raise VerificationError("Request is not awaiting review.")
    if reviewer.pk == req.user_id:
        raise VerificationError("You cannot review your own verification.")
    now = timezone.now()

    if decision == "approve":
        company, _ = Company.objects.get_or_create(
            domain=req.company_domain,
            defaults={"name": req.company_name, "crunchbase_url": req.crunchbase_url},
        )
        FounderProfile.objects.update_or_create(
            user=req.user,
            defaults={
                "company": company,
                "title": req.role_title,
                "status": FounderProfile.Status.VERIFIED,
                "verified_at": now,
                "expires_at": now + settings.VERIFICATION_VALIDITY,
                "linkedin_url": req.linkedin_url,
            },
        )
        req.status = VerificationRequest.Status.APPROVED
    elif decision == "reject":
        req.status = VerificationRequest.Status.REJECTED
    elif decision == "needs_info":
        req.status = VerificationRequest.Status.NEEDS_INFO
    else:
        raise VerificationError("Unknown decision.")

    req.reviewed_by = reviewer
    req.reviewed_at = now
    req.decision_reason = reason[:500]
    if req.status in (VerificationRequest.Status.APPROVED, VerificationRequest.Status.REJECTED):
        req.notes = ""  # data minimisation: purge evidence once decided
    req.save()
    audit.record(
        f"verification.{decision}",
        actor=reviewer,
        target=req,
        request=request,
        metadata={"user": str(req.user_id), "reason": reason[:200]},
    )
    return req


@transaction.atomic
def revoke(profile: FounderProfile, actor, reason: str, request=None) -> None:
    profile.status = FounderProfile.Status.REVOKED
    profile.save(update_fields=["status"])
    audit.record(
        "founder.revoked",
        actor=actor,
        target=profile,
        request=request,
        metadata={"user": str(profile.user_id), "reason": reason[:200]},
    )


def expire_due() -> int:
    due = FounderProfile.objects.filter(
        status=FounderProfile.Status.VERIFIED, expires_at__lte=timezone.now()
    )
    count = 0
    for profile in due:
        profile.status = FounderProfile.Status.EXPIRED
        profile.save(update_fields=["status"])
        audit.record("founder.expired", target=profile)
        count += 1
    return count
