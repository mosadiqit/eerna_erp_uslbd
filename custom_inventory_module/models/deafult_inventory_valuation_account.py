from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)')], string="Costing Method",
        company_dependent=True, copy=True, required=True,
        help="""Standard Price: The products are valued at their standard cost defined on the product.
            Average Cost (AVCO): The products are valued at weighted average cost.
            First In First Out (FIFO): The products are valued supposing those that enter the company first will also leave it first.
            """, default='average')

    property_valuation = fields.Selection([
        ('manual_periodic', 'Manual'),
        ('real_time', 'Automated')], string='Inventory Valuation',
        company_dependent=True, copy=True, required=True,
        help="""Manual: The accounting entries to value the inventory are not posted automatically.
        Automated: An accounting entry is automatically created to value the inventory when a product enters or leaves the company.
        """, default='real_time')

    property_account_expense_categ_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Expense Account",
        domain="['&', ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="""The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation
              in which case the expense (Cost of Goods Sold account) is recognized at the customer invoice validation.""",
        default=lambda self: self.env['account.account'].search([('name', 'like', '%Cost of Goods Sold%')]))
        # default=lambda self: self.load_account_expense_default())
