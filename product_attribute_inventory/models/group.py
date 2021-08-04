from odoo import models, fields, api


class ProductGroup(models.Model):
    _inherit = 'product.template'
    _description = 'product group'

    group_id = fields.Many2one('product.group', string='Group')


class GroupProduct(models.Model):
    _name = 'product.group'
    _description = 'product group'

    name = fields.Char(String="Name")
    member_ids = fields.One2many('product.template', 'group_id')
    product_count = fields.Char(String='Product Count', compute='get_count_products', store=True)

    @api.depends('member_ids')
    def get_count_products(self):
        self.product_count = len(self.member_ids)


class GroupReportStock(models.Model):
    _inherit = 'stock.quant'
    _description = 'stock quant group'

    product_group_id = fields.Many2one(related='product_id.group_id',
                       string='Group', store=True, readonly=True)
