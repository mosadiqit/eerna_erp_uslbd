# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    _description = 'Account move state update'

    def submit_for_approval(self):
        for rec in self:
            # for p in rec.invoice_line_ids:
            # print(p.bank_payment)
            # print('User', self.env.user)
            salesman_default_warehouse = self.env.user.context_default_warehouse_id.id
            # approved_setting = self.env['sale.approval'].search([])
            # if approved_setting.approve_sale_order:
            default_company = self.env.user.company_id
            approved_setting = self.env['invoice.approve'].search(
                [('is_active', '=', True), ('invoice_approve_company', '=', default_company.id)], limit=1)

            print(default_company)
            print(approved_setting)
            if approved_setting:
                rec.state = 'waiting_for_approval'
                partner_ids = []
                display_message = 'An invoice is posted on the "waiting for approval" state. Please approve it.'
                for approver in approved_setting.invoice_approve_user:
                    # print('Salesman Default warehouse', salesman_default_warehouse)
                    # print('Approver Default warehouse', approver.context_default_warehouse_id.name)
                    if approver.context_default_warehouse_id.id == salesman_default_warehouse:
                        approver.notify_info(message=display_message)
                        partner_ids.append(
                            self.env['res.partner'].search([('name', 'ilike', approver.name)], limit=1).id)

                # sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
                rec.message_post(body=display_message, subtype='mt_note', partner_ids=partner_ids)
            else:
                rec.state = 'posted'

    def approve_invoice_order(self):
        print(self)

        if self.state == 'posted' or self.state == 'cancel':
            raise ValidationError('already Approved or Cancel')
        else:

            res = super(AccountMoveInherit, self).action_post()
            self.env['account.move'].browse(self.env.context.get('active_ids'))
            invoice = self.env['account.move'].search([('id', '=', self.id)])
            for order in self:
                order.state = 'posted'
                display_message = '@{} Your sale order is Approved!'.format(order.user_id.name)
                # print(display_message)
                partner_ids = self.env['res.partner'].search([('name', 'ilike', order.user_id.name)], limit=1)
                # partner_ids = self.env['res.partner'].search(['name', '=', order.user_id.name])
                # print(partner_ids)
                order.message_post(body=display_message, subtype='mt_note', partner_ids=[(partner_ids.id)])
                # order.message_post(body=display_message, subtype='mt_note', moderator_id=order.user_id.id)
                # order.message_post(body=display_message, subtype='mt_comment')
                order.user_id.notify_success(message='Your invoice is Approved!')

                # if invoice.state == 'posted':
                #     raise ValueError('alrady posted')
                # else:
                #     order.state = 'posted'
                #     display_message = '@{} Your sale order is Approved!'.format(order.user_id.name)
                #     # print(display_message)
                #     partner_ids = self.env['res.partner'].search([('name', 'ilike', order.user_id.name)], limit=1)
                #     # partner_ids = self.env['res.partner'].search(['name', '=', order.user_id.name])
                #     # print(partner_ids)
                #     order.message_post(body=display_message, subtype='mt_note', partner_ids=[(partner_ids.id)])
                #     # order.message_post(body=display_message, subtype='mt_note', moderator_id=order.user_id.id)
                #     # order.message_post(body=display_message, subtype='mt_comment')
                #     order.user_id.notify_success(message='Your invoice is Approved!')
            return res

    def cancel_invoice_order(self):
        if self.state == 'posted' or self.state == 'cancel':
            raise ValidationError('already Approved or Cancel')
        else:
            return super(AccountMoveInherit, self).button_cancel()

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
