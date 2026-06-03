# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form, TransactionCase


class TestMrpByproductAutoPick(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        manufacture_route = cls.env.ref("mrp.route_warehouse0_manufacture")
        cls.finished = cls.env["product.product"].create(
            {
                "name": "Finished",
                "type": "consu",
                "is_storable": True,
                "route_ids": [Command.set(manufacture_route.ids)],
            }
        )
        cls.component = cls.env["product.product"].create(
            {"name": "Component", "type": "consu"}
        )
        cls.byproduct = cls.env["product.product"].create(
            {"name": "Byproduct", "type": "consu", "is_storable": True}
        )
        # BoM: 1 finished = 1 component (+) 2 byproduct
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    Command.create({"product_id": cls.component.id, "product_qty": 1.0})
                ],
                "byproduct_ids": [
                    Command.create({"product_id": cls.byproduct.id, "product_qty": 2.0})
                ],
            }
        )

    def _confirm_mo(self):
        mo_form = Form(self.env["mrp.production"])
        mo_form.product_id = self.finished
        mo_form.bom_id = self.bom
        mo_form.product_qty = 1.0
        mo = mo_form.save()
        mo.action_confirm()
        return mo

    def _recompute(self, mo):
        """Reproduce the recompute that 'Produce All' triggers."""
        mo.qty_producing = 1.0
        mo._set_qty_producing(False)

    def test_always_preserves_manual_quantity(self):
        self.byproduct.byproduct_auto_pick = "always"
        mo = self._confirm_mo()
        move = mo.move_byproduct_ids
        self.assertEqual(len(move), 1)
        move.quantity = 5.0
        # Editing the byproduct quantity auto-marks the line as picked.
        self.assertTrue(move.picked)
        self._recompute(mo)
        # The manual value survives the recompute.
        self.assertEqual(move.quantity, 5.0)

    def test_never_reverts_manual_quantity(self):
        self.byproduct.byproduct_auto_pick = "never"
        mo = self._confirm_mo()
        move = mo.move_byproduct_ids
        move.quantity = 5.0
        self.assertFalse(move.picked)
        self._recompute(mo)
        # Standard behavior: reset to the quantity to produce (2 per unit).
        self.assertEqual(move.quantity, 2.0)

    def test_tracked_byproduct_pick_on_line_edit(self):
        # For tracked byproducts the quantity field is read-only; the operator
        # enters quantities through the move lines (lot numbers) instead, which
        # the form sends as move_line_ids commands on the move.
        self.byproduct.write({"tracking": "lot", "byproduct_auto_pick": "always"})
        mo = self._confirm_mo()
        move = mo.move_byproduct_ids
        self.assertFalse(move.picked)
        line = move.move_line_ids[:1]
        if line:
            move.write(
                {
                    "move_line_ids": [
                        Command.update(
                            line.id, {"quantity": 5.0, "lot_name": "BP-LOT-1"}
                        )
                    ]
                }
            )
        else:
            move.write(
                {
                    "move_line_ids": [
                        Command.create(
                            {
                                "product_id": self.byproduct.id,
                                "quantity": 5.0,
                                "lot_name": "BP-LOT-1",
                                "location_id": move.location_id.id,
                                "location_dest_id": move.location_dest_id.id,
                            }
                        )
                    ]
                }
            )
        # Editing the lot line auto-marks the byproduct as picked.
        self.assertTrue(move.picked)
        self._recompute(mo)
        # The manually entered quantity survives the recompute.
        self.assertEqual(move.quantity, 5.0)

    def test_company_default_applies(self):
        self.env.company.byproduct_auto_pick = True
        self.byproduct.byproduct_auto_pick = False
        mo = self._confirm_mo()
        move = mo.move_byproduct_ids
        move.quantity = 5.0
        self.assertTrue(move.picked)
        self._recompute(mo)
        self.assertEqual(move.quantity, 5.0)

    def test_cascade_resolution(self):
        move = self._confirm_mo().move_byproduct_ids
        category = self.byproduct.categ_id
        # Everything inherits, company off -> not auto picked.
        self.env.company.byproduct_auto_pick = False
        self.byproduct.byproduct_auto_pick = False
        category.byproduct_auto_pick = False
        self.assertFalse(move._should_auto_pick_byproduct())
        # Company default on.
        self.env.company.byproduct_auto_pick = True
        self.assertTrue(move._should_auto_pick_byproduct())
        # Category 'never' overrides the company default.
        category.byproduct_auto_pick = "never"
        self.assertFalse(move._should_auto_pick_byproduct())
        # Product 'always' overrides the category.
        self.byproduct.byproduct_auto_pick = "always"
        self.assertTrue(move._should_auto_pick_byproduct())
