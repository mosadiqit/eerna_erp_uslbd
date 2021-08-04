from odoo import models, fields
from odoo.tools import float_is_zero, float_compare
class port(models.Model):
    _name="usl.port"

    name=fields.Char()
    address=fields.Char()