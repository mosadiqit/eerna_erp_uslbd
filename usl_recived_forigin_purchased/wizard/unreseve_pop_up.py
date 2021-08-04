from odoo import fields, models, api


class ModelName(models.TransientModel):
    _name = 'transfer.unreserved.popup'
    _description = 'Description'

    name = fields.Char(string='',
                       default='This serial number is already reserved by someone , do you want to unreserved ?',
                       readonly=True)

    def action_confirm(self):
        print('confirm')
