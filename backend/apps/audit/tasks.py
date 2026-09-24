import logging

from celery import shared_task

from .services import head_hash, verify_chain

logger = logging.getLogger("wof.audit")


@shared_task
def verify_chain_task() -> dict:
    ok, bad_id = verify_chain()
    if not ok:
        # Wired to a paging alert in production (see docs/11-observability-and-operations.md).
        logger.critical("AUDIT CHAIN BROKEN at entry %s", bad_id)
    else:
        # Export the head hash off-site (object-lock bucket / external notary) for anchoring.
        logger.info("audit chain ok head=%s", head_hash())
    return {"ok": ok, "bad_id": bad_id}
