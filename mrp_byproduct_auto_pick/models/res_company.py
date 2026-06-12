# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    byproduct_auto_pick = fields.Boolean(
        string="Auto-pick Manually Edited Byproducts",
        help="When enabled, a manually entered byproduct quantity on a "
        "manufacturing order is kept (marked as picked) instead of being "
        "reset to the quantity to produce.",
    )
