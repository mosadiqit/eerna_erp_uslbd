# from soupsieve.util import upper

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_is_zero
from datetime import date, datetime
from lxml import etree


class InheritStockLandedCostLines(models.Model):
    _inherit = 'stock.landed.cost.lines'

    # product_id=fields.Many2one('product.product', string="Product")
    partner = fields.Many2one('res.partner', string="Partner")
    invoice_line_product_id = fields.Integer()
    invoice_line_product_name = fields.Many2one('product.product', domain=lambda self: self._get_product())
    cd = fields.Float(string="Customs Duty (CD)")
    cd_partner=fields.Many2one('res.partner', string='Customs Duty Partner')
    at = fields.Float(string="Advance Tax (AT)")
    at_partner=fields.Many2one('res.partner', string='Advance Tax Partner')
    ait = fields.Float(string="Advance Income Tax (AIT)")
    ait_partner=fields.Many2one('res.partner', string='Advance Income Tax Partner')

    df = fields.Float(string="Document Fee")
    df_partner = fields.Many2one('res.partner', string='Document Fee Partner')
    cf = fields.Float(string="C&F and Clearing Mics")
    cf_partner = fields.Many2one('res.partner', string='C&F and Clearing Mics Partner')
    # cf_partner_id = fields.Many2one('res.partner', string='C&F Partner')
    transport = fields.Float(string="Transport Charges")
    transport_partner = fields.Many2one('res.partner', string='Transport Partner')
    freight = fields.Float(string="Freight Charges")
    freight_partner = fields.Many2one('res.partner', string='Freight Partner')
    insurance = fields.Float(string="Insurance")
    insurance_partner = fields.Many2one('res.partner', string='Insurance Partner')
    lc_commision = fields.Float(string="LC Commision")
    lc_commision_partner = fields.Many2one('res.partner', string='LC Commision Partner')
    lc_vat = fields.Float(string="LC VAT")
    lc_vat_partner = fields.Many2one('res.partner', string='LC Vat Partner')

    port_demarrage = fields.Float(string="Port Demurrage")
    port_demarrage_partner = fields.Many2one('res.partner', string='Port Demurrage Partner')
    other = fields.Float(string="Other")
    other_partner = fields.Many2one('res.partner', string='other Partner')


    vat = fields.Float(string="Value Added Tax (VAT)")
    vat_partner = fields.Many2one('res.partner', string='Value Added Tax partner')
    sd = fields.Float(string="Supplementary Duty (SD)")
    sd_partner = fields.Many2one('res.partner', string='Supplementary Duty partner')
    rd = fields.Float(string="Regularity Duty (RD)")
    rd_partner = fields.Many2one('res.partner', string='Regularity Duty partner')
    atv = fields.Float(string="Advance Trade VAT(ATV)")
    atv_partner = fields.Many2one('res.partner', string='Advance Trade VAT partner')
    fbc = fields.Float(string="Foreign Bank Charge")
    fbc_partner = fields.Many2one('res.partner', string='Foreign Bank Charge partner')


    provision_for_warranty_cost = fields.Float(string="Provision For Warranty Cost")
    provision_for_marketting_expenses = fields.Float(string="Provision For Marketing Expenses")
    provision_for_salary = fields.Float(string="Provision For Salary")
    provision_for_bank_interest = fields.Float(string="Provision For Bank Interest")
    provision_for_product_insurance = fields.Float(string="Provision For Product Insurance")
    provision_for_income_tax = fields.Float(string="Provision For Income Tax")
    provision_for_trade_promotion = fields.Float(string="Provision For Trade Promotion")
    provision_for_dollar_risk = fields.Float(string="Provision For Dollar Risk")
    provision_for_sadaqua = fields.Float(string="Provision For Sadaqua")
    provision_for_sales_courier = fields.Float(string="Provision For Sales Courier")
    provision_for_house_rent = fields.Float(string="Provision For House Rent")
    provision_for_opex = fields.Float(string="Provision Other Opex")
    provision_for_damage_goods = fields.Float(string="Provision For Damage Goods")
    provision_for_ta_da = fields.Float(string="Provision For TA/DA")
    provision_for_bad_debt = fields.Float(string="Provision For Bad Debt")

    provision_for_emp_incentive = fields.Float(string="Provision For Emp. Incentive")
    provision_for_vat = fields.Float(string="Provision For Vat")
    # provision_1=fields.Float(string="Provision For TA/DA")
    # provision_2=fields.Float(string="Provision For TA/DA")

    price_unit_foreign = fields.Float(string="Total", compute="_update_price")

    @api.depends('cd', 'at', 'ait', 'df', 'cf','transport' ,'freight', 'insurance', 'lc_commision', 'lc_vat', 'port_demarrage',
                 'other','vat','sd','rd','atv','fbc',
                 'provision_for_warranty_cost', 'provision_for_marketting_expenses', 'provision_for_salary',
                 'provision_for_bank_interest',
                 'provision_for_product_insurance', 'provision_for_income_tax', 'provision_for_trade_promotion',
                 'provision_for_dollar_risk', 'provision_for_sadaqua', 'provision_for_sales_courier',
                 'provision_for_house_rent',
                 'provision_for_opex', 'provision_for_damage_goods', 'provision_for_ta_da', 'provision_for_bad_debt','provision_for_emp_incentive','provision_for_vat')
    # @api.onchange('cd', 'at', 'ait', 'df', 'cf', 'transport', 'freight', 'insurance', 'lc_commision', 'lc_vat',
    #              'port_demarrage',
    #              'other', 'vat', 'sd', 'rd', 'atv', 'fbc',
    #              'provision_for_warranty_cost', 'provision_for_marketting_expenses', 'provision_for_salary',
    #              'provision_for_bank_interest',
    #              'provision_for_product_insurance', 'provision_for_income_tax', 'provision_for_trade_promotion',
    #              'provision_for_dollar_risk', 'provision_for_sadaqua', 'provision_for_sales_courier',
    #              'provision_for_house_rent',
    #              'provision_for_opex', 'provision_for_damage_goods', 'provision_for_ta_da', 'provision_for_bad_debt',
    #              'provision_for_emp_incentive', 'provision_for_vat')
    def _update_price(self):
        for rec in self:
            rec.price_unit_foreign = rec.cd + rec.at + rec.ait + rec.df + rec.cf +rec.transport+ rec.freight \
                             + rec.insurance + rec.lc_commision + rec.lc_vat + rec.port_demarrage + rec.other+rec.vat+rec.sd+rec.rd+rec.atv+rec.fbc + rec.provision_for_warranty_cost + \
                             rec.provision_for_marketting_expenses + rec.provision_for_salary + rec.provision_for_bank_interest + \
                             rec.provision_for_product_insurance + rec.provision_for_income_tax + rec.provision_for_trade_promotion + \
                             rec.provision_for_dollar_risk + rec.provision_for_sadaqua + rec.provision_for_sales_courier + rec.provision_for_house_rent + \
                             rec.provision_for_opex + rec.provision_for_damage_goods + rec.provision_for_ta_da + rec.provision_for_bad_debt+rec.provision_for_emp_incentive+rec.provision_for_vat
            rec.price_unit=rec.price_unit_foreign

    def _get_product(self):
        if len(self) > 0:
            for rec in self:
                if rec.invoice_line_product_id == None:
                    rec.invoice_line_product_name = None
                else:
                    rec.invoice_line_product_name = rec.invoice_line_product_id

    @api.onchange('product_id')
    def onchange_product_id(self):
        print(self.product_id.name)
        price_unit = 0.0
        val = self._context.get('picking_ids')
        if self.product_id:
            if self.product_id.name.__contains__('Overseas'):
                if self._context.get('picking_ids'):
                    val = self._context.get('picking_ids')
                    print(val[0][2])
                    picking_ids = val[0][2]
                    if len(picking_ids) == 1:
                        # query="""select po.currency_rate from stock_picking sp
                        #         left join foreign_purchase_order po on po.name=sp.origin
                        #         left join foreign_purchase_order_line pol on pol.order_id=po.id
                        #         where sp.id = {}""".format(picking_ids[0])
                        # self._cr.execute(query=query)
                        # currency_rate = self._cr.fetchone()
                        currency_rate = self.env.ref('base.main_company').currency_id.rate
                        query_total_bank = """select sum(aml.total_local_payment) from stock_picking sp                            
                                left join account_move am on am.invoice_origin=sp.origin
                                left join account_move_line aml on aml.move_id=am.id
                                where sp.id = {}""".format(picking_ids[0])
                        # query_total_os=
                        self._cr.execute(query=query_total_bank)
                        total_bank_payment = self._cr.fetchone()
                    else:
                        # query = """select po.currency_rate from stock_picking sp
                        #                             left join foreign_purchase_order po on po.name=sp.origin
                        #                             left join foreign_purchase_order_line pol on pol.order_id=po.id
                        #                             where sp.id = {}""".format(picking_ids[0])
                        # self._cr.execute(query=query)
                        # currency_rate = self._cr.fetchone()
                        currency_rate = self.env.ref('base.main_company').currency_id.rate
                        query_total_bank = """select sum(aml.total_local_payment) from stock_picking sp                            
                                left join account_move am on am.invoice_origin=sp.origin
                                left join account_move_line aml on aml.move_id=am.id
                                where sp.id in {}""".format(tuple(picking_ids))
                        self._cr.execute(query=query_total_bank)
                        total_bank_payment = self._cr.fetchone()
                    print(currency_rate)
                    print(total_bank_payment)
                    if total_bank_payment[0] != None and currency_rate != None:
                        price_unit = total_bank_payment[0] * currency_rate
                    else:
                        price_unit = 0.0
                    print(total_bank_payment)

                if not self.product_id:
                    self.quantity = 0.0
                self.name = self.product_id.name or ''
                self.split_method = self.split_method or 'by_current_cost_price'
                self.price_unit = price_unit or 0.0
                accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
                self.account_id = accounts_data['stock_input']
            else:
                if not self.product_id:
                    self.quantity = 0.0
                self.name = self.product_id.name or ''
                self.split_method = self.split_method or 'by_current_cost_price'
                self.price_unit = self.product_id.standard_price or 0.0
                accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
                self.account_id = accounts_data['stock_input']
        else:
            self.quantity = 0.0
            self.name = self.product_id.name or ''
            self.split_method = self.split_method or 'by_current_cost_price'
            self.price_unit = self.product_id.standard_price or 0.0
            accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
            self.account_id = accounts_data['stock_input']


class InheritStockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(InheritStockLandedCost, self).fields_view_get(view_id=view_id, view_type=view_type,
    #                                                                    toolbar=toolbar, submenu=submenu)
    #     if view_type == 'tree':
    #         doc = etree.XML(res['arch'])
    #         product_id_field = doc.xpath("//field[@name='cost_lines']/field[@name=" + 'product_id' + "]")
    #         if product_id_field:
    #             product_id_field[0].addnext(etree.Element("field", {'string': 'Test', 'name': 'Total'}))
    #         res['arch'] = etree.tostring(doc, encoding='unicode')
    #     return res

    button_state = fields.Selection([
        ('cd', 'CD'),
        ('probation', 'Probation'),
        ('compute', 'Compute'),
    ], 'Incoterms', default='cd')
    vendor_bill_id_new = fields.Many2one('account.move', string='Foreign vendor bill')
    preview_costing = fields.One2many('stock.preview.costing', 'cost_id', 'Preview Costing',
                                      states={'done': [('readonly', True)]})

    @api.onchange('vendor_bill_id')
    def test(self):
        print("changed")

    def button_validate_foreign(self):
        print(self.env.user)
        print(self.env.user.company_id)
        # print(self.env.user.context)
        column_name = self.cost_lines.fields_get()
        line_ids = []
        journal_ids = []
        for cost in self:
            line_ids = []
            journal_ids = []
            for rec in cost.cost_lines:
                debit_account_id = rec.product_id.product_tmpl_id.categ_id.property_stock_account_input_categ_id.id
                total_expense = 0.0
                cd_lines = self.env['product.product'].search([('id', '=', rec.product_id.id)])
                cd_product_lines = self.env['product.template'].search([('id', '=', cd_lines.product_tmpl_id.id)])
                get_related_provision_item=self.env['probational.attribute.setup'].search([('product_id','=',rec.product_id.product_tmpl_id.id)])
                # for product in cd_product_lines:
                for cd_product in cd_product_lines.product_hs_code_id.hs_code_line:
                    for key in column_name.keys():
                        print(column_name[key]['string'])
                        if str(cd_product.tax_type_id.name).upper() == str(column_name[key]['string']).upper():

                            if len(cd_product.account_id) > 0:
                                # partner_id=cd_product.partner_id.id if len(cd_product.partner_id)>0 else rec[key+'_partner_id']
                                # if len(cd_product.partner_id) > 0:
                                #     partner_id = cd_product.partner_id.id
                                # else:
                                if key + '_partner' in column_name.keys():
                                    partner_id = rec[key + '_partner'].id if len(
                                        rec[key + '_partner']) > 0 else None
                                else:
                                    partner_id = None
                                account_id = cd_product.account_id.id
                                # debit_account_id=self.env['account.account'].search([('root_id','=',49049),('company_id','=',self.env.user.company_id.id)])



                                total_expense += rec[key]
                                val = (0, 0, {
                                    'partner_id': partner_id,
                                    'branch_id': self.env['res.users'].search(
                                        [('id', '=', self.env.user.id)]).branch_id.id,
                                    'currency_id': False,
                                    'debit': 0,
                                    'credit': rec[key],
                                    'quantity': 0,
                                    'discount': 0,
                                    'sequence': 10,
                                    'account_id': account_id,
                                    'parent_state': 'draft',
                                    'product_id':rec.product_id.id
                                })
                                line_ids.append(val)
                                val = (0, 0, {
                                    'partner_id': partner_id,
                                    'branch_id': self.env['res.users'].search(
                                        [('id', '=', self.env.user.id)]).branch_id.id,
                                    'currency_id': False,
                                    'debit': rec[key],
                                    'credit': 0,
                                    'quantity': 0,
                                    'discount': 0,
                                    'sequence': 10,
                                    'account_id':debit_account_id ,
                                    # 'account_id': 186,
                                    'parent_state': 'draft',
                                    'product_id': rec.product_id.id
                                })
                                line_ids.append(val)
                                break



                            else:
                                raise ValidationError(_("Account is not set for\n"+"HS-Code Other Tax Type="+"'"+cd_product.tax_type_id.name)+"'"+"\nwhich you find inside attached HS-Code of"+"\nproduct="+"'"+rec.name+"'")

                for provision in get_related_provision_item:
                    account_id=provision.probational_product_id.property_account_expense_id
                    for key in column_name.keys():
                        if str(provision.probational_product_id.name).upper() == str(column_name[key]['string']).upper():
                            if account_id.id>0:
                                val = (0, 0, {
                                    'partner_id': None,
                                    'branch_id': self.env['res.users'].search(
                                        [('id', '=', self.env.user.id)]).branch_id.id,
                                    'currency_id': False,
                                    'debit': 0,
                                    'credit': rec[key],
                                    'quantity': 0,
                                    'discount': 0,
                                    'sequence': 10,
                                    'account_id': account_id.id,
                                    'parent_state': 'draft',
                                    'product_id': rec.product_id.id
                                })
                                line_ids.append(val)
                                val = (0, 0, {
                                    'partner_id': None,
                                    'branch_id': self.env['res.users'].search(
                                        [('id', '=', self.env.user.id)]).branch_id.id,
                                    'currency_id': False,
                                    'debit': rec[key],
                                    'credit': 0,
                                    'quantity': 0,
                                    'discount': 0,
                                    'sequence': 10,
                                    'account_id': debit_account_id,
                                    # 'account_id': 186,
                                    'parent_state': 'draft',
                                    'product_id': rec.product_id.id
                                })
                                line_ids.append(val)
                                break
                            else:
                                # raise ValidationError(
                                #     _("Expense  Account is not set for\nproduct="+"'" + rec.name +"'"+ "\nColumn="+"'" + provision.probational_product_id.name+"'"))
                                raise ValidationError(
                                    _("Expense  Account is not set for:'" + provision.probational_product_id.name+"'"))

            if len(line_ids) > 0:
                val = {
                    'amount_total': total_expense,
                    'amount_total_signed': total_expense,
                    'branch_id': self.env['res.users'].search([('id', '=', self.env.user.id)]).branch_id.id,
                    'date': date.today(),
                    'journal_id': cost.account_journal_id.id,
                    'currency_id': self.env.ref('base.main_company').currency_id.id,
                    'line_ids': line_ids,
                    'ref': self.name,
                    'state': 'draft'

                }
                journal_ids.append(val)
            account_move = self.env['account.move']
            account_move = account_move.create(journal_ids)
        # account_move.state='posted'
        account_move.post()

        # total_expense=0.0
        # val_list = []
        # line_ids = []
        # for line in self.cost_lines:
        #
        #     if len(line.partner)>0:
        #
        #         total_expense+=line.price_unit
        #         val=(0,0,{
        #             'partner_id':line.partner.id,
        #             'branch_id':self.env['res.users'].search([('id','=',self.env.user.id)]).branch_id.id,
        #             'currency_id':False,
        #             'debit':0,
        #             'credit':line.price_unit,
        #             'quantity':0,
        #             'discount':0,
        #             'sequence':10,
        #             'account_id':self.env['account.account'].search([('root_id','=',50049),('company_id','=',self.env.user.company_id.id)]).id,
        #             'parent_state':'draft'
        #
        #         })
        #         line_ids.append(val)
        #         # val_list.append(val)
        #
        #
        # if len(line_ids)>0:
        #     val = (0, 0, {
        #         # 'partner_id': line.partner.id,
        #         'branch_id': self.env['res.users'].search([('id', '=', self.env.user.id)]).branch_id.id,
        #         'currency_id': False,
        #         'debit': total_expense,
        #         'credit': 0,
        #         'quantity': 0,
        #         'discount': 0,
        #         'sequence': 10,
        #         'account_id': self.env['account.account'].search(
        #             [('root_id', '=', 50048), ('company_id', '=', self.env.user.company_id.id)]).id,
        #         'parent_state': 'draft'
        #     })
        #     line_ids.append(val)
        #     val={
        #         'amount_total':total_expense,
        #         'amount_total_signed': total_expense,
        #         'branch_id':self.env['res.users'].search([('id', '=', self.env.user.id)]).branch_id.id,
        #         'date':date.today(),
        #         'journal_id':34,
        #         'currency_id':self.env.ref('base.main_company').currency_id.id,
        #         'line_ids':line_ids,
        #         'ref':self.name,
        #         'state':'draft'
        #
        #     }
        #     val_list.append(val)
        #     account_move=self.env['account.move']
        #     account_move=account_move.create(val_list)
        #     # account_move.state='posted'
        #     account_move.post()
        # account_move.execute( 'account.move', 'post', [[account_move.id], {'state': "posted"}])
        # for line in account_move.line_ids:
        #     line.parent_state='posted'
        # account_move.write(val_list)

        active_model = self.env.context.get('active_model')
        print(active_model)
        for line in self.cost_lines:
            line.partner = None

        if any(cost.state != 'draft' for cost in self):
            raise UserError(_('Only draft landed costs can be validated'))
        if not all(cost.picking_ids for cost in self):
            raise UserError(_('Please define the transfers on which those additional costs should apply.'))
        cost_without_adjusment_lines = self.filtered(lambda c: not c.valuation_adjustment_lines)
        if cost_without_adjusment_lines:
            cost_without_adjusment_lines.compute_landed_cost()
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

        for cost in self:
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
                'type': 'entry',
            }
            valuation_layer_ids = []
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                product = line.move_id.product_id
                svl_qty=product.quantity_svl
                total_length = len(cost.valuation_adjustment_lines)
                per_line_bank_payment = 0.0
                # invoice_products=self.env['account.move'].search([('vendor_bill_id','=',cost.vendor_bill_id.id)])
                # for product in cost.vendor_bill_id.line_ids:
                #     if line.product_id.id==product.product_id.id and product.account_internal_type!='payable':
                #         bank_payment=product.bank_payment*product.quantity*self.env.ref('base.main_company').currency_id.rate
                #         per_line_bank_payment=bank_payment/total_length
                # linked_layer=self.env['stock.valuation.layer']
                # if active_model == 'foreign.purchase.order':
                #     query="select quantity,product_id from account_move_line where move_id={} and account_internal_type!='payable' ".format(self.vendor_bill_id.id)
                #     self._cr.execute(query=query)
                #     res=self._cr.fetchall()
                #     invoice_qty=0.0
                #     for qty in res:
                #         if qty[1]==line.product_id.id:
                #             remaining_qty=qty[0]+line.move_id.stock_valuation_layer_ids.mapped('remaining_qty')
                # remaining_qty=res[0]


                # remaining_qty=line.move_id.stock_valuation_layer_ids.mapped('remaining_qty')
                # else:
                remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                linked_layer = line.move_id.stock_valuation_layer_ids[:1]

                # Prorate the value at what's still in stock

                # if active_model == 'foreign.purchase.order':
                    # if product.tracking=='serial':
                cost_to_add = (remaining_qty / remaining_qty) * line.additional_landed_cost
                # else:
                #     cost_to_add = (remaining_qty / line.move_id.product_qty) * line.additional_landed_cost

                if not cost.company_id.currency_id.is_zero(cost_to_add):
                    valuation_layer = self.env['stock.valuation.layer'].create({
                        'value': cost_to_add,
                        'unit_cost': 0,
                        'quantity': 0,
                        'remaining_qty': 0,
                        'stock_valuation_layer_id': linked_layer.id,
                        'description': cost.name,
                        'stock_move_id': line.move_id.id,
                        'product_id': line.move_id.product_id.id,
                        'stock_landed_cost_id': cost.id,
                        'company_id': cost.company_id.id,
                    })
                    linked_layer.remaining_value += cost_to_add
                    valuation_layer_ids.append(valuation_layer.id)
                # Update the AVCO
                product = line.move_id.product_id
                if product.cost_method == 'average' and not float_is_zero(product.quantity_svl,
                                                                          precision_rounding=product.uom_id.rounding):
                    # if active_model == 'foreign.purchase.order':
                        # changeable_standard_price=product.with_context(force_company=self.company_id.id).sudo().changeable_standard_price

                    product.with_context(
                        force_company=self.company_id.id).sudo().previous_standard_price =product.with_context(
                        force_company=self.company_id.id).sudo().standard_price
                    product.with_context(
                        force_company=self.company_id.id).sudo().changeable_standard_price += cost_to_add / product.quantity_svl
                    product.with_context(
                        force_company=self.company_id.id).sudo().standard_price = product.with_context(
                        force_company=self.company_id.id).sudo().changeable_standard_price
                    # else:
                    #     product.with_context(
                    #         force_company=self.company_id.id).sudo().standard_price += cost_to_add / product.quantity_svl

                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                # if active_model == 'foreign.purchase.order':
                if line.move_id._is_in_foreign():
                    qty_out = remaining_qty - remaining_qty
                elif line.move_id._is_out():
                    qty_out = line.move_id.product_qty
                # else:
                #     if line.move_id._is_in():
                #         qty_out = line.move_id.product_qty - remaining_qty
                #     elif line.move_id._is_out():
                #         qty_out = line.move_id.product_qty

                move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)

            move_vals['stock_valuation_layer_ids'] = [(6, None, valuation_layer_ids)]
            move = move.create(move_vals)
            cost.write({'state': 'done', 'account_move_id': move.id})
            move.post()

            if cost.vendor_bill_id and cost.vendor_bill_id.state == 'posted' and cost.company_id.anglo_saxon_accounting:
                all_amls = cost.vendor_bill_id.line_ids | cost.account_move_id.line_ids
                for product in cost.cost_lines.product_id:
                    accounts = product.product_tmpl_id.get_product_accounts()
                    input_account = accounts['stock_input']
                    # all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()
                    all_amls.filtered(
                        lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()
        return True

    def apply_cd_cost(self):
        column_name = self.cost_lines.fields_get()
        self.cost_lines = [(5, 0, 0)]
        val = {}
        cd_cost_lines = []
        for initial in self:
            for rec in initial.picking_ids.move_lines:

                cd_lines = self.env['product.product'].search([('id', '=', rec.product_id.id)])
                cd_product_lines = self.env['product.template'].search([('id', '=', cd_lines.product_tmpl_id.id)])
                query = """select aml.bank_payment,aml.quantity,aml.product_id from account_move am
                                                left join account_move_line aml on aml.move_id = am.id
                    	                       where  am.name = '{}' and aml.product_id = {}""".format(
                    initial.vendor_bill_id.name, rec.product_id.id)
                self._cr.execute(query)
                result = self._cr.fetchone()
                if result:
                    for product in cd_product_lines:
                        vals = {
                            'product_id': rec.product_id.id,
                            'name': product.name,
                            'split_method': 'by_current_cost_price',
                            'price_unit': 0,
                            # 'invoice_line_product_id': result[2],
                            # 'invoice_line_product_name': result[2],
                        }
                        for cd_rec in cd_product_lines.product_hs_code_id.hs_code_line:
                            product_name = cd_rec.tax_type_id.name
                            for key in column_name.keys():
                                column_string = self.cost_lines.fields_get()[key]['string']
                                if str(column_string).upper() == str(product_name).upper():
                                    vals[key] = ((result[0] * self.env.ref(
                                        'base.main_company').currency_id.rate * cd_rec.assessable_rate) / 100) * result[1]
                                    vals[key+"_"+"partner"]=cd_rec.partner_id.id
                                    vals['price_unit']+=vals[key]
                                    break

                        cd_cost_lines.append((0, 0, vals))

        initial.cost_lines = cd_cost_lines

    def get_valuation_lines_foreign(self):
        get_company_data = self.env['product.sale.accounting'].search([('company_id', '=', self.company_id.id)])
        if get_company_data:
            lines = []
            total_invoice_amount = 0.0
            total_invoice_amount_overseas = 0.0
            total_invoice_amount_other = 0.0
            # for rec in self.cost_lines:
            #     print(rec.name)
            for move in self.picking_ids.move_lines:
                query = """select aml.total_bank_payment,aml.total_local_payment,aml.price_unit,aml.quantity from stock_move sm
                                        left join account_move am on am.invoice_origin=sm.origin
                                        left join account_move_line aml on aml.move_id=am.id
                                        where sm.id = {} and aml.move_id={} and aml.account_internal_type!='payable' and sm.product_id = aml.product_id""".format(
                    move.id, self.vendor_bill_id.id)

                self._cr.execute(query=query)
                total_bank_local = self._cr.fetchone()
                if total_bank_local:
                    total_invoice_amount += total_bank_local[2]
                    total_invoice_amount_overseas += 0 if total_bank_local[1] == None else total_bank_local[1]
                    total_invoice_amount_other += 0 if total_bank_local[0] == None else total_bank_local[0]

            for move in self.picking_ids.move_lines:
                query = """select aml.total_bank_payment,aml.total_local_payment,aml.price_unit,aml.quantity,aml.company_currency_id from stock_move sm
                                                    left join account_move am on am.invoice_origin=sm.origin
                                                    left join account_move_line aml on aml.move_id=am.id
                                                    where sm.id = {} and aml.move_id={} and aml.account_internal_type!='payable' and sm.product_id = aml.product_id""".format(
                    move.id, self.vendor_bill_id.id)
                self._cr.execute(query=query)
                total_bank_local = self._cr.fetchone()
                # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
                # if move.product_id.valuation != 'real_time' or move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel':
                #     continue
                if total_bank_local:
                    if get_company_data.property_valuation != 'real_time' or get_company_data.property_cost_method not in (
                    'fifo', 'average') or move.state == 'cancel':
                        continue
                    vals = {
                        'product_id': move.product_id.id,
                        'move_id': move.id,
                        'quantity': total_bank_local[3],
                        # 'probational_sum':self._get_sum_provisional_value(move.product_id.id),
                        # 'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                        # 'former_cost': total_bank_local[0]*self.env.ref('base.main_company').currency_id.rate*total_bank_local[3],
                        'former_cost': total_bank_local[0] * self.env.ref('base.main_company').currency_id.rate,
                        'former_cost_overseas': total_invoice_amount_overseas * self.env['res.currency.rate'].search(
                            [('currency_id', '=', total_bank_local[4])]).rate,
                        'former_cost_other': total_invoice_amount_other * self.env.ref(
                            'base.main_company').currency_id.rate,

                        'weight': move.product_id.weight * total_bank_local[3],
                        'volume': move.product_id.volume * total_bank_local[3],
                        'bank_payment': (total_bank_local[0] / total_bank_local[3]) * self.env.ref(
                            'base.main_company').currency_id.rate,
                        'total_bank_payment': total_bank_local[0] * self.env.ref('base.main_company').currency_id.rate,
                        'local_payment': (total_bank_local[1] / total_bank_local[3]) * self.env['res.currency'].search(
                            [('id', '=', total_bank_local[4])]).local_currency,
                        'total_local_payment': total_bank_local[1] * self.env['res.currency'].search(
                            [('id', '=', total_bank_local[4])]).local_currency,

                    }
                    lines.append(vals)

            if not lines and self.mapped('vendor_bill_id.invoice_line_ids'):
                raise UserError(_(
                    "You cannot apply landed costs on the chosen transfer(s). Landed costs can only be applied for products with automated inventory valuation and FIFO or average costing method."))
            return lines
        else:
            raise ValidationError(_("Please first set your company accounting setting!!!"))



    def compute_landed_cost_foreign(self):
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

        digits = self.env['decimal.precision'].precision_get('Product Price')
        towrite_dict = {}
        for cost in self.filtered(lambda cost: cost.picking_ids):
            
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            new_all_val_line_value = []
            new_all_line_preview_costing = []
            all_val_line_values = cost.get_valuation_lines_foreign()
            default_currency_id = self.env.ref('base.main_company').currency_id.id
            bank_rate = self.env['res.currency.rate'].search([('currency_id', '=', default_currency_id)]).rate
            local_rate = self.env.ref('base.main_company').currency_id.local_currency

            for val_line_values in all_val_line_values:

                for cost_line in cost.cost_lines:

                    new_val_line_values = {}
                    new_val_line_preview_costing = {}
                    # if cost_line.invoice_line_product_id == 0:
                    #
                    #     print(cost_line.name)
                    #     val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                    #     new_val_line_values = {
                    #         'product_id': val_line_values['product_id'],
                    #         'move_id': val_line_values['move_id'],
                    #         'quantity': val_line_values['quantity'],
                    #         'former_cost': val_line_values['former_cost'],
                    #         'weight': val_line_values['weight'],
                    #         'volume': val_line_values['volume'],
                    #         'cost_id': val_line_values['cost_id'],
                    #         'cost_line_id': val_line_values['cost_line_id']
                    #     }
                    #     # self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                    #     self.env['stock.valuation.adjustment.lines'].create(new_val_line_values)
                    #     new_val_line_values = {
                    #         'product_id': val_line_values['product_id'],
                    #         'move_id': val_line_values['move_id'],
                    #         'quantity': val_line_values['quantity'],
                    #         # 'probational_sum':val_line_values['probational_sum'],
                    #         'former_cost': val_line_values['former_cost'],
                    #         'weight': val_line_values['weight'],
                    #         'volume': val_line_values['volume'],
                    #         'cost_id': val_line_values['cost_id'],
                    #         'cost_line_id': val_line_values['cost_line_id'],
                    #         'total_bank_payment': val_line_values['total_bank_payment'],
                    #         'total_local_payment': val_line_values['total_local_payment'],
                    #     }
                    #     print(new_val_line_values)
                    #     new_all_val_line_value.append(new_val_line_values)
                    # else:
                    if cost_line.product_id.id == val_line_values['product_id']:
                        # query="""select phcl.tax_type_id from product_product pp
                        # left join product_template pt on pt.id=pp.product_tmpl_id
                        # left join product_hs_code phc on pt.product_hs_code_id=phc.id
                        # left join product_hs_code_line phcl on phcl.hs_code_line_id=phc.id where pp.id={}""".format(cost_line.product_id.id)
                        # self._cr.execute(query=query)
                        # hs_product=self._cr.fetchall()
                        # for hsProduct in hs_product:
                        val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                        new_val_line_values = {
                            'product_id': val_line_values['product_id'],
                            'move_id': val_line_values['move_id'],
                            'quantity': val_line_values['quantity'],
                            'former_cost': val_line_values['former_cost'],
                            'weight': val_line_values['weight'],
                            'volume': val_line_values['volume'],
                            'cost_id': val_line_values['cost_id'],
                            'cost_line_id': val_line_values['cost_line_id'],
                            'cd': cost_line.cd,
                            'at': cost_line.at,
                            'ait': cost_line.ait,
                            'df': cost_line.df,
                            'cf': cost_line.cf,
                            'transport': cost_line.transport,
                            'freight': cost_line.freight,
                            'insurance': cost_line.insurance,
                            'lc_commision': cost_line.lc_commision,
                            'lc_vat': cost_line.lc_vat,
                            'port_demarrage': cost_line.port_demarrage,
                            'other': cost_line.other,
                            'vat':cost_line.vat,
                            'sd':cost_line.sd,
                            'rd':cost_line.rd,
                            'atv':cost_line.atv,
                            'fbc':cost_line.fbc,
                            'provision_for_warranty_cost': cost_line.provision_for_warranty_cost,
                            'provision_for_marketting_expenses': cost_line.provision_for_marketting_expenses,
                            'provision_for_salary': cost_line.provision_for_salary,
                            'provision_for_bank_interest': cost_line.provision_for_bank_interest,
                            'provision_for_product_insurance': cost_line.provision_for_product_insurance,
                            'provision_for_income_tax': cost_line.provision_for_income_tax,
                            'provision_for_trade_promotion': cost_line.provision_for_trade_promotion,
                            'provision_for_dollar_risk': cost_line.provision_for_dollar_risk,
                            'provision_for_sadaqua': cost_line.provision_for_sadaqua,
                            'provision_for_sales_courier': cost_line.provision_for_sales_courier,
                            'provision_for_house_rent': cost_line.provision_for_house_rent,
                            'provision_for_opex': cost_line.provision_for_opex,
                            'provision_for_damage_goods': cost_line.provision_for_damage_goods,
                            'provision_for_ta_da': cost_line.provision_for_ta_da,
                            'provision_for_bad_debt': cost_line.provision_for_bad_debt,
                            'provision_for_emp_incentive': cost_line.provision_for_emp_incentive,
                            'provision_for_vat': cost_line.provision_for_vat,

                            # 'cd_new':val_line_values['former_cost']+ cost_line.cd,
                            # 'at_new':val_line_values['former_cost']+ cost_line.at,
                            # 'ait_new':val_line_values['former_cost']+ cost_line.ait,
                            # 'df_new': val_line_values['former_cost']+cost_line.df,
                            # 'cf_new': val_line_values['former_cost']+cost_line.cf,
                            # 'freight_new':val_line_values['former_cost']+ cost_line.freight,
                            # 'insurance_new':val_line_values['former_cost']+ cost_line.insurance,
                            # 'lc_commision_new': val_line_values['former_cost']+cost_line.lc_commision,
                            # 'lc_vat_new':val_line_values['former_cost']+ cost_line.lc_vat,
                            # 'port_demarrage_new':val_line_values['former_cost']+ cost_line.port_demarrage,
                            # 'other_new': val_line_values['former_cost']/+cost_line.other,
                            # 'provision_1_new':val_line_values['former_cost']+ cost_line.provision_1,
                            # 'provision_2_new':val_line_values['former_cost']+ cost_line.provision_2,

                        }
                        self.env['stock.valuation.adjustment.lines'].create(new_val_line_values)
                        new_val_line_values = {
                            'product_id': val_line_values['product_id'],
                            'move_id': val_line_values['move_id'],
                            'quantity': val_line_values['quantity'],
                            # 'probational_sum':val_line_values['probational_sum'],
                            'former_cost': val_line_values['former_cost'],
                            'weight': val_line_values['weight'],
                            'volume': val_line_values['volume'],
                            'cost_id': val_line_values['cost_id'],
                            'cost_line_id': val_line_values['cost_line_id'],
                            'total_bank_payment': val_line_values['total_bank_payment'],
                            'total_local_payment': val_line_values['total_local_payment'],
                        }
                        print(new_val_line_values)
                        new_all_val_line_value.append(new_val_line_values)

                        get_product_changable_standard_price = self.env['product.product'].search(
                            [('id', '=', val_line_values['product_id'])]).changeable_standard_price
                        cd = cost_line.cd / val_line_values['quantity'] if cost_line.cd > 0 else 0
                        at = cost_line.at / val_line_values['quantity'] if cost_line.at > 0 else 0
                        ait = cost_line.ait / val_line_values['quantity'] if cost_line.ait > 0 else 0
                        df = cost_line.df / val_line_values['quantity'] if cost_line.df > 0 else 0
                        cf = cost_line.cf / val_line_values['quantity'] if cost_line.cf > 0 else 0
                        transport=cost_line.transport / val_line_values['quantity'] if cost_line.transport > 0 else 0
                        freight = cost_line.freight / val_line_values['quantity'] if cost_line.freight > 0 else 0
                        insurance = cost_line.insurance / val_line_values['quantity'] if cost_line.insurance > 0 else 0
                        lc_commision = cost_line.lc_commision / val_line_values[
                            'quantity'] if cost_line.lc_commision > 0 else 0
                        lc_vat = cost_line.lc_vat / val_line_values['quantity'] if cost_line.lc_vat > 0 else 0
                        port_demarrage = cost_line.port_demarrage / val_line_values[
                            'quantity'] if cost_line.port_demarrage > 0 else 0
                        other = cost_line.other / val_line_values['quantity'] if cost_line.other > 0 else 0
                        vat = cost_line.vat / val_line_values['quantity'] if cost_line.vat > 0 else 0
                        sd = cost_line.sd / val_line_values['quantity'] if cost_line.sd > 0 else 0
                        rd = cost_line.rd / val_line_values['quantity'] if cost_line.rd > 0 else 0
                        atv = cost_line.atv / val_line_values['quantity'] if cost_line.atv > 0 else 0
                        fbc = cost_line.fbc / val_line_values['quantity'] if cost_line.fbc > 0 else 0
                        provision_for_warranty_cost = cost_line.provision_for_warranty_cost / val_line_values[
                            'quantity'] if cost_line.provision_for_warranty_cost > 0 else 0
                        provision_for_marketting_expenses = cost_line.provision_for_marketting_expenses / \
                                                            val_line_values[
                                                                'quantity'] if cost_line.provision_for_marketting_expenses > 0 else 0
                        provision_for_salary = cost_line.provision_for_salary / val_line_values[
                            'quantity'] if cost_line.provision_for_salary > 0 else 0
                        provision_for_bank_interest = cost_line.provision_for_bank_interest / val_line_values[
                            'quantity'] if cost_line.provision_for_bank_interest > 0 else 0
                        provision_for_product_insurance = cost_line.provision_for_product_insurance / val_line_values[
                            'quantity'] if cost_line.provision_for_product_insurance > 0 else 0
                        provision_for_income_tax = cost_line.provision_for_income_tax / val_line_values[
                            'quantity'] if cost_line.provision_for_income_tax > 0 else 0
                        provision_for_trade_promotion = cost_line.provision_for_trade_promotion / val_line_values[
                            'quantity'] if cost_line.provision_for_trade_promotion > 0 else 0
                        provision_for_dollar_risk = cost_line.provision_for_dollar_risk / val_line_values[
                            'quantity'] if cost_line.provision_for_dollar_risk > 0 else 0
                        provision_for_sadaqua = cost_line.provision_for_sadaqua / val_line_values[
                            'quantity'] if cost_line.provision_for_sadaqua > 0 else 0
                        provision_for_sales_courier = cost_line.provision_for_sales_courier / val_line_values[
                            'quantity'] if cost_line.provision_for_sales_courier > 0 else 0
                        provision_for_house_rent = cost_line.provision_for_house_rent / val_line_values[
                            'quantity'] if cost_line.provision_for_house_rent > 0 else 0
                        provision_for_opex = cost_line.provision_for_opex / val_line_values[
                            'quantity'] if cost_line.provision_for_opex > 0 else 0
                        provision_for_damage_goods = cost_line.provision_for_damage_goods / val_line_values[
                            'quantity'] if cost_line.provision_for_damage_goods > 0 else 0
                        provision_for_ta_da = cost_line.provision_for_ta_da / val_line_values[
                            'quantity'] if cost_line.provision_for_ta_da > 0 else 0
                        provision_for_bad_debt = cost_line.provision_for_bad_debt / val_line_values[
                            'quantity'] if cost_line.provision_for_bad_debt > 0 else 0
                        provision_for_emp_incentive = cost_line.provision_for_emp_incentive / val_line_values[
                            'quantity'] if cost_line.provision_for_emp_incentive > 0 else 0
                        provision_for_vat = cost_line.provision_for_vat / val_line_values[
                            'quantity'] if cost_line.provision_for_vat > 0 else 0
                        product_average_price=get_product_changable_standard_price
                        # cost_price = get_product_changable_standard_price + ((cost_line.cd + cost_line.at + cost_line.ait + cost_line.df + cost_line.cf+cost_line.transport + cost_line.freight + cost_line.insurance + cost_line.lc_commision + cost_line.lc_vat + cost_line.port_demarrage + cost_line.other + \
                        #              cost_line.provision_for_warranty_cost + cost_line.provision_for_marketting_expenses + cost_line.provision_for_salary + cost_line.provision_for_bank_interest + cost_line.provision_for_product_insurance + \
                        #              cost_line.provision_for_income_tax + cost_line.provision_for_trade_promotion + cost_line.provision_for_dollar_risk + cost_line.provision_for_sadaqua + cost_line.provision_for_sales_courier + \
                        #              cost_line.provision_for_house_rent + cost_line.provision_for_opex + cost_line.provision_for_damage_goods + cost_line.provision_for_ta_da + cost_line.provision_for_bad_debt)/cost_line.product_id.quantity_svl)

                        bank_rate=bank_rate
                        bank_payment=val_line_values['bank_payment'] if val_line_values['bank_payment'] > 0 else 0
                        local_rate=local_rate
                        local_payment=val_line_values['local_payment'] if val_line_values['local_payment'] > 0 else 0
                        landed_cost=cd+at+ait+df+cf+freight+insurance+transport+lc_commision+lc_vat+port_demarrage+other+vat+sd+rd+atv+fbc
                        provision=provision_for_warranty_cost+provision_for_marketting_expenses+provision_for_salary+provision_for_bank_interest+\
                        provision_for_product_insurance+provision_for_income_tax+provision_for_trade_promotion+provision_for_dollar_risk+ \
                                  provision_for_sadaqua+provision_for_sales_courier+provision_for_house_rent+provision_for_opex+provision_for_damage_goods+ \
                                  provision_for_ta_da+provision_for_bad_debt+provision_for_emp_incentive+provision_for_vat
                        cost_price=bank_payment+local_payment+landed_cost+provision



                        get_existing = self.env['stock.preview.costing'].search(
                            [('cost_line_id', '=', val_line_values['cost_line_id']),
                             ('product_id', '=', val_line_values['product_id'])])
                        if len(get_existing) > 0:
                            for line in get_existing:
                                if line.product_id.id == val_line_values['product_id']:
                                    line.product_id = val_line_values['product_id']
                                    line.cd = cd
                                    line.at = at
                                    line.ait = ait
                                    line.df = df
                                    line.cf = cf
                                    line.transport=transport
                                    line.freight = freight
                                    line.insurance = insurance
                                    line.lc_commision = lc_commision
                                    line.lc_vat = lc_vat
                                    line.port_demarrage = port_demarrage
                                    line.other = other
                                    line.vat = vat
                                    line.sd = sd
                                    line.rd = rd
                                    line.atv = atv
                                    line.fbc = fbc
                                    line.provision_for_warranty_cost = provision_for_warranty_cost
                                    line.provision_for_marketting_expenses = provision_for_marketting_expenses
                                    line.provision_for_salary = provision_for_salary
                                    line.provision_for_bank_interest = provision_for_bank_interest
                                    line.provision_for_product_insurance = provision_for_product_insurance
                                    line.provision_for_income_tax = provision_for_income_tax
                                    line.provision_for_trade_promotion = provision_for_trade_promotion
                                    line.provision_for_dollar_risk = provision_for_dollar_risk
                                    line.provision_for_sadaqua = provision_for_sadaqua
                                    line.provision_for_sales_courier = provision_for_sales_courier
                                    line.provision_for_house_rent = provision_for_house_rent
                                    line.provision_for_opex = provision_for_opex
                                    line.provision_for_damage_goods = provision_for_damage_goods
                                    line.provision_for_ta_da = provision_for_ta_da
                                    line.provision_for_bad_debt = provision_for_bad_debt
                                    line.provision_for_emp_incentive = provision_for_emp_incentive
                                    line.provision_for_vat = provision_for_vat
                                    line.product_average_price=product_average_price


                                    line.bank_rate=bank_rate
                                    line.bank_payment=bank_payment
                                    line.local_rate=local_rate
                                    line.local_payment=local_payment
                                    line.provision=provision
                                    line.landed_cost=landed_cost
                                    line.cost_price = cost_price
                                    # get_existing.update(line)
                        else:
                            # self.preview_costing.unlink()
                            new_val_line_preview_costing = {
                                'product_id': val_line_values['product_id'],
                                'move_id': val_line_values['move_id'],
                                # 'quantity': val_line_values['quantity'],
                                # 'former_cost': val_line_values['former_cost'],
                                # 'weight': val_line_values['weight'],
                                # 'volume': val_line_values['volume'],
                                'cost_id': val_line_values['cost_id'],
                                'cost_line_id': val_line_values['cost_line_id'],
                                'cd': cd,
                                'at': at,
                                'ait': ait,
                                'df': df,
                                'cf': cf,
                                'transport': transport,
                                'freight': freight,
                                'insurance': insurance,
                                'lc_commision': lc_commision,
                                'lc_vat': lc_vat,
                                'port_demarrage': port_demarrage,
                                'other': other,
                                'vat': vat,
                                'sd': sd,
                                'rd': rd,
                                'atv': atv,
                                'fbc': fbc,
                                'provision_for_warranty_cost': provision_for_warranty_cost,
                                'provision_for_marketting_expenses': provision_for_marketting_expenses,
                                'provision_for_salary': provision_for_salary,
                                'provision_for_bank_interest': provision_for_bank_interest,
                                'provision_for_product_insurance': provision_for_product_insurance,
                                'provision_for_income_tax': provision_for_income_tax,
                                'provision_for_trade_promotion': provision_for_trade_promotion,
                                'provision_for_dollar_risk': provision_for_dollar_risk,
                                'provision_for_sadaqua': provision_for_sadaqua,
                                'provision_for_sales_courier': provision_for_sales_courier,
                                'provision_for_house_rent': provision_for_house_rent,
                                'provision_for_opex': provision_for_opex,
                                'provision_for_damage_goods': provision_for_damage_goods,
                                'provision_for_ta_da': provision_for_ta_da,
                                'provision_for_bad_debt': provision_for_bad_debt,
                                'provision_for_emp_incentive': provision_for_emp_incentive,
                                'provision_for_vat': provision_for_vat,
                                'product_average_price':product_average_price,
                                'bank_rate':bank_rate,
                                'bank_payment':bank_payment,
                                'local_rate':local_rate,
                                'local_payment':local_payment,
                                'provision':provision,
                                'landed_cost':landed_cost,
                                'cost_price': cost_price
                            }
                            # new_all_line_preview_costing.append(new_val_line_preview_costing)
                            self.env['stock.preview.costing'].create(new_val_line_preview_costing)

                        # val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                        # new_val_line_values = {
                        #     'product_id': val_line_values['product_id'],
                        #     'move_id': val_line_values['move_id'],
                        #     'quantity': val_line_values['quantity'],
                        #     'former_cost': val_line_values['former_cost'],
                        #     'weight': val_line_values['weight'],
                        #     'volume': val_line_values['volume'],
                        #     'cost_id': val_line_values['cost_id'],
                        #     'cost_line_id': val_line_values['cost_line_id']
                        # }
                        # # self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                        # self.env['stock.valuation.adjustment.lines'].create(new_val_line_values)
                        # new_val_line_values = {
                        #     'product_id': val_line_values['product_id'],
                        #     'move_id': val_line_values['move_id'],
                        #     'quantity': val_line_values['quantity'],
                        #     # 'probational_sum':val_line_values['probational_sum'],
                        #     'former_cost': val_line_values['former_cost'],
                        #     'weight': val_line_values['weight'],
                        #     'volume': val_line_values['volume'],
                        #     'cost_id': val_line_values['cost_id'],
                        #     'cost_line_id': val_line_values['cost_line_id'],
                        #     'total_bank_payment': val_line_values['total_bank_payment'],
                        #     'total_local_payment': val_line_values['total_local_payment'],
                        # }
                        # print(new_val_line_values)
                        # new_all_val_line_value.append(new_val_line_values)

                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)

                former_cost = val_line_values.get('former_cost', 0.0)
                former_cost_overseas = val_line_values.get('former_cost_overseas', 0.0)
                former_cost_other = val_line_values.get('former_cost_other', 0.0)
                # total_po=val_line_values.get('total_po',0.0)
                # total_os = val_line_values.get('total_os', 0.0)
                # round this because former_cost on the valuation lines is also rounded
                total_cost += tools.float_round(former_cost, precision_digits=digits) if digits else former_cost

                total_line += 1
            self.preview_costing = new_all_line_preview_costing
            print(new_all_val_line_value)

            for line in cost.cost_lines:
                print(line.name)

                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    # for valuation in new_all_val_line_value:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_current_cost_price':
                            # per_unit = (line.price_unit / total_cost)
                            # value = valuation.former_cost * per_unit
                            for newValuation in new_all_val_line_value:

                                if newValuation['product_id'] == valuation.product_id.id and newValuation[
                                    'cost_line_id'] == valuation.cost_line_id.id:
                                    query = "select bank_payment from account_move_line where move_id={} and product_id={}".format(
                                        self.vendor_bill_id.id, valuation.product_id.id)
                                    self._cr.execute(query=query)
                                    get_bank_payment = self._cr.fetchone()
                                    if line.name.__contains__('Overseas'):
                                        value = ((line.price_unit / former_cost_overseas) * newValuation[
                                            'total_local_payment'])
                                    else:
                                        if get_bank_payment[0] > 0:
                                            # value = ((line.price_unit / former_cost_other) * (newValuation['total_local_payment']+newValuation['total_bank_payment']))
                                            value = ((line.price_unit / newValuation[
                                                'total_bank_payment']) * (
                                                             newValuation['total_local_payment'] + newValuation[
                                                         'total_bank_payment']))
                                        else:
                                            value = (line.price_unit / newValuation['total_local_payment']) * (
                                                    newValuation['total_local_payment'] + newValuation[
                                                'total_bank_payment'])
                            # for newValuation in new_all_val_line_value :
                            #
                            #     if newValuation['product_id']==valuation.product_id.id and newValuation['cost_line_id']==valuation.cost_line_id.id:
                            #         if line.name.__contains__('Overseas'):
                            #             value=((line.price_unit/former_cost_overseas)*newValuation['total_local_payment'])
                            #         else:
                            #             value = ((line.price_unit / former_cost_other) * (newValuation['total_local_payment']+newValuation['total_bank_payment']))
                        else:
                            value = (line.price_unit / total_line)

                        if digits:
                            value = tools.float_round(value, precision_digits=digits, rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        for key, value in towrite_dict.items():
            AdjustementLines.browse(key).write({'additional_landed_cost': value})
        return True

    def apply_probational_cost(self):
        amount = 0.0
        cost_lines = []
        column_name = self.cost_lines.fields_get()
        if self.cost_lines.ids:
            for rec in self.cost_lines:
                query = "select product_id,name,bank_payment,quantity,local_payment from account_move_line where move_id={} and account_internal_type!='payable' and quantity!={} and product_id={}".format(
                    rec.cost_id.vendor_bill_id.id, 0, rec.product_id.id)
                self._cr.execute(query=query)
                get_product = self._cr.fetchone()
                line_price_unit = rec.cd + rec.at + rec.ait + rec.df + rec.cf+rec.transport + rec.freight + rec.insurance + rec.lc_commision + rec.lc_vat + rec.port_demarrage + rec.other+rec.vat+rec.sd+rec.rd+rec.atv+rec.fbc

                get_provisional_product = self.env['probational.attribute.setup'].search(
                    [('product_id', '=', rec.product_id.product_tmpl_id.id)])
                for provisional in get_provisional_product:
                    for key in column_name.keys():
                        column_string = self.cost_lines.fields_get()[key]['string']
                        if str(column_string).upper() == str(provisional.probational_product_id.name).upper():
                            bank_amount = get_product[2] * self.env.ref('base.main_company').currency_id.rate * \
                                          get_product[3]
                            local_amount = get_product[4] * self.env.ref(
                                'base.main_company').currency_id.local_currency * get_product[3]
                            rec[key] = (line_price_unit + bank_amount + local_amount) * (provisional.percentage / 100)
                line_landed_cost = rec.cd + rec.at + rec.ait + rec.df + rec.cf + rec.transport + rec.freight \
                                   + rec.insurance + rec.lc_commision + rec.lc_vat + rec.port_demarrage + rec.other + rec.vat + rec.sd + rec.rd + rec.atv + rec.fbc + rec.provision_for_warranty_cost + \
                                   rec.provision_for_marketting_expenses + rec.provision_for_salary + rec.provision_for_bank_interest + \
                                   rec.provision_for_product_insurance + rec.provision_for_income_tax + rec.provision_for_trade_promotion + \
                                   rec.provision_for_dollar_risk + rec.provision_for_sadaqua + rec.provision_for_sales_courier + rec.provision_for_house_rent + \
                                   rec.provision_for_opex + rec.provision_for_damage_goods + rec.provision_for_ta_da + rec.provision_for_bad_debt + rec.provision_for_emp_incentive + rec.provision_for_vat
                rec.price_unit = line_landed_cost

    def button_print_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                 'company_id': self.company_id.id,
                 'invoice_id': self.vendor_bill_id.id
            },
        }
        print('data is', data)
        return self.env.ref('usl_foreign_purchase_smart.foreign_costing_report').report_action(
            self, data=data)
        # return self.env.ref('usl_foreign_purchase_smart.foreign_costing_report').report_action(self)


class InheritStockValuationAdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    # cd_new = fields.Float(string="CD New Value")
    # cd = fields.Float(string="Customs Duty (CD)")
    #
    # at_new = fields.Float(string="AT New Value")
    # at = fields.Float(string="AT")
    # ait_new = fields.Float(string="AIT New Value")
    # ait = fields.Float(string="AIT")
    # df_new = fields.Float(string="DF New Value")
    # df = fields.Float(string="DF")
    # cf_new = fields.Float(string="C&F and Cleaning New Value")
    # cf = fields.Float(string="C&F and Cleaning Mics")
    #
    # transport = fields.Float(string="Transport Charges")
    # freight_new = fields.Float(string="Freight Charge New Value")
    # freight = fields.Float(string="Freight Charges")
    # insurance_new = fields.Float(string="Insurance New Value")
    # insurance = fields.Float(string="Insurance")
    # lc_commision_new = fields.Float(string="L/C Commision New Value")
    # lc_commision = fields.Float(string="L/C Commision")
    # lc_vat_new = fields.Float(string="L/C Vat New Value")
    # lc_vat = fields.Float(string="LC VAT")
    # port_demarrage_new = fields.Float(string="Port Damarage New Value")
    # port_demarrage = fields.Float(string="Port Damarage")
    # other_new = fields.Float(string="Other New Value")
    # other = fields.Float(string="Other")
    #
    # provision_for_warranty_cost = fields.Float(string="Provision For Warranty Cost")
    # provision_for_marketting_expenses = fields.Float(string="Provision For Marketting Expenses")
    # provision_for_salary = fields.Float(string="Provision For Salary")
    # provision_for_bank_interest = fields.Float(string="Provision For Bank Interest")
    # provision_for_product_insurance = fields.Float(string="Provision For Product Insurance")
    # provision_for_income_tax = fields.Float(string="Provision For Income Tax")
    # provision_for_trade_promotion = fields.Float(string="Provision For Trade Promotion")
    # provision_for_dollar_risk = fields.Float(string="Provision For Dollar Risk")
    # provision_for_sadaqua = fields.Float(string="Provision For Sadaqua")
    # provision_for_sales_courier = fields.Float(string="Provision For Sales Courier")
    # provision_for_house_rent = fields.Float(string="Provision For House Rent")
    # provision_for_opex = fields.Float(string="Provision Other Opex")
    # provision_for_damage_goods = fields.Float(string="Provision For Damage Goods")
    # provision_for_ta_da = fields.Float(string="Provision For TA/DA")
    # provision_for_bad_debt = fields.Float(string="Provision For Bad Debt")

    cd = fields.Float(string="Customs Duty (CD)")
    at = fields.Float(string="Advance Tax (AT)")
    ait = fields.Float(string="Advance Income Tax (AIT)")
    df = fields.Float(string="Document Fee")
    cf = fields.Float(string="C&F and Clearing Mics")
    cf_partner_id = fields.Many2one('res.partner', string='C&F Partner')
    transport = fields.Float(string="Transport Charges")
    transport_partner_id = fields.Many2one('res.partner', string='Transport Partner')
    freight = fields.Float(string="Freight Charges")
    freight_partner_id = fields.Many2one('res.partner', string='Freight Partner')
    insurance = fields.Float(string="Insurance")
    insurance_partner_id = fields.Many2one('res.partner', string='Insurance Partner')
    lc_commision = fields.Float(string="LC Commision")
    lc_commision_partner_id = fields.Many2one('res.partner', string='LC Commision Partner')
    lc_vat = fields.Float(string="LC VAT")
    port_demarrage = fields.Float(string="Port Demurrage")
    other = fields.Float(string="Other")

    vat = fields.Float(string="Value Added Tax (VAT)")
    sd = fields.Float(string="Supplementary Duty (SD)")
    rd = fields.Float(string="Regularity Duty (RD)")
    atv = fields.Float(string="Advance Trade VAT(ATV)")
    fbc = fields.Float(string="Foreign Bank Charge")

    provision_for_warranty_cost = fields.Float(string="Provision For Warranty Cost")
    provision_for_marketting_expenses = fields.Float(string="Provision For Marketing Expenses")
    provision_for_salary = fields.Float(string="Provision For Salary")
    provision_for_bank_interest = fields.Float(string="Provision For Bank Interest")
    provision_for_product_insurance = fields.Float(string="Provision For Product Insurance")
    provision_for_income_tax = fields.Float(string="Provision For Income Tax")
    provision_for_trade_promotion = fields.Float(string="Provision For Trade Promotion")
    provision_for_dollar_risk = fields.Float(string="Provision For Dollar Risk")
    provision_for_sadaqua = fields.Float(string="Provision For Sadaqua")
    provision_for_sales_courier = fields.Float(string="Provision For Sales Courier")
    provision_for_house_rent = fields.Float(string="Provision For House Rent")
    provision_for_opex = fields.Float(string="Provision Other Opex")
    provision_for_damage_goods = fields.Float(string="Provision For Damage Goods")
    provision_for_ta_da = fields.Float(string="Provision For TA/DA")
    provision_for_bad_debt = fields.Float(string="Provision For Bad Debt")

    provision_for_emp_incentive = fields.Float(string="Provision For Emp. Incentive")
    provision_for_vat = fields.Float(string="Provision For Vat")

    # @api.depends('cd', 'at', 'ait', 'df', 'cf', 'freight', 'insurance', 'lc_commision', 'lc_vat', 'port_demarrage',
    #              'other', 'provision_1', 'provision_2')
    # def _new_value(self):
    #     for rec in self:
    #         rec.cd_new=rec.cd+
    def _create_account_move_line(self, move, credit_account_id, debit_account_id, qty_out, already_out_account_id):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        AccountMoveLine = []
        query = """select slcl.partner from stock_valuation_adjustment_lines sval
                left join stock_landed_cost_lines slcl on slcl.id=sval.cost_line_id where sval.id={}""".format(self.id)
        self._cr.execute(query=query)
        partner_id = self._cr.fetchone()
        print(partner_id)
        base_line = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': 0,
            'partner_id': partner_id[0],
        }
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id)
        diff = self.additional_landed_cost
        if diff > 0:
            debit_line['debit'] = diff
            credit_line['credit'] = diff
        else:
            # negative cost, reverse the entry
            debit_line['credit'] = -diff
            credit_line['debit'] = -diff
        AccountMoveLine.append([0, 0, debit_line])
        AccountMoveLine.append([0, 0, credit_line])

        # Create account move lines for quants already out of stock
        if qty_out > 0:
            debit_line = dict(base_line,
                              name=(self.name + ": " + str(qty_out) + _(' already out')),
                              quantity=0,
                              account_id=already_out_account_id)
            credit_line = dict(base_line,
                               name=(self.name + ": " + str(qty_out) + _(' already out')),
                               quantity=0,
                               account_id=debit_account_id)
            diff = diff * qty_out / self.quantity
            if diff > 0:
                debit_line['debit'] = diff
                credit_line['credit'] = diff
            else:
                # negative cost, reverse the entry
                debit_line['credit'] = -diff
                credit_line['debit'] = -diff
            AccountMoveLine.append([0, 0, debit_line])
            AccountMoveLine.append([0, 0, credit_line])

            if self.env.company.anglo_saxon_accounting:
                expense_account_id = self.product_id.product_tmpl_id.get_product_accounts()['expense'].id
                debit_line = dict(base_line,
                                  name=(self.name + ": " + str(qty_out) + _(' already out')),
                                  quantity=0,
                                  account_id=expense_account_id)
                credit_line = dict(base_line,
                                   name=(self.name + ": " + str(qty_out) + _(' already out')),
                                   quantity=0,
                                   account_id=already_out_account_id)

                if diff > 0:
                    debit_line['debit'] = diff
                    credit_line['credit'] = diff
                else:
                    # negative cost, reverse the entry
                    debit_line['credit'] = -diff
                    credit_line['debit'] = -diff
                AccountMoveLine.append([0, 0, debit_line])
                AccountMoveLine.append([0, 0, credit_line])

        return AccountMoveLine




