from odoo import fields, models


class AdditionalCreditLimit(models.Model):
    _name = 'additional.credit.limit'

    from_date=fields.Date(string="From")
    to_date=fields.Date(string="To")
    ammount=fields.Float(string="Ammount")
    partner_id = fields.Many2one('res.partner', string='Partner Reference')
    is_deducted=fields.Boolean(default=False)
    is_sheduled_update=fields.Boolean(default=False)