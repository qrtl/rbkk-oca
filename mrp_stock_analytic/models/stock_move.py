# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Set analytic distribution when adding a new component line
            # after the MO is confirmed
            if vals.get("raw_material_production_id") and not vals.get(
                "analytic_distribution"
            ):
                production = self.env["mrp.production"].browse(
                    vals["raw_material_production_id"]
                )
                if production.analytic_distribution:
                    vals["analytic_distribution"] = production.analytic_distribution
        return super().create(vals_list)
