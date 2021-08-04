from odoo import api, fields, models 

class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    def post(self):
        return super(AccountPaymentInherit, self).post()


class SaleOrderInherited(models.Model):
    _inherit = 'sale.order'

    order_made_from = fields.Selection([
        ('erp', 'ERP'),
        ('api', 'API')
    ], string='Made_From', default='erp')