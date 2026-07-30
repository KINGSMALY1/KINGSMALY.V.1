from celery import shared_task


@shared_task
def sync_vouchers():

    from app.services.sync_service import SyncService
    SyncService.sync_vouchers()


@shared_task
def expire_vouchers():

    from datetime import datetime

    from app.extensions import db
    from app.models.voucher import Voucher

    vouchers = Voucher.query.filter(
        Voucher.expires_at <= datetime.utcnow(),
        Voucher.status != "expired",
    ).all()

    for voucher in vouchers:
        voucher.status = "expired"

    db.session.commit()
