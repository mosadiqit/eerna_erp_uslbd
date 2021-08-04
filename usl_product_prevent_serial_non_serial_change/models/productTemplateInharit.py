from odoo import models, fields, api
from odoo import exceptions



class ProductTemplateInharit(models.Model):
    _inherit = 'product.template'
    _description = 'ProductTemplateInharit'

    def write(self, vals):
        print('self of product template :', self)
        print('vals of product template :', vals)
        if 'tracking' in vals and self.qty_available > 0:
            raise exceptions.ValidationError('please do not change all track visibelity before all product sold')

        return super(ProductTemplateInharit, self).write(vals)
