from odoo import api, fields, models, _


class ChequeModel(models.Model):
    _name = 'cheque.model'
    _description = 'Cheque Model State'
    # models of check management
    #check
    state_name = fields.Char(string='State Name')
    # product_count = fields.Integer(string='Product Count.')
    # dashboard_button_name = fields.Char(string="Dashboard Button", compute='_compute_dashboard_button_name')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    color = fields.Integer(string='Color Index', help="The color of the channel")
    # dashboard_button_name = fields.Char(string="Dashboard Button", compute='_compute_dashboard_button_name')

    state_count = fields.Integer(
        compute='_compute_state_count',
        string='Number of state to invoice', readonly=True)
    state_amount = fields.Integer(
        compute = '_compute_state_count',
        string = 'Total amount of this state', readonly=True)

    def _compute_state_count(self):
        for rec in self: # take all id/obj(state) of current model,we set 8 states by data.xml
            domain = [('state', '=', rec.state_name)]

            count = self.env['account.payment'].sudo().search_count(domain) # take 'state' of 'account.payment' by current state_name dynamically
            cnt = self.env['account.payment'].sudo().search(domain)
            total_amount = 0
            for am in cnt:
                total_amount += am.amount
            print('total amount',total_amount)
            print('cnt is',cnt)

            rec.state_count = count # we store all states value in 'state_count' variable dynamically, when the function is called by kanban view it show all states value one by one
            rec.state_amount = total_amount # take amount of a specific state, 'rec' iterate over all states on current model
            print('rec.state_count',rec.state_count) # iterate all states(id of this model) and return in xml
            print('rec.state_amount',rec.state_amount)

    def title_action(self):
        """return action based on type for related journals"""
        # action_name = self._context.get('action_name')
        action_name = 'account.action_account_payments' # take the action of a 'account' module
        # Find action based on journal.
        action = self.env.ref(action_name).read()[0] # if you access action then use 0th index of 'action_name'
        action['domain'] = [('state', '=', self.state_name)] # here 'state' is field of 'account.payment' model which is in 'action_name','self' is current model

        # if self.state == 'sale':
        # count = self.env['account.payment'].sudo().search_count(domain)
        # action['domain'] = [('state_name', '=', self.state_name)]
        return action
    # def _compute_fpo_product_count(self):
    #     for rec in self:
    #         domain = [('state', '=', rec.state_name)]
    #         fpos = self.env['foreign.purchase.order'].sudo().search(domain)
    #         product_count = 0
    #         for fpo in fpos:
    #             product_count += len(fpo.line_ids)
    #         rec.fpo_product_count = product_count
    # def action_foreign_purchase_order(self):
    #     action_name = 'usl_forign_purchase_dashboard.action_foreign_po_order_kanban'
    #     for rec in self:
    #         print('state name : ', rec.state_name)
    #         domain = [('state', '=', rec.state_name)]
    #         fpos = self.env['foreign.purchase.order'].sudo().search(domain)
    #         fpo_id = list()
    #         for fpo in fpos:
    #             fpo_id.append(fpo.id)
    #         action = self.env.ref(action_name).read()[0]
    #         action['domain'] = [('id', 'in', fpo_id)]
    #         return action

# from odoo import api, fields, models, _
#
#
# class ChequeModelDash(models.Model):
#     _name = 'cheque.model'
#     _description = 'Cheque Model'
#     state_name = fields.Char(string='State Name')
#     product_count = fields.Integer(string='Product Count.')
#     # color = fields.Integer(string='Color Index', help="The color of the channel")
#     # dashboard_button_name = fields.Char(string="Dashboard Button", compute='_compute_dashboard_button_name')
#     draft_count = fields.Integer(
#         compute='_compute_draft_count',
#         string='Number of draft', readonly=True)
#     sent_count = fields.Integer(
#         compute='_compute_sent_count',
#         string='Number of sent', readonly=True)
#
#     honored_amount = fields.Integer(
#         compute='_compute_honored_amount',
#         string='Total amount of honored amount', readonly=True)
#     # fpo_product_amount = fields.Integer(
#     #     compute='_compute_sales_to_invoice',
#     #     string='Number of sales to invoice', readonly=True)
#
#     def _compute_total(self):
#         # print('self is',self)
#         # for record in self:  # self takes all id,and here iterate each product id
#         print('yes yes')
#         # cnt = 0
#         # for record in self:
#         total_draft = self.env['account.payment'].sudo().search_count(
#             [('state', '=', 'draft')])
#         total_sent = self.env['account.payment'].sudo().search_count(
#             [('state', '=', 'sent')])
#         total_dishonored = self.env['account.payment'].sudo().search_count(
#             [('state', '=', 'dishonored')])
#         total_posted = self.env['account.payment'].sudo().search_count(
#
#         amount_honored = self.env['account.payment'].sudo().search_count(
#             [('state', '=', 'honored')])

    # def _compute_draft_count(self):
    #     for rec in self: # self take all id/obj of current model(cheque.model),the id of current model is state,so take all state only
    #         # domain = [('state', '=', rec.state_name)] # here a list where 'state' is same as current model state
    #         count = self.env['account.payment'].sudo().search_count([('state', '=', 'draft')]) # 'state' is the field of 'account.payment' model and search count with current model's 'state_name'
    #         rec.draft_count = count

    # def action_f_p_o_product(self):
    #     action_name = 'usl_forign_purchase_dashboard.forigin_purches_order_kanban_action'
    #     for rec in self:
    #         print('state name : ', rec.state_name)
    #         domain = [('state', '=', rec.state_name)]
    #         fpos = self.env['foreign.purchase.order'].sudo().search(domain)
    #         fpo_id = list()
    #         for fpo in fpos:
    #             fpo_id.append(fpo.id)
    #         action = self.env.ref(action_name).read()[0]
    #         action['domain'] = [('order_id', 'in', fpo_id)]
    #         return action