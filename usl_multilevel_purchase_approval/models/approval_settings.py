from odoo import api, fields, models


class PurchaseApprovalSettings(models.Model):
    _name = 'purchase.approval.settings'
    # _rec_name = 'name'
    _description = 'Multiple Purchase Approval Settings'

    name = fields.Char(required=True,string="Name")
    allowed_company = fields.Many2many('res.company','res_company_approval_rel',string="Company")
    approval_line_ids = fields.One2many('purchase.approval.settings.line','purchase_approval_id',string="Approval Settings")


class PurchaseApprovalLine(models.Model):
    _name = 'purchase.approval.settings.line'

    purchase_approval_id = fields.Many2one('purchase.approval.settings',string="Approval Id")
    priority = fields.Integer(required=True,string="Level")
    user = fields.Many2one('res.users',string="Responsible Person")
    status = fields.Selection([
        ('approved','Approved'),
        ('waiting','waiting'),
        ('not_approved','Not Approved')
    ])
    purchase_order = fields.Many2one('purchase.order')