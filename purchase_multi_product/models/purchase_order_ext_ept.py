from odoo import models,fields,api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def open_multi_product_selection_wizard(self):
        return self.env['purchase.multi.products'].wizard_view()