from datetime import datetime

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare


class ForeignPurchaseOrder(models.Model):
    _name = "purchase.wise.lc.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]


    po_id=fields.Integer()
    po_line_id=fields.Integer()
    lc_id=fields.Integer()
    taking_amount_from_lc=fields.Float()
    # existing_remaining_bank_payment=fields.Float()