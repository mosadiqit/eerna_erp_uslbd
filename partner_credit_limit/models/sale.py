# See LICENSE file for full copyright and licensing details.


from odoo import api, models, _, fields
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="[('sale_not_allow', '!=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", )



    def check_limit(self):
        self.ensure_one()

        partner = self.partner_id
        user_id = self.env['res.users'].search([
            ('partner_id', '=', partner.id)], limit=1)
        if user_id and not user_id.has_group('base.group_portal') or not \
                user_id:
            debit_movelines = self.env['account.move.line'].search(
                [('partner_id', '=', partner.id),
                 ('move_id.state', '!=', 'cancel'),
                 ('account_id.user_type_id.name', 'in',
                  ['Receivable', 'Payable'])]
            )
            credit_movelines = self.env['account.move.line'].search(
                [('partner_id', '=', partner.id),
                 ('move_id.state', '=', 'posted'),
                 ('account_id.user_type_id.name', 'in',
                  ['Receivable', 'Payable'])]
            )
            debit, credit = 0.0, 0.0
            for line in debit_movelines:
                debit += line.debit
            for line in credit_movelines:
                credit += line.credit

            partner_credit_limit = (partner.credit_limit + partner.additional_credit_limit - debit) + credit

            confirm_sale_order = self.search([('partner_id', '=', partner.id),
                                              ('state', 'in', ['done', 'draft']),
                                              ('invoice_status', 'in', ['no', 'to invoice'])])
                                              # ('state', 'in', ['done', 'draft'])])
            amount_total = 0
            for sale_order in confirm_sale_order:
                amount_total += sale_order.amount_total

            if partner_credit_limit < amount_total:
                if not partner.over_credit:
                    msg = 'Your available credit limit' \
                          ' Amount = %s \nCheck "%s" Accounts or Credit ' \
                          'Limits.' % (partner_credit_limit,
                                       self.partner_id.name)
                    raise UserError(_('You can not confirm Sale '
                                      'Order. \n' + msg))
            return True
        #
        # partner = self.partner_id
        # user_id = self.env['res.users'].search([
        #     ('partner_id', '=', partner.id)], limit=1)
        # if user_id and not user_id.has_group('base.group_portal') or not \
        #         user_id:
        #     moveline_obj = self.env['account.move.line']
        #     movelines = moveline_obj.search(
        #         [('partner_id', '=', partner.id),
        #          ('move_id.state', '!=', 'cancel'),
        #          # ('parent_state', '=', 'posted'),
        #          ('account_id.user_type_id.name', 'in',
        #           ['Receivable', 'Payable'])]
        #     )
        #     confirm_sale_order = self.search([('partner_id', '=', partner.id),
        #                                       ('state', '=', 'sale')])
        #     debit, credit = 0.0, 0.0
        #     amount_total = self.amount_total
        #     for status in confirm_sale_order:
        #         amount_total += status.amount_total
        #     for line in movelines:
        #         credit += line.credit
        #         debit += line.debit
        #     partner_credit_limit = (partner.credit_limit - debit) + credit
        #     available_credit_limit = \
        #         ((partner_credit_limit -
        #           (amount_total - debit)) + self.amount_total)
        #
        #     if (amount_total - debit) > partner_credit_limit:
        #         if not partner.over_credit:
        #             msg = 'Your available credit limit' \
        #                   ' Amount = %s \nCheck "%s" Accounts or Credit ' \
        #                   'Limits.' % (partner_credit_limit,
        #                                self.partner_id.name)
        #             raise UserError(_('You can not confirm Sale '
        #                               'Order. \n' + msg))
        #         # partner.write(
        #         #     {'credit_limit': credit - debit + self.amount_total})
        #     return True
        # # self.ensure_one()
        # # partner = self.partner_id
        # # user_id = self.env['res.users'].search([
        # #     ('partner_id', '=', partner.id)], limit=1)
        # # if user_id and not user_id.has_group('base.group_portal') or not \
        # #         user_id:
        # #     moveline_obj = self.env['account.move.line']
        # #     movelines = moveline_obj.search(
        # #         [('partner_id', '=', partner.id),
        # #          ('account_id.user_type_id.name', 'in',
        # #           ['Receivable', 'Payable'])]
        # #     )
        # #     confirm_sale_order = self.search([('partner_id', '=', partner.id),
        # #                                       ('state', '=', 'sale')])
        # #     debit, credit = 0.0, 0.0
        # #     amount_total = 0.0
        # #     for status in confirm_sale_order:
        # #         amount_total += status.amount_total
        # #     for line in movelines:
        # #         credit += line.credit
        # #         debit += line.debit
        # #     partner_credit_limit = (partner.credit_limit - debit) + credit
        # #     available_credit_limit = \
        # #         ((partner_credit_limit -
        # #           (amount_total - debit)) + self.amount_total)
        # #
        # #     if (amount_total - debit) > partner_credit_limit:
        # #         if not partner.over_credit:
        # #             msg = 'Your available credit limit' \
        # #                   ' Amount = %s \nCheck "%s" Accounts or Credit ' \
        # #                   'Limits.' % (available_credit_limit,
        # #                                self.partner_id.name)
        # #             raise UserError(_('You can not confirm Sale '
        # #                               'Order. \n' + msg))
        # #         partner.write(
        # #             {'credit_limit': credit - debit + self.amount_total})
        # #     return True


    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            order.check_limit()
        return res

    @api.constrains('amount_total')
    def check_amount(self):
        for order in self:
            order.check_limit()

    def _prepare_invoice(self):
        invoice_vals= super(SaleOrder, self)._prepare_invoice()
        invoice_vals ['amount_total']=self.amount_total
        return invoice_vals
