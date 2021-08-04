from odoo import fields, models, api


class AllBank(models.Model):
    _name = "bank_info.all_bank"
    _description = 'all the bank\'s detail in Bangladesh'
    _rec_name = 'bank_name'

    bank_name = fields.Char(string="Bank Name")
    address = fields.Char(string="Bank Address")
