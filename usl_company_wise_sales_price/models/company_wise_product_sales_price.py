from odoo import models, fields, api, _


class ProductPriceSetUp(models.Model):
    _name = 'product.pricelist.companywise'


    default_product_id = fields.Many2one('product.template',string="Product Id")
    default_sales_price = fields.Float(string="Default Sales Price")
    company_id = fields.Many2one('res.company',string="Company")


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    default_multi_company_price = fields.One2many('product.pricelist.companywise','default_product_id')