class InheritStockLandedCost(models.Model):
    _name = 'stock.preview.costing'

    product_id = fields.Many2one('product.product', string="Product")
    # partner = fields.Many2one('res.partner', string="Partner")
    # invoice_line_product_id = fields.Integer()
    # invoice_line_product_name = fields.Many2one('product.product', domain=lambda self: self._get_product())
    # cd = fields.Float(string="Customs Duty (CD)")
    # at = fields.Float(string="AT")
    # ait = fields.Float(string="AIT")
    # df = fields.Float(string="DF")
    # cf = fields.Float(string="C&F and Clearing Mics")
    # transport = fields.Float(string="Transport Charges")
    # freight = fields.Float(string="Freight Charges")
    #
    # insurance = fields.Float(string="Insurance")
    # lc_commision = fields.Float(string="L/C Commision")
    # lc_vat = fields.Float(string="LC VAT")
    # port_demarrage = fields.Float(string="Port Demarrage")
    # other = fields.Float(string="Other")
    # provision_for_warranty_cost = fields.Float(string="Provision For Warranty Cost")
    # provision_for_marketting_expenses = fields.Float(string="Provision For Maeketting Expenses")
    # provision_for_salary = fields.Float(string="Provision For Salary")
    # provision_for_bank_interest = fields.Float(string="Provision For Bank Interest")
    # provision_for_product_insurance = fields.Float(string="Provision For Product Insurance")
    # provision_for_income_tax = fields.Float(string="Provision For Income Tax")
    # provision_for_trade_promotion = fields.Float(string="Provision For Trade Promotion")
    # provision_for_dollar_risk = fields.Float(string="Provision For Dollar Risk")
    # provision_for_sadaqua = fields.Float(string="Provision For Sadaqua")
    # provision_for_sales_courier = fields.Float(string="Provision For Sales Courier")
    # provision_for_house_rent = fields.Float(string="Provision For House Rent")
    # provision_for_opex = fields.Float(string="Provision Other Opex")
    # provision_for_damage_goods = fields.Float(string="Provision For Damage Goods")
    # provision_for_ta_da = fields.Float(string="Provision For TA/DA")
    # provision_for_bad_debt = fields.Float(string="Provision For Bad Debt")
    cd = fields.Float(string="Customs Duty (CD)")
    at = fields.Float(string="Advance Tax (AT)")
    ait = fields.Float(string="Advance Income Tax (AIT)")
    df = fields.Float(string="Document Fee")
    cf = fields.Float(string="C&F and Clearing Mics")
    cf_partner_id = fields.Many2one('res.partner', string='C&F Partner')
    transport = fields.Float(string="Transport Charges")
    transport_partner_id = fields.Many2one('res.partner', string='Transport Partner')
    freight = fields.Float(string="Freight Charges")
    freight_partner_id = fields.Many2one('res.partner', string='Freight Partner')
    insurance = fields.Float(string="Insurance")
    insurance_partner_id = fields.Many2one('res.partner', string='Insurance Partner')
    lc_commision = fields.Float(string="LC Commision")
    lc_commision_partner_id = fields.Many2one('res.partner', string='LC Commision Partner')
    lc_vat = fields.Float(string="LC VAT")
    port_demarrage = fields.Float(string="Port Demurrage")
    other = fields.Float(string="Other")

    vat = fields.Float(string="Value Added Tax (VAT)")
    sd = fields.Float(string="Supplementary Duty (SD)")
    rd = fields.Float(string="Regularity Duty (RD)")
    atv = fields.Float(string="Advance Trade VAT(ATV)")
    fbc = fields.Float(string="Foreign Bank Charge")

    provision_for_warranty_cost = fields.Float(string="Provision For Warranty Cost")
    provision_for_marketting_expenses = fields.Float(string="Provision For Marketing Expenses")
    provision_for_salary = fields.Float(string="Provision For Salary")
    provision_for_bank_interest = fields.Float(string="Provision For Bank Interest")
    provision_for_product_insurance = fields.Float(string="Provision For Product Insurance")
    provision_for_income_tax = fields.Float(string="Provision For Income Tax")
    provision_for_trade_promotion = fields.Float(string="Provision For Trade Promotion")
    provision_for_dollar_risk = fields.Float(string="Provision For Dollar Risk")
    provision_for_sadaqua = fields.Float(string="Provision For Sadaqua")
    provision_for_sales_courier = fields.Float(string="Provision For Sales Courier")
    provision_for_house_rent = fields.Float(string="Provision For House Rent")
    provision_for_opex = fields.Float(string="Provision Other Opex")
    provision_for_damage_goods = fields.Float(string="Provision For Damage Goods")
    provision_for_ta_da = fields.Float(string="Provision For TA/DA")
    provision_for_bad_debt = fields.Float(string="Provision For Bad Debt")

    provision_for_emp_incentive = fields.Float(string="Provision For Emp. Incentive")
    provision_for_vat = fields.Float(string="Provision For Vat")
    product_average_price=fields.Float(string="Product Average Price")

    cost_id = fields.Many2one(
        'stock.landed.cost', 'Landed Cost',
        required=True, ondelete='cascade')
    cost_line_id = fields.Many2one(
        'stock.landed.cost.lines', 'Cost Line', readonly=True, ondelete='cascade')
    move_id = fields.Many2one('stock.move', 'Stock Move', readonly=True, ondelete='cascade')

    bank_rate=fields.Float(string="Bank Rate")
    bank_payment=fields.Float(string="Bank Payment/Unit")
    local_rate=fields.Float(string="Local Rate")
    local_payment=fields.Float(string="Local Payment/Unit")
    provision=fields.Float(string="Provision/Unit")
    landed_cost=fields.Float(string="Landed Cost/Unit")
    cost_price = fields.Float(string="Cost Price/Unit")
