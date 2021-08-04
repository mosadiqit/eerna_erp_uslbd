from odoo import api, fields, models

class usl_customer_area_map(models.Model):
    _name= "customer.area.map"
    _description = "Area Mapping for customer"

    area = fields.Many2one(
        'customer.area.setup', string='Sales Area', index=True, ondelete='cascade')
    customer_name = fields.Many2one(
        'res.partner', string='Customer', index=True, ondelete='cascade')