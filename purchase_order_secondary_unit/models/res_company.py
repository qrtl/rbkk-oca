# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    secondary_uom_price_display = fields.Selection(
        selection=[
            ("primary", "Primary Unit Price Only"),
            ("secondary", "Prioritize Secondary Unit Price"),
            ("both", "Both Primary and Secondary Unit Prices"),
        ],
        string="Secondary Unit Price Display",
        default="primary",
        help="Configure how unit prices are displayed in purchase reports when "
        "secondary units are used.\n"
        "- Primary Unit Price Only: Shows only the primary unit price\n"
        "- Prioritize Secondary Unit Price: Shows secondary unit price when "
        "available, falls back to primary otherwise\n"
        "- Both: Shows both prices (primary and secondary)",
    )
    # Added for supporting the existing report presentation. We can drop this together
    # with the second qty column in reports if the community agrees with it.
    hide_secondary_uom_column = fields.Boolean(
        string="Hide Secondary UoM Column",
        default=False,
        help="When enabled, hides the separate Secondary Qty column in purchase "
        "reports. The secondary quantity will still be shown in the main Qty column "
        "based on the 'Secondary Unit Price Display' setting.",
    )
