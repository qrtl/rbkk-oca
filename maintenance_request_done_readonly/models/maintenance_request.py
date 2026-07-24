# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    def _writable_fields_when_done(self):
        """Fields a non-manager may still write on a completed (done) request.

        Everything else is locked by default (allow-list approach), so business
        fields - including those added by other modules - are protected without
        listing them. The set is made of:

        * mail/activity bookkeeping, so that commenting, following and
          scheduling activities keep working on a completed request;
        * the fields an administrator selected in the maintenance settings
          (stored in the ``maintenance_request_done_readonly.editable_fields``
          system parameter).

        Completion side effects (e.g. ``close_date``) are not listed here: they
        are handled through the ``mnt_done_bypass_lock`` context set below, so
        they stay protected against direct edits unless explicitly selected.
        """
        allowed = {
            "message_main_attachment_id",
            "message_follower_ids",
            "message_ids",
            "activity_ids",
        }
        names = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("maintenance_request_done_readonly.editable_fields", "")
        )
        return allowed | {name for name in names.split(",") if name}

    def write(self, vals):
        # A completed (done) request can only be edited by a maintenance
        # manager. Checked against the pre-write state, so completing a request
        # (moving it to a done stage) is still allowed for everyone. The bypass
        # context lets the internal write cascade triggered by completion (e.g.
        # close_date) through, while direct edits of those fields stay blocked.
        if (
            not self.env.user.has_group("maintenance.group_equipment_manager")
            and (set(vals) - self._writable_fields_when_done())
            and not self.env.context.get("mnt_done_bypass_lock")
        ):
            locked = self.filtered("done")
            if locked:
                raise UserError(
                    _(
                        "'%s' is completed and can only be edited by a "
                        "maintenance manager.",
                        locked[0].display_name,
                    )
                )
        records = self
        stage_id = vals.get("stage_id")
        if stage_id and self.env["maintenance.stage"].browse(stage_id).done:
            records = self.with_context(mnt_done_bypass_lock=True)
        return super(MaintenanceRequest, records).write(vals)
