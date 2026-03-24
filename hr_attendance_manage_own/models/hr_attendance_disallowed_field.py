# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrAttendanceDisallowedField(models.Model):
    _name = "hr.attendance.disallowed.field"
    _description = "HR Attendance Disallowed Fields for Field Editors"
    _order = "field_name"

    field_id = fields.Many2one(
        "ir.model.fields",
        string="Field",
        required=True,
        domain="[('model', '=', 'hr.attendance')]",
        ondelete="cascade",
    )
    field_name = fields.Char(related="field_id.name", string="Field Name", store=True)

    _sql_constraints = [
        (
            "field_id_uniq",
            "unique(field_id)",
            "This field is already in the disallowed list!",
        )
    ]
