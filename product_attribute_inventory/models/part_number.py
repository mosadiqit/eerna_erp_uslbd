from odoo import models, fields, api


class ProductPartNumber(models.Model):
    _inherit = 'product.template'
    _description = 'product part number'

    part_number_id = fields.Many2one('product.part_number', string='Part Number')


class PartNumberProduct(models.Model):
    _name = 'product.part_number'
    _description = 'product part number'

    name = fields.Char(String="Name")
    member_ids = fields.One2many('product.template', 'part_number_id')
    product_count = fields.Char(String='Product Count', compute='get_count_products', store=True)

    @api.depends('member_ids')
    def get_count_products(self):
        self.product_count = len(self.member_ids)


class PartNumberReportStock(models.Model):
    _inherit = 'stock.quant'
    _description = 'stock quant part number'

    part_number_id = fields.Many2one(related='product_id.part_number_id',
                     string='Part Number', store=True, readonly=True)
