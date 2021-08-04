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
        approval_configuration = self.env['purchase.approval.settings'].search([])
        if approval_configuration:
            self.state = 'initial'
        else:
            for order in self:
                if order.state not in ['draft', 'sent']:
                    continue
                order._add_supplier_to_product()
                # Deal with double validation process
                if order.company_id.po_double_validation == 'one_step' \
                        or (order.company_id.po_double_validation == 'two_step' \
                            and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                            order.date_order or fields.Date.today())) \
                        or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_approve()
                else:
                    order.write({'state': 'to approve'})
            return True

    def submit_for_approval(self):
        self.state = 'waiting_for_approval'

        configured_id = self.env['purchase.approval.settings.line'].search([('purchase_approval_id','!=',None)])
        for rec in configured_id:
            rec.write({'status':'waiting'})

        purchase_approver_group = self.env.ref('usl_purchase_multilevel_approval.group_purchase_approval_settings')
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
                approver_status = self.env['purchase.approval.settings.line'].search([('user','=',user_id.id),('purchase_approval_id','!=',None)])
                approver_status.write({'status':'waiting'})
                self._cr.commit()
                break
            self.get_approval_status()
            return self

    def confirm_approval(self):
        waited_approver = self.env['purchase.approval.settings.line'].search([('status','=','waiting'),('purchase_approval_id','!=',None)])
        if waited_approver:
            purchase_approver_group = self.env.ref('usl_purchase_multilevel_approval.group_purchase_approval_settings')
            purchase_approver_list = self.env['purchase.approval.settings'].search([])
            approval_list = list()
            for user in waited_approver:
                unlink_id = self.env['res.users'].search([('id', '!=', user.id)])
                for usr_id in unlink_id:
                    purchase_approver_group.sudo().write({
                        'users': [(3, usr_id.id)]
                    })
                current_unlink = self.env['res.users'].search([('id', '=', user.user.id)])
                purchase_approver_group.sudo().write({
                    'users': [(3, current_unlink.id)]
                })
                upgrade_status = self.env['purchase.approval.settings.line'].search([('user', '=', user.user.id),('purchase_approval_id','!=',None)])
                upgrade_status.write({'status':'approved'})
                next_approvers = self.env['purchase.approval.settings.line'].search([('priority','>',user.priority),('purchase_approval_id','!=',None)])
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
                            [('priority', '=', val),('purchase_approval_id','!=',None)])
                        next_approver_status.write({'status':'waiting'})
                        break
                self.get_approval_status()
                break
            check_level_approver = self.env['purchase.approval.settings.line'].search([('status','=','waiting'),('purchase_approval_id','!=',None)])
            if check_level_approver:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload', }
            else:
                self.get_approval_status()
                for order in self:
                    order.button_approve()

    def button_approve(self, force=False):
        self.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
        self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
        return {}

    def get_approval_status(self):
        for rec in self:
            rec.approval_line_ids = None
            lines = []
            for line in self.env['purchase.approval.settings.line'].search([('purchase_approval_id','!=',None)]):
                vals = {
                    'priority': line.priority,
                    'user': line.user.id,
                    'status':line.status
                }
                lines.append((0, 0, vals))
            rec.approval_line_ids = lines

    def reject_order(self):
        self.state = 'cancel'
        for rec in self:
            for val in self.approval_line_ids:
                if val.user.id == rec.write_uid.id:
                    val.status = 'not_approved'
        return {
            'type': 'ir.actions.client',
            'tag': 'reload', }