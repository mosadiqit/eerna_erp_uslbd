from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    _description = 'Account move state update'

    is_draft_invoice = fields.Boolean(string="Is draft Invoice", default=False)

    # def button_draft(self):
    #     print("invoice Draft")
    #     self.is_draft_invoice = False
    #     res = super(AccountMoveInherit, self).button_draft()
    #     return res

    @api.model
    def create(self, vals_list):
        # if vals_list['ref'] != False:
        #     if 'POS' in vals_list['ref']:
        #         return super(AccountMoveInherit, self).create(vals_list)
        #     else:
        sale_journal = self.env['account.journal'].search(
            [('company_id', '=', self.env.company.id), ('id', '=', vals_list['journal_id']),
             ('type', '=', 'sale')])
        if sale_journal:
            user_id = self.env['res.users'].search([
                ('partner_id', '=', vals_list['partner_id'])], limit=1)
            partner = self.env['res.partner'].browse(vals_list['partner_id'])

            if user_id and not user_id.has_group('base.group_portal') or not \
                    user_id:
                if 'is_draft_invoice' not in vals_list.keys():
                    vals_list["is_draft_invoice"] = True
                else:
                    vals_list["is_draft_invoice"] = True
                    # vals_list.add("is_draft_invoice", True)

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
                sale_amount = 0
                if 'line_ids' in vals_list.keys():
                    for line in vals_list['line_ids']:
                        sale_amount += line[2]['debit']
                else:
                    sale_amount += vals_list['amount_total']

                partner_credit_limit = (partner.credit_limit + partner.additional_credit_limit - debit) + credit
                if sale_amount > partner_credit_limit:
                    if not partner.over_credit:
                        msg = 'Your available credit limit' \
                              ' Amount = %s \nCheck "%s" Accounts or Credit ' \
                              'Limits.' % (partner_credit_limit,
                                           partner.name)
                        raise UserError(_('You can not confirm Sale '
                                          'Order. \n' + msg))
                        return False
                    else:
                        return super(AccountMoveInherit, self).create(vals_list)
                else:
                    return super(AccountMoveInherit, self).create(vals_list)
            else:
                return super(AccountMoveInherit, self).create(vals_list)
        else:
            return super(AccountMoveInherit, self).create(vals_list)


        # else:
        #     sale_journal = self.env['account.journal'].search([('company_id', '=', self.env.company.id), ('id', '=', vals_list['journal_id']), ('type', '=', 'sale')])
        #     if sale_journal:
        #         user_id = self.env['res.users'].search([
        #             ('partner_id', '=', vals_list['partner_id'])], limit=1)
        #         partner = self.env['res.partner'].browse(vals_list['partner_id'])
        #
        #         if user_id and not user_id.has_group('base.group_portal') or not \
        #                 user_id:
        #             if 'is_draft_invoice' not in vals_list.keys():
        #                 vals_list["is_draft_invoice"] = True
        #             else:
        #                 vals_list["is_draft_invoice"] = True
        #                 # vals_list.add("is_draft_invoice", True)
        #
        #             debit_movelines = self.env['account.move.line'].search(
        #                 [('partner_id', '=', partner.id),
        #                  ('move_id.state', '!=', 'cancel'),
        #                  ('account_id.user_type_id.name', 'in',
        #                   ['Receivable', 'Payable'])]
        #             )
        #             credit_movelines = self.env['account.move.line'].search(
        #                 [('partner_id', '=', partner.id),
        #                  ('move_id.state', '=', 'posted'),
        #                  ('account_id.user_type_id.name', 'in',
        #                   ['Receivable', 'Payable'])]
        #             )
        #             debit, credit = 0.0, 0.0
        #             for line in debit_movelines:
        #                 debit += line.debit
        #             for line in credit_movelines:
        #                 credit += line.credit
        #             sale_amount = 0
        #             if 'line_ids' in vals_list.keys():
        #                 for line in vals_list['line_ids']:
        #                     sale_amount += line[2]['debit']
        #             else:
        #                 sale_amount += vals_list['amount_total']
        #
        #             partner_credit_limit = (partner.credit_limit + partner.additional_credit_limit - debit) + credit
        #             if sale_amount > partner_credit_limit:
        #                 if not partner.over_credit:
        #                     msg = 'Your available credit limit' \
        #                           ' Amount = %s \nCheck "%s" Accounts or Credit ' \
        #                           'Limits.' % (partner_credit_limit,
        #                                        partner.name)
        #                     raise UserError(_('You can not confirm Sale '
        #                                       'Order. \n' + msg))
        #                     return False
        #                 else:
        #                     return super(AccountMoveInherit, self).create(vals_list)
        #             else:
        #                 return super(AccountMoveInherit, self).create(vals_list)
        #         else:
        #             return super(AccountMoveInherit, self).create(vals_list)
        #     else:
        #         return super(AccountMoveInherit, self).create(vals_list)


