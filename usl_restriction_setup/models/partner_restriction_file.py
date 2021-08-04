from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartnerRestriction(models.Model):
    _inherit = 'res.partner'



    mobile = fields.Char(required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if 'mobile' in values:
                pre_data = self.env['res.partner'].search([('mobile','=',values['mobile'])])
                if len(pre_data) >= 1:
                    raise ValidationError("{} Mobile NUmber Already Exists...".format(values['mobile']))
        res = super(ResPartnerRestriction, self).create(vals_list)
        return res

    def name_get(self):
        res = []
        for partner in self:
            name = "%s" % partner.name
            res += [(partner.id, name)]
        return res

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = args + ['|', ('mobile', operator, name),('name', operator, name)]
        return super(ResPartnerRestriction, self).search(domain, limit=limit).name_get()
