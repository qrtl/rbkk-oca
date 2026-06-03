# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    byproduct_auto_pick = fields.Selection(
        selection=[
            ("always", "Always"),
            ("never", "Never"),
        ],
        help="Controls whether a manually entered quantity for products in "
        "this category, when produced as a byproduct, is kept (marked as "
        "picked) instead of being reset to the quantity to produce. Leave "
        "empty to fall back to the parent category, then the company "
        "setting.",
    )
