from odoo import fields, models


class InventoryApproval(models.Model):
    _name = 'inventory.approval'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'inventory Approval'

    name = fields.Char(default='Inventory Approval Configuration')
    approve_stock_move = fields.Boolean(string="Approval on Stock Move",
                                        help='Enable this field for adding the approvals for the stock move')
    stock_move_approver_ids = fields.Many2many('res.users', 'inventory_approver_id', string='Stock Move Approver',
                                               # domain=lambda self: [('groups_id', 'in', self.env.ref('invoice_multi_approval.group_approver').id)],
                                               help='In this field you can add the approvers for the Stock Move',
                                               track_visibility='always')

    def apply_configuration(self):
        """Function for applying the approval configuration"""
        # print(self.sale_order_approver_ids)
        res_groups = self.env['res.groups'].search([('name', 'ilike', 'Inventory Approver')], limit=1)
        # print(res_groups)
        res_groups.write({'users': self.stock_move_approver_ids})
        return True
