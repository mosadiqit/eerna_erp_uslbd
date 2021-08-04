from odoo import api, fields, models
from odoo.exceptions import ValidationError

class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    # delivery order delete not allowed for users.
    def unlink(self):
        if self.user_has_groups('base.group_user'):
            raise ValidationError('You can not delete the sale order item from here')
