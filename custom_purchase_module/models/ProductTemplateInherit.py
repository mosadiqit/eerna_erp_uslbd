from odoo import fields, models
class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    probational_cost_ok = fields.Boolean('Is a Probational Cost', help='Indicates whether the product is a probational cost.')
    probational_percentage_ok=fields.Boolean('Is Probational Percentage', help='Indicates whether the product is probational Percentage.')
    percentage=fields.Float(string='Percentage Amount')