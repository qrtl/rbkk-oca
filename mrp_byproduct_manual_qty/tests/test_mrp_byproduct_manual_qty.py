# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMrpByproductManualQty(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product_main = cls.env["product.product"].create(
            {
                "name": "Main Product",
                "type": "consu",
                "uom_id": cls.uom_unit.id,
                "is_storable": True,
            }
        )
        cls.product_byproduct = cls.env["product.product"].create(
            {
                "name": "Byproduct",
                "type": "consu",
                "uom_id": cls.uom_unit.id,
                "is_storable": True,
            }
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_main.product_tmpl_id.id,
                "type": "normal",
                "product_qty": 1.0,
                "byproduct_ids": [
                    Command.create(
                        {
                            "product_id": cls.product_byproduct.id,
                            "product_qty": 1.0,
                        }
                    )
                ],
            }
        )

    def _create_mo(self, qty=1.0):
        return self.env["mrp.production"].create(
            {
                "product_id": self.product_main.id,
                "product_qty": qty,
                "bom_id": self.bom.id,
            }
        )

    def _byproduct_move(self, mo):
        return mo.move_byproduct_ids.filtered(
            lambda m: m.product_id == self.product_byproduct
        )

    def test_byproduct_qty_change_sets_flags(self):
        mo = self._create_mo()
        mo.action_confirm()
        byproduct = self._byproduct_move(mo)
        self.assertFalse(byproduct.manual_consumption)
        self.assertFalse(byproduct.picked)
        byproduct.quantity = 3.0
        self.assertTrue(byproduct.manual_consumption)
        self.assertTrue(byproduct.picked)

    def test_manual_qty_preserved_on_qty_producing_change(self):
        mo = self._create_mo()
        mo.action_confirm()
        byproduct = self._byproduct_move(mo)
        byproduct.quantity = 5.0
        mo.qty_producing = 2.0
        self.assertEqual(byproduct.quantity, 5.0)

    def test_manual_qty_preserved_on_mark_done(self):
        mo = self._create_mo()
        mo.action_confirm()
        mo.qty_producing = 1.0
        byproduct = self._byproduct_move(mo)
        byproduct.quantity = 5.0
        mo.button_mark_done()
        self.assertEqual(mo.state, "done")
        self.assertEqual(byproduct.quantity, 5.0)

    def test_done_move_not_relocked(self):
        mo = self._create_mo()
        mo.action_confirm()
        mo.qty_producing = 1.0
        mo.button_mark_done()
        byproduct = self._byproduct_move(mo)
        self.assertEqual(byproduct.state, "done")
        prior_qty = byproduct.quantity
        # Writing to a done move's quantity must not retrigger the lock
        # logic on a finalized record.
        byproduct.with_context(skip_byproduct_filter=True)
        self.assertEqual(byproduct.quantity, prior_qty)
