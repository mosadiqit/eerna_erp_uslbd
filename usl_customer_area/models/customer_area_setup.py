from odoo import api, fields, models


class usl_customer_area(models.Model):
    _name= "customer.area.setup"
    _description = "create customer area like teritory concept"
    _check_company_auto = True
    _rec_name = 'area_name'

    area_name = fields.Char(string='Customer Area Name',required=True)
    is_active = fields.Selection([('1', 'Active'), ('2', 'Inactive')], default='1')
    parent_area = fields.Many2one(
        'customer.area.setup', string='Parent Area', index=True, ondelete='cascade')