# from odoo import models, fields, api, _
# from odoo.exceptions import ValidationError, UserError
#
#
# class AccountMoveInherit(models.Model):
#     _inherit = 'account.move'
#     _description = 'Account move state update'
#
#     def check_credit_limit(self, partner, sale_amount_total):
#         # partner = self.partner_id
#         user_id = self.env['res.users'].search([
#             ('partner_id', '=', partner.id)], limit=1)
#         if user_id and not user_id.has_group('base.group_portal') or not \
#                 user_id:
#
#             debit_movelines = self.env['account.move.line'].search(
#                 [('partner_id', '=', partner.id),
#                  ('move_id.state', '!=', 'cancel'),
#                  ('account_id.user_type_id.name', 'in',
#                   ['Receivable', 'Payable'])]
#             )
#             credit_movelines = self.env['account.move.line'].search(
#                 [('partner_id', '=', partner.id),
#                  ('move_id.state', '=', 'posted'),
#                  ('account_id.user_type_id.name', 'in',
#                   ['Receivable', 'Payable'])]
#             )
#             debit, credit = 0.0, 0.0
#             for line in debit_movelines:
#                 debit += line.debit
#             for line in credit_movelines:
#                 credit += line.credit
#
#             partner_credit_limit = (partner.credit_limit + partner.additional_credit_limit - debit) + credit
#             if 0 > partner_credit_limit:
#                 if not partner.over_credit:
#                     msg = 'Your available credit limit' \
#                           ' Amount = %s \nCheck "%s" Accounts or Credit ' \
#                           'Limits.' % (sale_amount_total + partner_credit_limit,
#                                        partner.name)
#                     raise UserError(_('You can not confirm Sale '
#                                       'Order. \n' + msg))
#                     return False
#                 # partner.write(
#                 #     {'credit_limit': credit - debit + self.amount_total})
#             return True
#
#     def submit_for_approval(self):
#         for rec in self:
#             # for p in rec.invoice_line_ids:
#                 # print(p.bank_payment)
#             # print('User', self.env.user)
#             if rec.type == 'out_invoice':
#                 limit_status = self.check_credit_limit(rec.partner_id, rec.amount_total)
#                 if not limit_status:
#                     return False
#             salesman_default_warehouse = self.env.user.context_default_warehouse_id.id
#             approved_setting = self.env['sale.approval'].search([])
#             if approved_setting.approve_sale_order:
#                 rec.state = 'waiting_for_approval'
#                 partner_ids = []
#                 display_message = 'An invoice is posted on the "waiting for approval" state. Please approve it.'
#                 for approver in approved_setting.sale_order_approver_ids:
#                     # print('Salesman Default warehouse', salesman_default_warehouse)
#                     # print('Approver Default warehouse', approver.context_default_warehouse_id.name)
#                     if approver.context_default_warehouse_id.id == salesman_default_warehouse:
#                         approver.notify_info(message=display_message)
#                         partner_ids.append(
#                             self.env['res.partner'].search([('name', 'ilike', approver.name)], limit=1).id)
#
#                 # sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
#                 rec.message_post(body=display_message, subtype='mt_note', partner_ids=partner_ids)
#             else:
#                 rec.state = 'posted'
