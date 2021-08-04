# Copyright (C) 2018 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ForeignPurchaseConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_foreign_purchase_disable_adding_lines = fields.Boolean(
        string="Disable adding more lines to SOs",
        implied_group="foreign_purchase_order."
        "foreign_purchase_orders_disable_adding_lines",
    )
