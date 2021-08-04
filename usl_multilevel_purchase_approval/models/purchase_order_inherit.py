from odoo import api, fields, models


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('initial', 'Draft'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    approval_level_list = list()

    approval_line_ids = fields.One2many('purchase.approval.settings.line','purchase_order',string="Approval Status")

    def button_confirm(self):
        self.state = 'initial'
        self.get_approval_status()


    def submit_for_approval(self):
        self.state = 'waiting_for_approval'
        purchase_approver_group = self.env.ref('usl_multilevel_purchase_approval.group_purchase_approval_settings')
        purchase_approver_list = self.env['purchase.approval.settings'].search([])

        for user in purchase_approver_list.approval_line_ids:
            for rec in user:
                self.approval_level_list.append(user.priority)

        sorted_approval = sorted(self.approval_level_list, reverse=False)

        if sorted_approval:
            for val in sorted_approval:
                query = """select * from purchase_approval_settings_line where priority = {}""".format(val)
                self._cr.execute(query=query)
                result = self._cr.fetchone()
                user_id = self.env['res.users'].search([('id', '=', result[3])])
                unlink_id = self.env['res.users'].search([('id', '!=', user_id.id)])
                purchase_approver_group.write({
                    'users': [(4, user_id.id)]
                })
                for res in unlink_id:
                    purchase_approver_group.write({
                        'users': [(3, res.id)]
                    })
                sorted_approval.remove(val)
                self.approval_level_list = sorted_approval
                approver_status = self.env['purchase.approval.settings.line'].search([('user','=',user_id.id)])
                approver_status.write({'status':'waiting'})
                self._cr.commit()
                break
            return self


    def confirm_approval(self):
        waited_approver = self.env['purchase.approval.settings.line'].search([('status','=','waiting')])
        if waited_approver:
            purchase_approver_group = self.env.ref('usl_multilevel_purchase_approval.group_purchase_approval_settings')
            purchase_approver_list = self.env['purchase.approval.settings'].search([])
            approval_list = list()
            for user in waited_approver:
                # query = """select * from purchase_approval_settings_line where priority = {}""".format(val)
                # self._cr.execute(query=query)
                # result = self._cr.fetchone()
                # user_id = self.env['res.users'].search([('id', '=', result[3])])
                unlink_id = self.env['res.users'].search([('id', '!=', user.id)])
                for usr_id in unlink_id:
                    purchase_approver_group.sudo().write({
                        'users': [(3, usr_id.id)]
                    })
                current_unlink = self.env['res.users'].search([('id', '=', user.user.id)])
                purchase_approver_group.sudo().write({
                    'users': [(3, current_unlink.id)]
                })
                upgrade_status = self.env['purchase.approval.settings.line'].search([('user', '=', user.user.id)])
                upgrade_status.write({'status':'approved'})
                next_approvers = self.env['purchase.approval.settings.line'].search([('priority','>',user.priority)])
                for val in next_approvers:
                    next_approvers_id = self.env['res.users'].search([('id', '=', val.user.id)])
                    purchase_approver_group.sudo().write({
                        'users': [(4, next_approvers_id.id)]
                    })
                    break
                self._cr.commit()
                for user in next_approvers:
                    approval_list.append(user.priority)
                sorted_approval = sorted(approval_list)
                if sorted_approval:
                    for val in sorted_approval:
                        next_approver_status = self.env['purchase.approval.settings.line'].search(
                            [('priority', '=', val)])
                        next_approver_status.write({'status':'waiting'})
                        break
                break
            check_level_approver = self.env['purchase.approval.settings.line'].search([('status','=','waiting')])
            if check_level_approver:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload', }
            else:
                for order in self:
                    order.button_approve()

    def button_approve(self, force=False):
        self.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
        self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
        return {}

    # @api.onchange('state')
    def get_approval_status(self):
        for rec in self:
            lines = []
            for line in self.env['purchase.approval.settings.line'].search([]):
                vals = {
                    'priority': line.priority,
                    'user': line.user.id,
                    'status':line.status
                }
                lines.append((0, 0, vals))
            rec.approval_line_ids = lines