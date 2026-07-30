from datetime import datetime

from app.extensions import db
from app.models.voucher import Voucher
from app.services.gwn_service import GWNService


class SyncService:

    @staticmethod
    def sync_vouchers():
        """
        NOTE: GWN.Cloud's confirmed voucher/list endpoint returns
        voucher GROUPS (batch stats), not individual voucher codes with
        their own status/MAC address. Since Kingsmaly creates one group
        per voucher (voucherNum=1), we can infer a voucher's used/unused
        status from the group's usedVoucherNum - but this is a stand-in
        until the per-code endpoint (get_voucher_group_detail) is
        confirmed, which will give a cleaner, more direct sync.
        """

        gwn = GWNService()

        groups = gwn.get_voucher_groups()

        updated = 0

        for group in groups:
            # Our group names are "KSM-{payment.reference}" - match back
            # to the Voucher row via that same reference embedded in the
            # payment relationship, since a 1-voucher group maps 1:1.
            name = group.get("name", "")
            if not name.startswith("KSM-"):
                continue  # skip groups not created by this system

            reference = name  # group name IS the payment reference

            voucher = (
                Voucher.query
                .join(Voucher.payment)
                .filter_by(reference=reference)
                .first()
            )

            if not voucher:
                continue

            used = group.get("usedVoucherNum", 0) > 0
            if used and voucher.status == "unused":
                voucher.status = "active"
                updated += 1

        db.session.commit()

        return updated
