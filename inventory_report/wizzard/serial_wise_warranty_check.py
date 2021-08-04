from odoo import api, fields, models
from odoo.exceptions import ValidationError

class NewModule(models.TransientModel):
    _name = 'serial.warranty.check'
    # _rec_name = 'name'
    _description = 'New Description'

    serial_no = fields.Char(string='Enter Your Serial Number')

    def get_report(self):
        query = """select am.id from stock_move_line sml 
                    left join stock_production_lot spl on spl.id = sml.lot_id 
	                left join stock_move sm on sm.id = sml.move_id 
	                left join account_move am on am.invoice_origin = sm.origin 
	                where spl.name = '{}' and sml.reference like '%OUT%'""".format(self.serial_no)
        self._cr.execute(query=query)
        result = self._cr.fetchone()
        if result is not None:
            account_move = self.env['account.move'].search([('id','=',result[0])])
            if account_move:
                return self.env.ref('account.account_invoices').report_action(account_move)
            else:
                raise ValidationError('Invalid Serial Number!')
        else:
            raise ValidationError('Invalid Serial Number!')