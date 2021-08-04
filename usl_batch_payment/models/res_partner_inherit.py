from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    sale_not_allow = fields.Boolean(string="Sales not Allow")