from odoo import models, fields


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    date_start = fields.Datetime('Start Date', required=True,help="Starting date for the pricelist item validation")
    date_end = fields.Datetime('End Date', required=True,help="Ending valid for the pricelist item validation")

