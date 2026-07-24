# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    maintenance_done_editable_field_ids = fields.Many2many(
        "ir.model.fields",
        string="Editable fields on completed requests",
        domain=[("model", "=", "maintenance.request"), ("store", "=", True)],
        help="Fields that non-managers may still edit after a maintenance "
        "request is completed. Other fields stay locked.",
    )

    def get_values(self):
        res = super().get_values()
        names = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("maintenance_request_done_readonly.editable_fields", "")
        )
        name_list = [name for name in names.split(",") if name]
        field_recs = self.env["ir.model.fields"].search(
            [("model", "=", "maintenance.request"), ("name", "in", name_list)]
        )
        res["maintenance_done_editable_field_ids"] = [(6, 0, field_recs.ids)]
        return res

    def set_values(self):
        res = super().set_values()
        names = ",".join(self.maintenance_done_editable_field_ids.mapped("name"))
        self.env["ir.config_parameter"].sudo().set_param(
            "maintenance_request_done_readonly.editable_fields", names
        )
        return res
