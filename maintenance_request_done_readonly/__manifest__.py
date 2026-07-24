# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Maintenance Request Done Read-only",
    "summary": "Make completed maintenance requests read-only except for managers",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/maintenance",
    "depends": ["maintenance"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
