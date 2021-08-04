from odoo import fields, models


class CustomerPayment(models.Model):
    _name = 'customer.payment.approval'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer Payment Approval'

    name = fields.Char(default='Customer Payment Approval Configuration')
    approve_customer_payment = fields.Boolean(string="Approval on customer payment",
                                        help='Enable this field for adding the approvals for the customer payment')
    customer_payment_approver_ids = fields.Many2many('res.users', 'customer_payment_id', string='Customer Payment Approver',
                                               # domain=lambda self: [('groups_id', 'in', self.env.ref('invoice_multi_approval.group_approver').id)],
                                               help='In this field you can add the approvers for the customer payment',
                                               track_visibility='always')

    def apply_configuration(self):
        """Function for applying the approval configuration"""
        # print(self.sale_order_approver_ids)
        res_groups = self.env['res.groups'].search([('name', 'ilike', 'Customer Payment Approver')], limit=1)
        # print(res_groups)
        res_groups.write({'users': self.customer_payment_approver_ids})
        return True
