from odoo import fields, models, api


class ModelName(models.Model):
    _inherit = 'sale.approval'
    _description = 'Description'

    oder_approval = fields.Boolean(string='Order Approval')
    order_approval_company = fields.Many2one('res.company', string='select company for order approval')
    order_approver_ids = fields.Many2many('res.users', 'order_ids', string='Order Approver',
                                          domain="[('company_id', '=', order_approval_company)]",
                                          help='In this field you can add the approvers for the sale order',
                                          track_visibility='always')
    invoice_approval_company = fields.Many2one('res.company', string='select company for invoice approval')

    @api.onchange('invoice_approval_company')
    def invoice_approval_user_selection(self):
        if not self.invoice_approval_company:
            print('come in gourd close')
            return {
                'domain': {
                    'sale_order_approver_ids': []
                },
            }
        print('come others')
        return {
            'domain': {
                'sale_order_approver_ids': [('company_id', '=', self.invoice_approval_company.id)]
            },
        }

    def apply_configuration(self):
        """Function for applying the approval configuration"""
        # print(self.sale_order_approver_ids)
        res_groups = self.env['res.groups'].search([('name', 'ilike', 'Sale Order Approver')], limit=1)
        # print(res_groups)
        res_groups.write({'users': self.sale_order_approver_ids})
        res_groups_order = self.env['res.groups'].search([('name', 'ilike', 'Order Approver')], limit=1)
        # print(res_groups)
        res_groups_order.write({'users': self.order_approver_ids})

        return True
