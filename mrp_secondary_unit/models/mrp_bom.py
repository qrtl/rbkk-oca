# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

MRP_SECONDARY_UNIT_QTY_FIELD = {
    "store": True,
    "readonly": False,
    "compute": "_compute_product_qty",
    "precompute": True,
    "default": None,
}


class MrpBom(models.Model):
    _name = "mrp.bom"
    _inherit = ["mrp.bom", "mrp.bom.secondary.unit.mixin"]

    product_qty = fields.Float(**MRP_SECONDARY_UNIT_QTY_FIELD)

    def _get_product_uom(self):
        self.ensure_one()
        return (self.product_id or self.product_tmpl_id)[self._product_uom_field]

    @api.model
    def _get_secondary_uom_id_depends(self):
        return super()._get_secondary_uom_id_depends() + ["product_tmpl_id"]

    def _is_secondary_uom_allowed(self):
        """A bill of materials is defined on the template, so a unit of the
        template is allowed even when it carries a variant of its own."""
        self.ensure_one()
        secondary_uom = self.secondary_uom_id
        if secondary_uom.product_tmpl_id != self.product_tmpl_id:
            return False
        return (
            not self.product_id
            or not secondary_uom.product_id
            or secondary_uom.product_id == self.product_id
        )


class MrpBomLine(models.Model):
    _name = "mrp.bom.line"
    _inherit = ["mrp.bom.line", "mrp.bom.secondary.unit.mixin"]

    product_qty = fields.Float(**MRP_SECONDARY_UNIT_QTY_FIELD)


class MrpBomByproduct(models.Model):
    _name = "mrp.bom.byproduct"
    _inherit = ["mrp.bom.byproduct", "mrp.bom.secondary.unit.mixin"]

    product_qty = fields.Float(**MRP_SECONDARY_UNIT_QTY_FIELD)
