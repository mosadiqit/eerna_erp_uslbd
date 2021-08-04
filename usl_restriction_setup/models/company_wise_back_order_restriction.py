from datetime import datetime

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare


class BackOrderRestriction(models.Model):
    _name = "back.order.restriction"
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
    # allowed_user_ids=fields.Many2many('res.users','company_wise_allowed_user_rel',"restriction_id","user_id", string="Allowed Users",domain="[('company_id','=',company_id)]")

    @api.onchange('company_id')
    def _get_companies(self):
        final_company_id=[]
        user_default_companies=self.env.user.company_ids.ids
        get_done_company=self.env['back.order.restriction'].search([]).company_id.ids

        for child in get_done_company:
            if child in user_default_companies:user_default_companies.remove(child)
        return {"domain":{"company_id":[('id','in',user_default_companies)]}}



    @api.model
    def create(self, vals_list):
        if vals_list.get("name", _("New")) == _("New"):
            get_company_name=self.env['res.company'].search([('id','=',vals_list['company_id'])]).name
            company=get_company_name.split(" ")[0]
            name= self.env["ir.sequence"].next_by_code("back.order.restriction") or _("New")
            vals_list["name"] = company+'-'+name
            vals_list["status"]=1
        return  super(BackOrderRestriction, self).create(vals_list)


class StockPickingInherit(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        count_flag=0
        loged_user_company_id = self.env.company.id
        company_restriction_chk=self.env['back.order.restriction'].search([('company_id','=',loged_user_company_id)])
        if (self.picking_type_id.sequence_code).upper() == "OUT":
            if company_restriction_chk:
                if company_restriction_chk.is_restricted==True:
                    for move in self.move_ids_without_package:
                        for move_line in move.move_line_ids:
                            move_line.qty_done=move_line.product_uom_qty
                        if move.move_line_ids:
                            product_type=move.move_line_ids[0].product_id.product_tmpl_id.tracking
                        else:
                            product_type='non-serial'
                        product_demand_qty = move.product_qty
                        if (product_type).upper()=="SERIAL":
                            exists_line_qty=len(move.move_line_ids)
                            if product_demand_qty==exists_line_qty:
                                count_flag=1
                            else:
                                raise ValidationError(_("Quantity need to same as sale order quantity, Please fix it (clicking 'Check Availability' button) to proceed!!!."))
                        else:
                            if move.move_line_ids:
                                exists_line_qty=len(move.move_line_ids)
                                done_qty = move.move_line_ids.qty_done
                            else:
                                exists_line_qty=0
                                done_qty = 0

                            if exists_line_qty>0:
                                if product_demand_qty==done_qty:
                                    count_flag=1
                                else:
                                    raise ValidationError(_("Quantity need to same as sale order quantity, Please fix it (clicking 'Check Availability' button) to proceed!!!."))
                            else:
                                raise ValidationError(_("Quantity need to same as sale order quantity, Please fix it (clicking 'Check Availability' button) to proceed!!!."))

                    if count_flag==1:
                        return super(StockPickingInherit, self).button_validate()
                else:
                    return super(StockPickingInherit, self).button_validate()
            else:
                return super(StockPickingInherit, self).button_validate()
        else:
            return super(StockPickingInherit, self).button_validate()





