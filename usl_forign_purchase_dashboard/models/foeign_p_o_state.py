from odoo import api, fields, models, _


class ForeignPOState(models.Model):
    _name = 'foreign.purchase.state'
    _description = 'ForeignPOState'

    state_name = fields.Char(string='State Name')
    product_count = fields.Integer(string='Product Count.')
    color = fields.Integer(string='Color Index', help="The color of the channel")
    dashboard_button_name = fields.Char(string="Dashboard Button", compute='_compute_dashboard_button_name')
    fpo_count = fields.Integer(
        compute='_compute_fpo_count',
        string='Number of quotations to invoice', readonly=True)

    fpo_product_count = fields.Integer(
        compute='_compute_fpo_product_count',
        string='Amount of quotations to invoice', readonly=True)

    # fpo_product_amount = fields.Integer(
    #     compute='_compute_sales_to_invoice',
    #     string='Number of sales to invoice', readonly=True)

    def action_primary_channel_button(self):
        return

    def _compute_dashboard_button_name(self):
        """ Sets the adequate dashboard button name depending on the Sales Team's options
        """
        for team in self:
            team.dashboard_button_name = _("Big Pretty Button :)")  # placeholder

    def _compute_fpo_count(self):
        for rec in self:
            domain = [('state', '=', rec.state_name)]
            count = self.env['foreign.purchase.order'].sudo().search_count(domain)
            rec.fpo_count = count

    def _compute_fpo_product_count(self):
        for rec in self:
            domain = [('state', '=', rec.state_name)]
            fpos = self.env['foreign.purchase.order'].sudo().search(domain)
            product_count = 0
            for fpo in fpos:
                product_count += len(fpo.line_ids)
            rec.fpo_product_count = product_count

    def action_foreign_purchase_order(self):
        action_name = 'usl_forign_purchase_dashboard.action_foreign_po_order_kanban'
        for rec in self:
            print('state name : ', rec.state_name)
            domain = [('state', '=', rec.state_name)]
            fpos = self.env['foreign.purchase.order'].sudo().search(domain)
            fpo_id = list()
            for fpo in fpos:
                fpo_id.append(fpo.id)
            action = self.env.ref(action_name).read()[0]
            action['domain'] = [('id', 'in', fpo_id)]
            return action

    def action_f_p_o_product(self):
        action_name = 'usl_forign_purchase_dashboard.forigin_purches_order_kanban_action'
        for rec in self:
            print('state name : ', rec.state_name)
            domain = [('state', '=', rec.state_name)]
            fpos = self.env['foreign.purchase.order'].sudo().search(domain)
            fpo_id = list()
            for fpo in fpos:
                fpo_id.append(fpo.id)
            action = self.env.ref(action_name).read()[0]
            action['domain'] = [('order_id', 'in', fpo_id)]
            return action
