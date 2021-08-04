# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'
    _description = 'Stock Move update'

    # def submit_for_approval(self):
    #     for rec in self:
    #         # print('User', self.env.user)
    #         salesman_default_warehouse = self.env.user.context_default_warehouse_id.name
    #         approved_setting = self.env['sale.approval'].search([])
    #         if approved_setting.approve_sale_order:
    #             rec.state = 'waiting_for_approval'
    #             partner_ids = []
    #             display_message = 'An order is posted on the "waiting for approval" state. Please approve it.'
    #             for approver in approved_setting.sale_order_approver_ids:
    #                 # print('Salesman Default warehouse', salesman_default_warehouse)
    #                 # print('Approver Default warehouse', approver.context_default_warehouse_id.name)
    #                 if approver.context_default_warehouse_id.name == salesman_default_warehouse:
    #                     approver.notify_info(message=display_message)
    #                     partner_ids.append(self.env['res.partner'].search([('name', 'ilike', approver.name)], limit=1).id)
    #
    #             # sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
    #             rec.message_post(body=display_message, subtype='mt_note', partner_ids=partner_ids)
    #         else:
    #             rec.state = 'sale'

    # def approve_sale_order(self):
    #     res = super(StockPickingInherit, self).action_confirm()
    #     sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
    #     for order in self:
    #         display_message = '@{} Your sale order is Approved!'.format(order.user_id.name)
    #         # print(display_message)
    #         partner_ids = self.env['res.partner'].search([('name', 'ilike', order.user_id.name)], limit=1)
    #         # partner_ids = self.env['res.partner'].search(['name', '=', order.user_id.name])
    #         # print(partner_ids)
    #         order.message_post(body=display_message, subtype='mt_note', partner_ids=[(partner_ids.id)])
    #         # order.message_post(body=display_message, subtype='mt_note', moderator_id=order.user_id.id)
    #         # order.message_post(body=display_message, subtype='mt_comment')
    #         order.user_id.notify_success(message='Your sale order is Approved!')
    #     return res

    def approve_stock_move(self):
        pass

    def cancel_sale_order(self):
        return super(StockPickingInherit, self).action_cancel()

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")


# class SaleOrderCancelReason(models.Model):
#     _name = "sale.order.cancel.reason"
#     _description = 'Sale Order Cancel Reason'
#
#     name = fields.Char('Description', required=True, translate=True)
#     active = fields.Boolean('Active', default=True)
