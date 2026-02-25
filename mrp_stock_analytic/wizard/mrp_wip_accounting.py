# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, fields, models


class MrpWipAccountingLine(models.TransientModel):
    _name = "mrp.account.wip.accounting.line"
    _inherit = ["mrp.account.wip.accounting.line", "analytic.mixin"]

    # Required by analytic.mixin for validating analytic distribution against
    # company-specific analytic plans (see analytic.mixin._validate_distribution)
    company_id = fields.Many2one(
        "res.company",
        related="wip_accounting_id.journal_id.company_id",
        store=True,
        readonly=True,
    )


class MrpWipAccounting(models.TransientModel):
    _inherit = "mrp.account.wip.accounting"

    @api.depends("date")
    def _compute_line_ids(self):
        super()._compute_line_ids()
        wip_account_id = self.env.company.account_production_wip_account_id.id
        for wizard in self:
            if not wizard.mo_ids:
                continue
            # Aggregate analytic distribution from all selected manufacturing orders
            merged = defaultdict(float)
            for dist in wizard.mo_ids.mapped("analytic_distribution"):
                if dist:
                    for k, v in dist.items():
                        # Sum up percentages per analytic account across MOs
                        merged[k] += v
            if not merged:
                continue
            # Find the WIP line (only the initial WIP debit line uses this account)
            wip_line = wizard.line_ids.filtered(
                lambda line: line.account_id.id == wip_account_id
            )
            if wip_line:
                wip_line.analytic_distribution = dict(merged)
        return

    def confirm(self):
        line_analytic = {
            line.label: line.analytic_distribution
            for line in self.line_ids
            if line.analytic_distribution
        }
        # Pass analytic distribution via context to account.move creation
        if line_analytic:
            self = self.with_context(wip_analytic_distribution=line_analytic)
        return super().confirm()
