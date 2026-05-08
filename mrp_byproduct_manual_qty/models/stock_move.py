# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _lock_byproduct_qty(self):
        # Reuse core's manual_consumption + picked bypass so the user-entered
        # byproduct quantity is not recomputed from the BoM on completion.
        moves = self.filtered(
            lambda m: m.production_id
            and m.byproduct_id
            and not (m.manual_consumption and m.picked)
            and m.state not in ("done", "cancel")
        )
        if moves:
            moves.write({"manual_consumption": True, "picked": True})
