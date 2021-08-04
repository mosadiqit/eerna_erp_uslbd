
from odoo import fields, models


class ValueAddedItem(models.Model):
    _name = "value.added.item"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, string="Item Name")
    item_code = fields.Char(required=True, string="Item Code")
    sequence = fields.Integer(string="Sequence")
    percent = fields.Float(string="Value Added %")
    status = fields.Selection([('1', 'Active'), ('2', 'InActive')], string="Status", default='1')
    value_type = fields.Selection([('1', 'Direct'), ('2', 'InDirect'), ('3', 'Trading')], string="Value Type", default='1')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        index=True,
        default=lambda self: self.env.company.id)