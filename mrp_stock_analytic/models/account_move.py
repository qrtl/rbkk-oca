# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        """Apply WIP analytic distribution from context during move creation."""
        moves = super().create(vals_list)
        # Apply analytic distribution from context if WIP move
        wip_analytic = self.env.context.get("wip_analytic_distribution")
        if not wip_analytic:
            return moves
        for move in moves:
            for line in move.line_ids.filtered(lambda line: line.name in wip_analytic):
                line.analytic_distribution = wip_analytic[line.name]
        return moves
