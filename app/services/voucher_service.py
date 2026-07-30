from datetime import datetime, timedelta

from app.extensions import db
from app.models.voucher import Voucher
from app.services.gwn_service import GWNService


class VoucherService:

    @staticmethod
    def create(payment):

        gwn = GWNService()

        code = gwn.create_voucher(payment)

        expiry = datetime.utcnow() + timedelta(
            minutes=payment.plan.duration_minutes
        )

        voucher = Voucher(
            code=code,
            payment_id=payment.id,
            plan_id=payment.plan.id,
            device_limit=1,
            expires_at=expiry,
            status="unused",
        )

        db.session.add(voucher)
        db.session.commit()

        return voucher

    @staticmethod
    def disable(voucher):
        """
        Disables a voucher both locally and on GWN (via delete, since
        GWN has no separate disable endpoint - see gwn_service.py).
        Looked up by payment reference, since that's what the GWN
        voucher group is named after.
        """

        gwn = GWNService()
        gwn.disable_voucher(voucher.payment.reference)

        voucher.status = "disabled"
        db.session.commit()

        return voucher
