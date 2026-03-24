# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    is_calendar_flexible = fields.Boolean(
        related="employee_id.resource_calendar_id.flexible_hours",
    )
    rest_time = fields.Float(
        help="Rest time in hours deducted from the total worked hours.",
        compute="_compute_rest_time",
        inverse="_inverse_rest_time",
        store=True,
        readonly=False,
        tracking=True,
        aggregator="sum",
    )
    is_rest_time_readonly = fields.Boolean(
        compute="_compute_is_rest_time_readonly",
    )

    @api.depends("overtime_status", "employee_id.attendance_manager_id")
    def _compute_is_rest_time_readonly(self):
        is_manager = self.env.user.has_group(
            "hr_attendance.group_hr_attendance_manager"
        )
        is_officer = self.env.user.has_group(
            "hr_attendance.group_hr_attendance_officer"
        )
        for attendance in self:
            if is_manager:
                attendance.is_rest_time_readonly = False
            elif is_officer:
                is_attendance_manager = (
                    attendance.employee_id.attendance_manager_id == self.env.user
                )
                attendance.is_rest_time_readonly = not is_attendance_manager
            else:
                attendance.is_rest_time_readonly = (
                    attendance.overtime_status == "approved"
                )

    @api.depends("employee_id", "check_in", "check_out")
    def _compute_rest_time(self):
        for attendance in self:
            calendar = attendance._get_employee_calendar()
            if (
                not calendar
                or not calendar.flexible_hours
                or not attendance.check_in
                or not attendance.check_out
            ):
                attendance.rest_time = 0.0
                continue
            gross_hours = attendance._get_worked_hours_in_range(
                attendance.check_in, attendance.check_out
            )
            attendance.rest_time = calendar._get_rest_time(gross_hours)

    def _inverse_rest_time(self):
        self._update_overtime()

    @api.depends("check_in", "check_out", "rest_time", "employee_id")
    def _compute_worked_hours(self):
        res = super()._compute_worked_hours()
        for attendance in self.filtered(lambda a: a.worked_hours and a.rest_time):
            attendance.worked_hours -= attendance.rest_time
        return res

    def _get_pre_post_work_time(self, employee, working_times, attendance_date):
        """Subtract rest_time from work_duration so overtime is computed on net
        worked hours rather than gross (check-out − check-in) hours."""
        pre, work, post, planned = super()._get_pre_post_work_time(
            employee, working_times, attendance_date
        )
        total_rest = sum(self.mapped("rest_time"))
        return pre, work - total_rest, post, planned

    @api.constrains("rest_time")
    def _check_rest_time_positive(self):
        for record in self:
            if record.rest_time < 0:
                raise ValidationError(
                    _("Rest time must be greater than or equal to 0.")
                )

    @api.constrains("rest_time", "check_in", "check_out")
    def _check_rest_time_not_exceed_gross_time(self):
        for record in self:
            if not (record.check_in and record.check_out and record.rest_time):
                continue
            gross_hours = record._get_worked_hours_in_range(
                record.check_in, record.check_out
            )
            if record.rest_time > gross_hours:
                raise ValidationError(
                    _(
                        "Rest time (%(rest).2f hours) cannot exceed the total"
                        " time between check in and check out"
                        " (%(gross).2f hours).",
                        rest=record.rest_time,
                        gross=gross_hours,
                    )
                )
