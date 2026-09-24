from datetime import datetime

import pyotp

ISSUER = "Wall of Founders"


def new_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def verify(user, code: str) -> bool:
    """Verify a TOTP code, allowing +-1 step of clock drift and rejecting replays."""
    if not user.totp_secret or not code or not code.isdigit():
        return False
    totp = pyotp.TOTP(user.totp_secret)
    now_step = totp.timecode(datetime.now())
    for step in (now_step - 1, now_step, now_step + 1):
        if step <= user.totp_last_used_step:
            continue
        if pyotp.utils.strings_equal(totp.generate_otp(step), code):
            user.totp_last_used_step = step
            user.save(update_fields=["totp_last_used_step"])
            return True
    return False
