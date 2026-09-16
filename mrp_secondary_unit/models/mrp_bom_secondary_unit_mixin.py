# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpBomSecondaryUnitMixin(models.AbstractModel):
    _name = "mrp.bom.secondary.unit.mixin"
    _inherit = "product.secondary.unit.mixin"
    _description = "MRP BoM Secondary Unit Mixin"
    _secondary_unit_fields = {
        "qty_field": "product_qty",
        "uom_field": "product_uom_id",
    }

    secondary_uom_id = fields.Many2one(
        compute="_compute_secondary_uom_id",
        store=True,
        readonly=False,
        precompute=True,
        default=None,
    )

    @api.model
    def _get_default_value_for_qty_field(self):
        return 1.0

    @api.model
    def _get_secondary_uom_id_depends(self):
        return ["product_id"]

    def _is_secondary_uom_allowed(self):
        """Return whether the secondary unit still belongs to the product.

        It mirrors the domain the form views put on the field, so that a unit
        left over from a previously selected product is dropped instead of
        silently converting the quantity with a foreign factor.
        """
        self.ensure_one()
        secondary_uom = self.secondary_uom_id
        if not self.product_id:
            return False
        return secondary_uom.product_id == self.product_id or (
            not secondary_uom.product_id
            and self.product_id in secondary_uom.product_tmpl_id.product_variant_ids
        )

    @api.depends(lambda x: x._get_secondary_uom_id_depends())
    def _compute_secondary_uom_id(self):
        for record in self:
            if record.secondary_uom_id and not record._is_secondary_uom_allowed():
                record.secondary_uom_id = False
                record.secondary_uom_qty = 0.0

    @api.model
    def _get_secondary_uom_qty_depends(self):
        # The factor refers to the unit of the product, so the secondary
        # quantity has to be converted again when the unit of the line changes.
        return super()._get_secondary_uom_qty_depends() + ["product_uom_id"]

    @api.depends("secondary_uom_qty", "secondary_uom_id")
    def _compute_product_qty(self):
        for record in self:
            if record.secondary_uom_id and not record.secondary_uom_qty:
                record._onchange_helper_product_uom_for_secondary()
        self._compute_helper_target_field_qty()
