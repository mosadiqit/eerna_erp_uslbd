from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re

class OtherExpAccMap (models.Model):
    _name = "saleotherexpense"
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Sales Other Expense Accounting Map"
    _check_company_auto = True


    # business_promotion=fields.Char(string="Business Promotion")
    # security_money=fields.Char(string="Security Money")

    bp_account_id = fields.Many2one(
        'account.account', string='BP Payable Account',required=True)


    bp_exp_account_id = fields.Many2one(
        'account.account', string='BP Expense Account',required=True)

    security_money_account_id = fields.Many2one(
        'account.account', string='Security Money Account',required=True)

    tax_received_account_id = fields.Many2one(
        'account.account', string='Tax Received Account',required=True)

    vat_payable_account_id = fields.Many2one(
        'account.account', string='VAT Payable Account',required=True)

    cheque_in_hand_account_id = fields.Many2one(
        'account.account', string='Cheque In Hand Account', required=True)

    company_id = fields.Many2one('res.company', string="Company", required=True, index=True,
                                 default=lambda self: self.env.company)