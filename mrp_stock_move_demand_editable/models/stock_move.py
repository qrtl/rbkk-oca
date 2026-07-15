# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends("state", "picking_id.is_locked", "picking_type_id")
    def _compute_is_initial_demand_editable(self):
        """Make the initial demand editable on manufacturing "pick components"
        transfers (2/3-step manufacturing).

        Core keeps the demand read-only once the transfer is locked and out of
        the ``draft`` state. For component-pick transfers we want to be able to
        request a different quantity than the one strictly needed by the
        manufacturing order (e.g. move a larger quantity to the shop floor and
        return the surplus afterwards), so we allow editing as long as the move
        is not done or cancelled.
        """
        super()._compute_is_initial_demand_editable()
        candidates = self.filtered(
            lambda m: not m.is_initial_demand_editable
            and m.state not in ("done", "cancel")
            and m.picking_type_id
        )
        if not candidates:
            return
        pbm_type_ids = self.env["stock.warehouse"].sudo().search([]).pbm_type_id.ids
        for move in candidates:
            if move.picking_type_id.id in pbm_type_ids:
                move.is_initial_demand_editable = True
