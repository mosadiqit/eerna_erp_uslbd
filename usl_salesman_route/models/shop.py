from odoo import api, fields, models


class Shop(models.Model):
    _inherit = 'res.partner'

    shop_name = fields.Char(string='Shop Name')




