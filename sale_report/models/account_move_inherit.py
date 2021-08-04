from odoo import api, fields, models


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    def amount_to_word(self, DATA):
        return self.currency_id.amount_to_text(DATA)

    def get_payment_terms(self, DATA):
        s_order_payment_term = self.env['sale.order'].search([('name','=',DATA)]).payment_term_id.name
        return s_order_payment_term
