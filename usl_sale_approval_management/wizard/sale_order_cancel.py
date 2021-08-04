# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrderCancel(models.TransientModel):
    _name = 'sale.order.cancel'
    _description = 'Sale Order Cancel'

    # cancel_reason_id = fields.Many2one('sale.order.cancel.reason', 'Cancel Reason')
    cancel_reason_id = fields.Char('Cancel Reason')

    def action_cancel_reason_apply(self):
        # print(self.cancel_reason_id)
        sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        display_message = 'Your order is canceled! \nCancel reason: ' + str(self.cancel_reason_id)
        sale_order.message_post(body=display_message, subtype='mt_comment')
        # sale_order.message_post(body=display_message, subtype='mt_note')
        # sale_order.message_post(body=display_message, partner_ids=[sale_order.user_id.id], subtype='mail.mt_note')
        sale_order.user_id.notify_danger(message='Your sale order is canceled.')
        # msg2 = self.env['mail.message'].create({
        #     'subject': '_ZTest', 'body': 'A+B', 'subtype_id': self.ref('mail.mt_comment'),
        #     'partner_ids': [(2, 0, [cancel_reason.user_id.id])]})
        # msg = self.env['mail.message'].with_user(sale_order.user_id).create({'message_type': 'comment',
        #                                        'model': 'sale.order',
        #                                        'body': 'Your order is canceled!' + sale_order.user_id,
        #                                        'res_id': sale_order.id,
        #                                        # 'partner_ids': [(8,)],
        #                                        # partner to whom you send notification
        #                                        })
        # msg = self.env['mail.message'].create({'message_type': 'notification',
        #                                        'model': 'sale.order',
        #                                        'body': 'Your order is canceled!',
        #                                        'res_id': sale_order.id,
        #                                        'partner_ids': [sale_order.user_id.id],
        #                                        # partner to whom you send notification
        #                                        })
        # print(msg)
        return sale_order.action_cancel()
