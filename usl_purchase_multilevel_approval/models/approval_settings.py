from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PurchaseApprovalSettings(models.Model):
    _name = 'purchase.approval.settings'
    _description = 'Multiple Purchase Approval Settings'

    name = fields.Char(required=True,string="Name")
    allowed_company = fields.Many2many('res.company','res_company_approval_rel',string="Company")
    approval_line_ids = fields.One2many('purchase.approval.settings.line','purchase_approval_id',string="Approval Settings")

    @api.model_create_multi
    def create(self, vals_list):
        priority_list = list()
        for val in vals_list[0]['approval_line_ids']:
            priority_list.append(val[2]['priority'])
        _size = len(priority_list)
        repeated = []
        for i in range(_size):
            k = i + 1
            for j in range(k, _size):
                if priority_list[i] == priority_list[j] and priority_list[i] not in repeated:
                    repeated.append(priority_list[i])
        if repeated:
            raise ValidationError('Priority level Can\'t be Duplicate. Please Select lower to higher')
        res  = super(PurchaseApprovalSettings, self).create(vals_list)
        return res


class PurchaseApprovalLine(models.Model):
    _name = 'purchase.approval.settings.line'

    purchase_approval_id = fields.Many2one('purchase.approval.settings',string="Approval Id")
    priority = fields.Integer(required=True,string="Level")
    user = fields.Many2one('res.users',string="Responsible Person")
    status = fields.Selection([
        ('approved','Approved'),
        ('waiting','Waiting For Approval'),
        ('not_approved','Not Approved')
    ], default='waiting')
    purchase_order = fields.Many2one('purchase.order')

    # @api.onchange('priority')
    # def onchange_priority(self):
    #     for rec in self:
    #         if rec.priority <= 0:
    #             raise ValidationError('Priotity Can\'t be less or equal to zero')
    #         line_priority = self.env['purchase.approval.settings.line'].search([('purchase_approval_id','!=',None)])
    #         for val in line_priority:
    #             if rec.priority <= val.priority:
    #                 raise ValidationError("This Priority is already set to someone. Please provide higher priority")