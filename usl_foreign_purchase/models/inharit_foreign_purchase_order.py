from odoo import api, fields, models


class ForeignPurchaseOrder(models.Model):
    _inherit = "foreign.purchase.order"

    def action_f_p_o_product(self):
        action_name = 'usl_foreign_purchase_smart.forigin_purches_order_kanban_action'
        for rec in self:
            action = self.env.ref(action_name).read()[0]
            action['domain'] = [('order_id', '=', rec.id)]
            return action
