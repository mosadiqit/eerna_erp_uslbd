from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict

class InheritAccountpayment(models.Model):
    _inherit = 'account.payment'
    _description = 'Inherit For State Increase'

    dishonor_count=fields.Integer()
    sent_date=fields.Datetime()
    honor_date=fields.Datetime()
    dishonor_date=fields.Datetime()

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('dishonored', 'Dishonored'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('posted', 'Validated'),


        ('reconciled', 'Reconciled'),
        ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status", tracking=4)
    # state = fields.Selection([('draft', 'Draft'),('sent', 'Sent'),('dishonoured', 'Dishonoured'), ('posted', 'Validated'),  ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")

    def sent(self):
        print(self)

        self.state='sent'
        self.sent_date=date.today()

    def dishonor(self):
        for rec in self:
            rec.dishonor_date=date.today()
            rec.state='dishonored'
            rec.dishonor_count=rec.dishonor_count+1
            get_partner=self.env['res.partner'].browse(self.partner_id.id)
            print(get_partner)
            get_partner.update({
                'active': False
            })

        # self.update({
        #     'active':False
        # })

    def action_open_attachments(self):
        return self
