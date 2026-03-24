# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import AccessError


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.model
    def _get_disallowed_fields(self):
        disallowed = self.env["hr.attendance.disallowed.field"].search([])
        return {rec.field_name for rec in disallowed if rec.field_name}

    def _is_attendance_manager_for_records(self):
        return self.env.user.has_group(
            "hr_attendance.group_hr_attendance_officer"
        ) and all(
            rec.employee_id.attendance_manager_id.id == self.env.uid for rec in self
        )

    @api.model
    def check_field_access_rights(self, operation, field_names):
        valid_fields = super().check_field_access_rights(operation, field_names)
        if (
            self.env.su
            or operation != "write"
            or self.env.context.get("skip_attendance_field_check")
            or not self.env.user.has_group(
                "hr_attendance_manage_own.group_hr_attendance_own_manager"
            )
            or self.env.user.has_group("hr_attendance.group_hr_attendance_manager")
        ):
            return valid_fields
        disallowed_fields = self._get_disallowed_fields()
        field_names_set = set(field_names) if field_names else set()
        forbidden = disallowed_fields.intersection(field_names_set)
        if forbidden:
            field_labels = [
                self._fields[f].string for f in sorted(forbidden) if f in self._fields
            ]
            raise AccessError(
                _("You are not allowed to modify the following fields: %s")
                % ", ".join(field_labels)
            )
        return valid_fields

    @api.model_create_multi
    def create(self, vals_list):
        own_manager = self.env.user.has_group(
            "hr_attendance_manage_own.group_hr_attendance_own_manager"
        )
        is_manager = self.env.user.has_group(
            "hr_attendance.group_hr_attendance_manager"
        )
        if not own_manager or is_manager:
            return super().create(vals_list)
        for vals in vals_list:
            temp_record = self.env["hr.attendance"].new(vals)
            if temp_record._is_attendance_manager_for_records():
                continue
            if (
                temp_record.employee_id.company_id.attendance_overtime_validation
                == "by_manager"
                and vals.get("overtime_status")
                and vals["overtime_status"] != "to_approve"
            ):
                raise AccessError(
                    _(
                        "You can only create attendance records with"
                        " 'To Approve' status."
                    )
                )
        return super().create(vals_list)

    def write(self, vals):
        if self._is_attendance_manager_for_records():
            return super(
                HrAttendance, self.with_context(skip_attendance_field_check=True)
            ).write(vals)
        own_manager = self.env.user.has_group(
            "hr_attendance_manage_own.group_hr_attendance_own_manager"
        )
        is_manager = self.env.user.has_group(
            "hr_attendance.group_hr_attendance_manager"
        )
        if own_manager and not is_manager:
            records = self.filtered(lambda r: r.overtime_status != "to_approve")
            if records:
                raise AccessError(
                    _(
                        "You cannot modify attendance records that have already"
                        " been processed (approved or refused)."
                    )
                )
        return super().write(vals)
