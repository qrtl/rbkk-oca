# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockMoveDemandEditable(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        # Configure 2-step manufacturing (pick components then manufacture).
        cls.warehouse.write({"manufacture_steps": "pbm"})

        cls.component = cls.env["product.product"].create(
            {"name": "Test Component", "type": "consu", "is_storable": True}
        )
        cls.finished = cls.env["product.product"].create(
            {"name": "Test Finished", "type": "consu", "is_storable": True}
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (0, 0, {"product_id": cls.component.id, "product_qty": 1.0})
                ],
            }
        )

    def _create_confirmed_mo(self, qty=5.0):
        mo = self.env["mrp.production"].create(
            {
                "product_id": self.finished.id,
                "product_qty": qty,
                "bom_id": self.bom.id,
            }
        )
        mo.action_confirm()
        return mo

    def test_pick_component_demand_editable(self):
        """The demand of a locked pick-components transfer is editable."""
        self.assertTrue(self.warehouse.pbm_type_id)
        mo = self._create_confirmed_mo(qty=5.0)
        pick_move = mo.move_raw_ids.move_orig_ids
        self.assertTrue(pick_move, "The pick-components move should be created.")
        picking = pick_move.picking_id
        self.assertEqual(picking.picking_type_id, self.warehouse.pbm_type_id)
        # It is locked and past draft: core would normally lock the demand.
        self.assertTrue(picking.is_locked)
        self.assertNotIn(pick_move.state, ("draft", "done", "cancel"))
        self.assertTrue(
            pick_move.is_initial_demand_editable,
            "The demand should be editable on a pick-components transfer.",
        )
        # The demand can actually be changed (e.g. over-pick 5 -> 7).
        pick_move.product_uom_qty = 7.0
        self.assertEqual(pick_move.product_uom_qty, 7.0)

    def test_regular_transfer_demand_not_editable(self):
        """A regular locked internal transfer keeps its demand read-only."""
        internal_type = self.warehouse.int_type_id
        self.assertNotEqual(internal_type, self.warehouse.pbm_type_id)
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": internal_type.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.warehouse.pbm_loc_id.id,
            }
        )
        move = self.env["stock.move"].create(
            {
                "name": "Test regular move",
                "product_id": self.component.id,
                "product_uom_qty": 3.0,
                "product_uom": self.component.uom_id.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.warehouse.pbm_loc_id.id,
                "picking_id": picking.id,
            }
        )
        picking.action_confirm()
        self.assertTrue(picking.is_locked)
        self.assertNotIn(move.state, ("draft", "done", "cancel"))
        self.assertFalse(
            move.is_initial_demand_editable,
            "A regular locked transfer should keep its demand read-only.",
        )
