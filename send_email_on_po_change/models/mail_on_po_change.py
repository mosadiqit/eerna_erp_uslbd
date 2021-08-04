from odoo import _, api, fields, models, tools


class MailOnUpdate(models.Model):
    _inherit='purchase.order'
    _description = ''
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Vendor', required=True,change_default=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    partner_ref = fields.Char('Vendor Reference', copy=False,track_visibility='onchange',
                              help="Reference of the sales order or bid sent by the vendor. "
                                   "It's used to do the matching when you receive the "
                                   "products as this reference is usually written on the "
                                   "delivery order sent by your vendor.")

    def send_user_mail(self):
        self.env.ref('send_email_on_po_change.send_mail_on_change').send_mail(self.id, force_send=True)

    def write(self, vals):
        res = super(MailOnUpdate, self).write(vals)
        if vals.get('date_planned'):
            self.order_line.filtered(lambda line: not line.display_type).date_planned = vals['date_planned']
        if ('partner_ref' or 'date_order') in vals.keys():
            self.send_user_mail()

        return res


