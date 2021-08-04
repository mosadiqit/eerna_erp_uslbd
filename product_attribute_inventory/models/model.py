from odoo import models,fields,api


class ProductModel(models.Model):
    _inherit = 'product.template'
    _description = 'product model'

    product_model_id = fields.Many2one('product.model', string='Model')
    product_manager_id = fields.Many2one('res.users', string='Product Manager')


class ModelProduct(models.Model):
    _name = 'product.model'
    _description = 'product model'

    name = fields.Char(String="Name")
    member_ids = fields.One2many('product.template', 'product_model_id')
    product_count = fields.Char(String='Product Count', compute='get_count_products', store=True)

    @api.depends('member_ids')
    def get_count_products(self):
        self.product_count = len(self.member_ids)


class ModelReportStock(models.Model):
    _inherit = 'stock.quant'
    _description = 'stock quant model'

    product_model_id = fields.Many2one(related='product_id.product_model_id',
                       string='Model', store=True, readonly=True)




