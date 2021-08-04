
from odoo import fields, models


class VATDeductionServices(models.Model):
    _name = "vat.deduction.services"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, string="Service Name")
    service_code = fields.Char(required=True, string="Service Code")
    net_vat_rate = fields.Float(string="Net VAT Rate")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        index=True,
        default=lambda self: self.env.company.id)