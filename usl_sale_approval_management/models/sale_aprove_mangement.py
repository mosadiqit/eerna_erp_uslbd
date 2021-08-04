from odoo import fields, models, api


class SaleApproveManagement(models.Model):
    _name = 'sale.approve.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sale approve management'

    name = fields.Char(string="sale", default="Sale Approve Management")
    order_approve_ids = fields.One2many('order.approve', 'sale_order_management', string='Order Approve')
    invoice_approve_ids = fields.One2many('invoice.approve', 'sale_invoice_management', string='Invoice Approve')

    def apply_configuration(self):
        """Function for applying the approval configuration"""

    def write(self, vals):
        res = super(SaleApproveManagement, self).write(vals)
        res_groups = self.env['res.groups'].search([('name', 'ilike', 'Sale Order Approver')], limit=1)
        # print(res_groups)
        res_groups.write({'users': self.invoice_approve_ids.invoice_approve_user})
        # print(self.order_approve_ids.order_approve_user)
        # print(self.order_approve_ids.is_active)
        res_groups_order = self.env['res.groups'].search([('name', 'ilike', 'Order Approver')], limit=1)
        # print(res_groups)
        res_groups_order.write({'users': self.order_approve_ids.order_approve_user})
        return res


class OrderApprove(models.Model):
    _name = 'order.approve'
    _description = 'OrderApprove'

    order_approve_company = fields.Many2one('res.company', string='Company')
    order_approve_user = fields.Many2many('res.users', 'user_order_approve_rel', string='User',
                                          domain="[('company_id', '=', order_approve_company)]")
    is_active = fields.Boolean(string="Active")
    sale_order_management = fields.Many2one('sale.approve.management', string='Sale approve')




class InvoiceApprove(models.Model):
    _name = 'invoice.approve'
    _description = 'InvoiceApprove'

    invoice_approve_company = fields.Many2one('res.company', string='Company')
    invoice_approve_user = fields.Many2many('res.users', 'user_invoice_approve_rel', string='User',
                                            domain="[('company_id', '=', invoice_approve_company)]")
    is_active = fields.Boolean(string="Active")
    sale_invoice_management = fields.Many2one('sale.approve.management', string='Sale approve')
