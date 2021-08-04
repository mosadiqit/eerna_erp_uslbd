from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class InheritPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        accounting_existency = self.env['product.sale.accounting'].search(
            [('company_id', '=', self.env.user.company_id.id)])
        if accounting_existency:
            # if self.picking_type_id.code == 'incoming':
            #     if not accounting_existency.stock_input_account:
            #         raise ValidationError(_("Stock input account id is not set for your company!!!"))

            return super(InheritPurchaseOrder, self).action_view_invoice()
        else:
            raise ValidationError(_("Please set accounting for your company!!!"))