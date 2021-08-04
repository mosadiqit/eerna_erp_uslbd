from odoo import fields, models


class SaleApproval(models.Model):
    _name = 'sale.approval'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sale Approval'

    name = fields.Char(default='Sale Approval Configuration')
    approve_sale_order = fields.Boolean(string="Approval on Sales Order",
                                        help='Enable this field for adding the approvals for the sales order')
    sale_order_approver_ids = fields.Many2many('res.users', 'sale_order_id', string='Sale Order Approver',
                                               # domain=lambda self: [('groups_id', 'in', self.env.ref('invoice_multi_approval.group_approver').id)],
                                               help='In this field you can add the approvers for the sale order',
                                               track_visibility='always')

    def apply_configuration(self):
        """Function for applying the approval configuration"""
        # print(self.sale_order_approver_ids)
        res_groups = self.env['res.groups'].search([('name', 'ilike', 'Sale Order Approver')], limit=1)
        # print(res_groups)
        res_groups.write({'users': self.sale_order_approver_ids})
        return True
