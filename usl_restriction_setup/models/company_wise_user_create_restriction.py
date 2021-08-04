from datetime import datetime

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare


class UserCreateRestriction(models.Model):
    _name = "user.create.restriction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Company wise user create Restriction"

    name = fields.Char(
        string="Name",
        readonly=True,
        index=True,
        copy=False,
        default=lambda self: _("New"),
    )
    status = fields.Integer()
    company_id=fields.Many2one('res.company', string="Company")
    is_restricted=fields.Boolean(string="Is Restricted", default=True)
    allowed_user_ids=fields.Many2many('res.users','company_wise_allowed_user_rel',"restriction_id","user_id", string="Allowed Users",domain="[('company_id','=',company_id)]")

    @api.onchange('company_id')
    def _get_companies(self):
        final_company_id=[]
        user_default_companies=self.env.user.company_ids.ids
        get_done_company=self.env['user.create.restriction'].search([]).company_id.ids

        for child in get_done_company:
            if child in user_default_companies:user_default_companies.remove(child)
            # for parent in user_default_companies:
            #     if child==parent:
        return {"domain":{"company_id":[('id','in',user_default_companies)]}}



    @api.model
    def create(self, vals_list):
        if vals_list.get("name", _("New")) == _("New"):
            get_company_name=self.env['res.company'].search([('id','=',vals_list['company_id'])]).name
            company=get_company_name.split(" ")[0]
            name= self.env["ir.sequence"].next_by_code("user.create.restriction") or _("New")
            vals_list["name"] = company+'-'+name
            vals_list["status"] = 1
        return  super(UserCreateRestriction, self).create(vals_list)

# class ResUserInherit(models.Model):
#     _inherit = "res.users"
#
#     @api.model
#     def create(self,vals):
#         super_admin_user=self.env.ref('base.group_system').users.ids
#         loged_user_id=self.env.user.id
#         loged_user_company_id=self.env.company.id
#         check_company_is_restricted=self.env['user.create.restriction'].search([('company_id','=',loged_user_company_id)])
#         if check_company_is_restricted:
#             if check_company_is_restricted.is_restricted==True:
#                 query="""select * from company_wise_allowed_user_rel where user_id={} and restriction_id={}""".format(loged_user_id,check_company_is_restricted.id)
#                 self._cr.execute(query=query)
#                 get_user_have_access_or_not=self._cr.fetchone()
#                 # get_user_have_access_or_not=self.env['company.wise.allowed.user.rel'].search([('user_id','=',loged_user_id),('restriction_id','=',check_company_is_restricted.id)])
#                 if get_user_have_access_or_not:
#                     return super(ResUserInherit, self).create(vals)
#                 else:
#                     if loged_user_id in super_admin_user:
#                         return super(ResUserInherit, self).create(vals)
#                     else:
#                         raise ValidationError(_("You have no permission to create user!!!."))
#             else:
#                 return super(ResUserInherit, self).create(vals)
#         else:
#             return super(ResUserInherit, self).create(vals)
#         # print("Inherit successful")

class ResUserInherit(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self,vals):
        super_admin_user=self.env.ref('base.group_system').users.ids
        loged_user_id=self.env.user.id
        loged_user_company_id=self.env.company.id
        check_company_is_restricted=self.env['user.create.restriction'].search([('company_id','=',loged_user_company_id)])
        if check_company_is_restricted:
            if check_company_is_restricted.is_restricted==True:
                query="""select * from company_wise_allowed_user_rel where user_id={} and restriction_id={}""".format(loged_user_id,check_company_is_restricted.id)
                self._cr.execute(query=query)
                get_user_have_access_or_not=self._cr.fetchone()
                # get_user_have_access_or_not=self.env['company.wise.allowed.user.rel'].search([('user_id','=',loged_user_id),('restriction_id','=',check_company_is_restricted.id)])
                if get_user_have_access_or_not:
                    return super(ResUserInherit, self).create(vals)
                else:
                    if loged_user_id in super_admin_user:
                        return super(ResUserInherit, self).create(vals)
                    else:
                        raise ValidationError(_("You have no permission to create user!!!."))
            else:
                return super(ResUserInherit, self).create(vals)
        else:
            return super(ResUserInherit, self).create(vals)
        # print("Inherit successful")


