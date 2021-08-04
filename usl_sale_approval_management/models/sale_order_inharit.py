# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    _description = 'sale order state update'

    def submit_for_approval(self):
        for rec in self:
            # print('User', self.env.user)
            salesman_default_warehouse = self.env.user.context_default_warehouse_id.id
            # approved_setting = self.env['sale.approval'].search([])
            default_company = self.env.user.company_id
            approved_setting = self.env['order.approve'].search(
                [('is_active', '=', True), ('order_approve_company', '=', default_company.id)])

            print(default_company)
            print(approved_setting)
            if approved_setting:
                print('come to recived')
                rec.state = 'waiting_for_approval'
                partner_ids = []
                display_message = 'An order is posted on the "waiting for approval" state. Please approve it.'
                for approver in approved_setting.order_approve_user:
                    # print('Salesman Default warehouse', salesman_default_warehouse)
                    # print('Approver Default warehouse', approver.context_default_warehouse_id.name)
                    if approver.context_default_warehouse_id.id == salesman_default_warehouse:
                        approver.notify_info(message=display_message)
                        partner_ids.append(self.env['res.partner'].search([('name', 'ilike', approver.id)], limit=1).id)

                # sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
                rec.message_post(body=display_message, subtype='mt_note', partner_ids=partner_ids)
            else:
                super(SaleOrderInherit, self).action_confirm()

    # def submit_for_approval(self):
    #     for rec in self:

    def approve_sale_order(self):
        if self.state != 'waiting_for_approval':
            raise ValidationError('already Approved or Cancel')
        else:
            res = super(SaleOrderInherit, self).action_confirm()
            sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
            for order in self:
                display_message = '@{} Your sale order is Approved!'.format(order.user_id.name)
                # print(display_message)
                partner_ids = self.env['res.partner'].search([('name', 'ilike', order.user_id.name)], limit=1)
                # partner_ids = self.env['res.partner'].search(['name', '=', order.user_id.name])
                # print(partner_ids)
                order.message_post(body=display_message, subtype='mt_note', partner_ids=[(partner_ids.id)])
                # order.message_post(body=display_message, subtype='mt_note', moderator_id=order.user_id.id)
                # order.message_post(body=display_message, subtype='mt_comment')
                order.user_id.notify_success(message='Your sale order is Approved!')
            return res

    def cancel_sale_order(self):
        return super(SaleOrderInherit, self).action_cancel()

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')


class SaleOrderCancelReason(models.Model):
    _name = "sale.order.cancel.reason"
    _description = 'Sale Order Cancel Reason'

    name = fields.Char('Description', required=True, translate=True)
    active = fields.Boolean('Active', default=True)
