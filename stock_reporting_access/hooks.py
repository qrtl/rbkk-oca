# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    if "stock.valuation.layer" not in env:
        return
    group = env.ref("stock_reporting_access.group_stock_reporting_user")
    model = env.ref("stock_account.model_stock_valuation_layer")
    existing = env["ir.model.access"].search(
        [
            ("name", "=", "stock.valuation.layer reporting"),
            ("model_id", "=", model.id),
            ("group_id", "=", group.id),
        ]
    )
    if not existing:
        env["ir.model.access"].create(
            {
                "name": "stock.valuation.layer reporting",
                "model_id": model.id,
                "group_id": group.id,
                "perm_read": True,
                "perm_write": False,
                "perm_create": False,
                "perm_unlink": False,
            }
        )
