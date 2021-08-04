from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseBasedOnSaleOrder(models.Model):
    _name = 'purchase.based.on.sale.order'

    product = fields.Many2one('product.product', string='Product')
    qty = fields.Integer(string='Quantity')
    is_purchased=fields.Boolean(string='Flag',default=True)
