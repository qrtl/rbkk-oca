# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if any("quantity" in vals for vals in vals_list):
            lines.move_id._lock_byproduct_qty()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if "quantity" in vals:
            self.move_id._lock_byproduct_qty()
        return res
