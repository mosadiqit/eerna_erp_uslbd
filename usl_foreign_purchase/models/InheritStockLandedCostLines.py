from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import date,datetime
# from soupsieve.util import upper


class InheritStockLandedCostLines(models.Model):
    _inherit='stock.landed.cost.lines'

    partner=fields.Many2one('res.partner',string="Partner")
    invoice_line_product_id=fields.Integer()
    invoice_line_product_name=fields.Many2one('product.product',domain=lambda self:self._get_product())

    def _get_product(self):
        if len(self)>0:
            for rec in self:
                if rec.invoice_line_product_id==None:
                    rec.invoice_line_product_name=None
                else:
                    rec.invoice_line_product_name=rec.invoice_line_product_id


    @api.onchange('product_id')
    def onchange_product_id(self):
        print(self.product_id.name)
        price_unit=0.0
        val = self._context.get('picking_ids')
        if self.product_id:
            if self.product_id.name.__contains__('Overseas'):
                if self._context.get('picking_ids'):
                    val=self._context.get('picking_ids')
                    print(val[0][2])
                    picking_ids=val[0][2]
                    if len(picking_ids)==1:
                        # query="""select po.currency_rate from stock_picking sp
                        #         left join foreign_purchase_order po on po.name=sp.origin
                        #         left join foreign_purchase_order_line pol on pol.order_id=po.id
                        #         where sp.id = {}""".format(picking_ids[0])
                        # self._cr.execute(query=query)
                        # currency_rate = self._cr.fetchone()
                        currency_rate = self.env.ref('base.main_company').currency_id.rate
                        query_total_bank="""select sum(aml.total_local_payment) from stock_picking sp                            
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
                    if total_bank_payment[0]!=None and currency_rate!=None:
                        price_unit=total_bank_payment[0]*currency_rate
                    else:
                        price_unit=0.0
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
    _inherit='stock.landed.cost'

    preview_costing = fields.One2many('stock.preview.costing', 'cost_id', 'Preview Costing',
                                      states={'done': [('readonly', True)]})
    button_state = fields.Selection([
        ('cd', 'CD'),
        ('probation', 'Probation'),
        ('compute', 'Compute'),
    ], 'Incoterms', default='cd')
    vendor_bill_id_new=fields.Many2one('account.move',string='Foreign vendor bill')

    @api.onchange('vendor_bill_id')
    def test(self):
        print("changed")
    def button_validate_foreign(self):
        print(self.env.user)
        print(self.env.user.company_id)
        # print(self.env.user.context)
        total_expense=0.0
        val_list = []
        line_ids = []
        for line in self.cost_lines:
            credit_account_id=self.env['product.hs.code.line'].search([('tax_type_id','=',line.product_id.id)]).account_id
            hs_code_line_partner=self.env['product.hs.code.line'].search([('tax_type_id','=',line.product_id.id)]).partner_id
            debit_account_id = line.product_id.product_tmpl_id.categ_id.property_stock_account_input_categ_id.id
            if line.product_id.product_tmpl_id.landed_cost_ok==True:
                if credit_account_id>0:
                    # if len(line.partner)>0:
                    total_expense+=line.price_unit
                    val=(0,0,{
                        # 'partner_id':line.partner.id if len(line.partner)>0 else hs_code_line_partner,
                        'partner_id':line.partner.id if len(line.partner)>0 else None,
                        'branch_id':self.env['res.users'].search([('id','=',self.env.user.id)]).branch_id.id,
                        'currency_id':False,
                        'debit':0,
                        'credit':line.price_unit,
                        'quantity':0,
                        'discount':0,
                        'sequence':10,
                        # 'account_id':self.env['account.account'].search([('root_id','=',50049),('company_id','=',self.env.user.company_id.id)]).id,
                        'account_id':credit_account_id,
                        'parent_state':'draft',
                        'product_id': line.product_id.id

                    })
                    line_ids.append(val)
                    # val_list.append(val)
                    val = (0, 0, {
                        # 'partner_id': line.partner.id if len(line.partner)>0 else hs_code_line_partner,
                        'partner_id': line.partner.id if len(line.partner)>0 else None,
                        'branch_id': self.env['res.users'].search([('id', '=', self.env.user.id)]).branch_id.id,
                        'currency_id': False,
                        'debit': 0,
                        'credit': line.price_unit,
                        'quantity': 0,
                        'discount': 0,
                        'sequence': 10,
                        # 'account_id': self.env['account.account'].search(
                        #     [('root_id', '=', 50049), ('company_id', '=', self.env.user.company_id.id)]).id,
                        'account_id': debit_account_id,
                        'parent_state': 'draft',
                        'product_id': line.product_id.id
                    })
                    line_ids.append(val)
                else:
                    return {
                        'warning': {
                            'title': 'Warning!',
                            # 'message': "Account is not set for product="+rec.name+" & Column="+cd_product.tax_type_id.name}
                            'message': "Account is not set for product"}
                    }
            if line.product_id.product_tmpl_id.probational_cost_ok == True:
                provision_credit_account_id = line.product_id.product_tmpl_id.property_account_expense_id
                if credit_account_id > 0:
                    # if len(line.partner)>0:
                    total_expense += line.price_unit
                    val = (0, 0, {
                        'partner_id': None,
                        'branch_id': self.env['res.users'].search([('id', '=', self.env.user.id)]).branch_id.id,
                        'currency_id': False,
                        'debit': 0,
                        'credit': line.price_unit,
                        'quantity': 0,
                        'discount': 0,
                        'sequence': 10,
                        # 'account_id':self.env['account.account'].search([('root_id','=',50049),('company_id','=',self.env.user.company_id.id)]).id,
                        'account_id': provision_credit_account_id,
                        'parent_state': 'draft',
                        'product_id': line.product_id.id

                    })
                    line_ids.append(val)
                    # val_list.append(val)
                    val = (0, 0, {
                        'partner_id': None,
                        'branch_id': self.env['res.users'].search([('id', '=', self.env.user.id)]).branch_id.id,
                        'currency_id': False,
                        'debit': 0,
                        'credit': line.price_unit,
                        'quantity': 0,
                        'discount': 0,
                        'sequence': 10,
                        # 'account_id': self.env['account.account'].search(
                        #     [('root_id', '=', 50049), ('company_id', '=', self.env.user.company_id.id)]).id,
                        'account_id': debit_account_id,
                        'parent_state': 'draft',
                        'product_id': line.product_id.id
                    })
                    line_ids.append(val)
                else:
                    return {
                        'warning': {
                            'title': 'Warning!',
                            # 'message': "Account is not set for product="+rec.name+" & Column="+cd_product.tax_type_id.name}
                            'message': "Account is not set for product"}
                    }
        if len(line_ids)>0:
            # val = (0, 0, {
            #     # 'partner_id': line.partner.id,
            #     'branch_id': self.env['res.users'].search([('id', '=', self.env.user.id)]).branch_id.id,
            #     'currency_id': False,
            #     'debit': total_expense,
            #     'credit': 0,
            #     'quantity': 0,
            #     'discount': 0,
            #     'sequence': 10,
            #     'account_id': self.env['account.account'].search(
            #         [('root_id', '=', 50048), ('company_id', '=', self.env.user.company_id.id)]).id,
            #     'parent_state': 'draft'
            # })
            # line_ids.append(val)
            val={
                'amount_total':total_expense,
                'amount_total_signed': total_expense,
                'branch_id':self.env['res.users'].search([('id', '=', self.env.user.id)]).branch_id.id,
                'date':date.today(),
                'journal_id':34,
                'currency_id':self.env.ref('base.main_company').currency_id.id,
                'line_ids':line_ids,
                'ref':self.name,
                'state':'draft'

            }
            val_list.append(val)
            account_move=self.env['account.move']
            account_move=account_move.create(val_list)
            # account_move.state='posted'
            account_move.post()
            # account_move.execute( 'account.move', 'post', [[account_move.id], {'state': "posted"}])
            # for line in account_move.line_ids:
            #     line.parent_state='posted'
            # account_move.write(val_list)

        active_model = self.env.context.get('active_model')
        print(active_model)
        for line in self.cost_lines:
            line.partner=None

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
                total_length=len(cost.valuation_adjustment_lines)
                per_line_bank_payment=0.0
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
                #     remaining_qty=0.0
                #     for qty in res:
                #         if qty[1]==line.product_id.id:
                #             remaining_qty=qty[0]
                    # remaining_qty=res[0]

                    # remaining_qty=
                    # remaining_qty=line.move_id.stock_valuation_layer_ids.mapped('remaining_qty')
                # else:
                remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                linked_layer = line.move_id.stock_valuation_layer_ids[:1]

                # Prorate the value at what's still in stock
                product = line.move_id.product_id
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
                if product.cost_method == 'average' and not float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
                    # if active_model == 'foreign.purchase.order':
                        # changeable_standard_price=product.with_context(force_company=self.company_id.id).sudo().changeable_standard_price
                    product.with_context(
                        force_company=self.company_id.id).sudo().previous_standard_price = product.with_context(
                        force_company=self.company_id.id).sudo().standard_price
                    product.with_context(force_company=self.company_id.id).sudo().changeable_standard_price += cost_to_add / product.quantity_svl
                    product.with_context(force_company=self.company_id.id).sudo().standard_price=product.with_context(force_company=self.company_id.id).sudo().changeable_standard_price
                    # else:
                    #     product.with_context(force_company=self.company_id.id).sudo().standard_price += cost_to_add / product.quantity_svl

                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                # if active_model == 'foreign.purchase.order':
                if line.move_id._is_in_foreign():
                    qty_out = remaining_qty- remaining_qty
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
                    all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()
        return True

    def apply_cd_cost(self):
        # self.button_state = 'probation'
        self.cost_lines=[(5,0,0)]
        cd_cost_set = set()
        for initial in self:
            for rec in initial.picking_ids.move_lines:
                cd_cost_lines = []
                cd_lines = self.env['product.product'].search([('id', '=', rec.product_id.id)])
                cd_product_lines = self.env['product.template'].search([('id', '=', cd_lines.product_tmpl_id.id)])
                query = """select aml.bank_payment,aml.quantity,aml.product_id from account_move am 
                                left join account_move_line aml on aml.move_id = am.id                                
    	                       where  am.name = '{}' and aml.product_id = {}""".format(
                    initial.vendor_bill_id.name, rec.product_id.id)
                self._cr.execute(query)
                result = self._cr.fetchone()
                print(result)
                for cd_rec in cd_product_lines.product_hs_code_id.hs_code_line:

                    # if cd_rec.tax_type_id.id not in cd_cost_set:
                    print(cd_rec.assessable_rate)
                    print(self.env.ref('base.main_company').currency_id.rate)
                    vals = {
                        'product_id': cd_rec.tax_type_id.id,
                        'partner':cd_rec.partner_id.id,
                        'name': cd_rec.tax_type_id.name,
                        'split_method': 'by_current_cost_price',
                        'price_unit': ((result[0] * self.env.ref('base.main_company').currency_id.rate * cd_rec.assessable_rate) / 100)*result[1],
                        'invoice_line_product_id':result[2],
                        'invoice_line_product_name':result[2],
                    }
                    # cd_cost_set.add(cd_rec.tax_type_id.id)
                    cd_cost_lines.append((0, 0, vals))
                    # else:
                    #     for cd_product in cd_cost_lines[1::]:
                    #         if cd_product[2]['product_id'] == cd_rec.tax_type_id.id:
                    #             price = ((result[0] * self.env.ref(
                    #                 'base.main_company').currency_id.rate * cd_rec.assessable_rate) / 100)*result[1]
                    #             cd_product[2]['price_unit'] += price
                initial.cost_lines = cd_cost_lines



    def get_valuation_lines_foreign(self):
        lines = []
        total_invoice_amount=0.0
        total_invoice_amount_overseas=0.0
        total_invoice_amount_other = 0.0
        # for rec in self.cost_lines:
        #     print(rec.name)
        for move in self.picking_ids.move_lines:
            # query = """select aml.total_bank_payment,aml.total_local_payment,aml.price_unit,pol.invoiced_uom_qty from stock_move sm
            #                         left join foreign_purchase_order po on po.name=sm.origin
            #                         left join foreign_purchase_order_line pol on pol.order_id=po.id
            #                         left join account_move am on am.invoice_origin=po.name
            #                         left join account_move_line aml on aml.move_id=am.id
            #                         where sm.id ={} and aml.product_id=sm.product_id""".format(move.id)
            query = """select aml.total_bank_payment,aml.total_local_payment,aml.price_unit,aml.quantity from stock_move sm
                                    left join account_move am on am.invoice_origin=sm.origin
                                    left join account_move_line aml on aml.move_id=am.id
                                    where sm.id = {} and aml.move_id={} and aml.account_internal_type!='payable' and sm.product_id = aml.product_id""".format(move.id,self.vendor_bill_id.id)

            self._cr.execute(query=query)
            total_bank_local = self._cr.fetchone()
            total_invoice_amount += total_bank_local[2]
            total_invoice_amount_overseas += 0 if total_bank_local[1] == None else total_bank_local[1]
            total_invoice_amount_other += 0 if total_bank_local[0] == None else total_bank_local[0]
        # for move in self.mapped('picking_ids').mapped('move_lines'):
        #     query="""select aml.total_bank_payment,aml.total_local_payment,aml.price_unit from stock_move sm
        #                 left join foreign_purchase_order po on po.name=sm.origin
        #                 left join foreign_purchase_order_line pol on pol.order_id=po.id
        #                 left join account_move am on am.invoice_origin=po.name
        #                 left join account_move_line aml on aml.move_id=am.id
        #                 where sm.id ={} and pol.product_id=sm.product_id""".format(move.id)
        #     self._cr.execute(query=query)
        #     total_os_po=self._cr.fetchone()
        #     total_invoice_amount+=total_os_po[3]
        #     total_invoice_amount_overseas+=0 if total_os_po[0]==None else total_os_po[0]
        #     total_invoice_amount_other+=0 if total_os_po[1]==None else total_os_po[1]
        # for move in self.mapped('picking_ids').mapped('move_lines'):
        #     query="""select pol.total_os,pol.total_po,po.currency_rate,pol.price_unit from stock_move sm
        #                 left join foreign_purchase_order po on po.name=sm.origin
        #                 left join foreign_purchase_order_line pol on pol.order_id=po.id
        #                 where sm.id ={} and pol.product_id=sm.product_id""".format(move.id)
        #     self._cr.execute(query=query)
        #     total_os_po=self._cr.fetchone()
        for move in self.picking_ids.move_lines:
            # query = """select aml.total_bank_payment,aml.total_local_payment,aml.price_unit,pol.invoiced_uom_qty from stock_move sm
            #                         left join foreign_purchase_order po on po.name=sm.origin
            #                         left join foreign_purchase_order_line pol on pol.order_id=po.id
            #                         left join account_move am on am.invoice_origin=po.name
            #                         left join account_move_line aml on aml.move_id=am.id
            #                         where sm.id ={} and aml.product_id=sm.product_id""".format(move.id)
                    # " left join account_move am on am.id=aml.move_id" \
                    # " left join foreign_purchase_order fpo on fpo.name=am.invoice_origin" \
                    # " left join res_currency_rate rcr on rcr.currency_id=fpo.currency_id" \

            query = """select aml.total_bank_payment,aml.total_local_payment,aml.price_unit,aml.quantity,aml.company_currency_id from stock_move sm
                                                left join account_move am on am.invoice_origin=sm.origin
                                                left join account_move_line aml on aml.move_id=am.id
                                                where sm.id = {} and aml.move_id={} and aml.account_internal_type!='payable' and sm.product_id = aml.product_id""".format(
                move.id,self.vendor_bill_id.id)
            self._cr.execute(query=query)
            total_bank_local = self._cr.fetchone()
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            # if move.product_id.valuation != 'real_time' or move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel':
            #     continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                 'quantity': total_bank_local[3],
                # 'probational_sum':self._get_sum_provisional_value(move.product_id.id),
                # 'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                # 'former_cost': total_bank_local[0]*self.env.ref('base.main_company').currency_id.rate*total_bank_local[3],
                'former_cost': total_bank_local[0]*self.env.ref('base.main_company').currency_id.rate,
                'former_cost_overseas': total_invoice_amount_overseas*self.env['res.currency.rate'].search([('currency_id','=',total_bank_local[4])]).rate,
                'former_cost_other': total_invoice_amount_other*self.env.ref('base.main_company').currency_id.rate,

                'weight': move.product_id.weight * total_bank_local[3],
                'volume': move.product_id.volume * total_bank_local[3],
                'bank_payment': (total_bank_local[0] / total_bank_local[3]) * self.env.ref(
                    'base.main_company').currency_id.rate,
                'total_bank_payment':total_bank_local[0]*self.env.ref('base.main_company').currency_id.rate,
                'local_payment': (total_bank_local[1] / total_bank_local[3]) * self.env['res.currency'].search(
                    [('id', '=', total_bank_local[4])]).local_currency,
                'total_local_payment':total_bank_local[1]*self.env['res.currency'].search([('id','=',total_bank_local[4])]).local_currency,
            }
            lines.append(vals)

        if not lines and self.mapped('vendor_bill_id.invoice_line_ids'):
            raise UserError(_("You cannot apply landed costs on the chosen transfer(s). Landed costs can only be applied for products with automated inventory valuation and FIFO or average costing method."))
        return lines

    # def _get_sum_provisional_value(self,val=None):
    #     query="select product_tmpl_id from product_product where id={}".format(val)
    #     self._cr.execute(query=query)
    #     product_tmpl_id=self._cr.fetchone()
    #     query="select sum(percentage) from probational_attribute_setup where product_probational_tmpl_id1={}".format(product_tmpl_id[0])
    #     self._cr.execute(query=query)
    #     sum_provisonal_value = self._cr.fetchone()
    #     return sum_provisonal_value[0]

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
            new_all_val_line_value=[]
            all_val_line_values = cost.get_valuation_lines_foreign()
            default_currency_id = self.env.ref('base.main_company').currency_id.id
            bank_rate = self.env['res.currency.rate'].search([('currency_id', '=', default_currency_id)]).rate
            local_rate = self.env.ref('base.main_company').currency_id.local_currency
            cost_preview_array=[]
            for val_line_values in all_val_line_values:
                landed_cost=0
                provision=0
                for cost_line in cost.cost_lines:
                    new_val_line_values = {}
                    if cost_line.invoice_line_product_id==0:

                        print(cost_line.name)
                        val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                        new_val_line_values = {
                            'product_id': val_line_values['product_id'],
                            'move_id': val_line_values['move_id'],
                            'quantity': val_line_values['quantity'],
                            'former_cost': val_line_values['former_cost'],
                            'weight': val_line_values['weight'],
                            'volume': val_line_values['volume'],
                            'cost_id':val_line_values['cost_id'],
                            'cost_line_id':val_line_values['cost_line_id']
                        }
                        # self.env['stock.valuation.adjustment.lines'].create(val_line_values)
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
                            'total_bank_payment':val_line_values['total_bank_payment'],
                            'total_local_payment': val_line_values['total_local_payment'],
                        }
                        print(new_val_line_values)
                        new_all_val_line_value.append(new_val_line_values)




                    else:
                        if cost_line.invoice_line_product_id==val_line_values['product_id']:
                            val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                            new_val_line_values = {
                                'product_id': val_line_values['product_id'],
                                'move_id': val_line_values['move_id'],
                                'quantity': val_line_values['quantity'],
                                'former_cost': val_line_values['former_cost'],
                                'weight': val_line_values['weight'],
                                'volume': val_line_values['volume'],
                                'cost_id': val_line_values['cost_id'],
                                'cost_line_id': val_line_values['cost_line_id']
                            }
                            # self.env['stock.valuation.adjustment.lines'].create(val_line_values)
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
                            bank_rate = bank_rate
                            bank_payment = val_line_values['bank_payment'] if val_line_values['bank_payment'] > 0 else 0
                            local_rate = local_rate
                            local_payment = val_line_values['local_payment'] if val_line_values[
                                                                                    'local_payment'] > 0 else 0
                            if cost_line.product_id.product_tmpl_id.landed_cost_ok==True and not str(cost_line.product_id.product_tmpl_id.name).upper().__contains__("PROVISION"):
                                landed_cost += cost_line.price_unit/val_line_values['quantity']
                            if cost_line.product_id.product_tmpl_id.probational_cost_ok==True:
                                provision += cost_line.price_unit/val_line_values['quantity']

                            # cost_price = bank_payment + local_payment + landed_cost + provision
                get_existing = self.env['stock.preview.costing'].search(
                    [('cost_line_id', '=', val_line_values['cost_line_id']),
                     ('product_id', '=', val_line_values['product_id'])])
                if len(get_existing)>0:
                    for line in get_existing:
                        if line.product_id.id == val_line_values['product_id']:
                            line.product_id = val_line_values['product_id']
                            line.product_average_price = get_product_changable_standard_price
                            line.bank_rate = bank_rate
                            line.bank_payment = bank_payment
                            line.local_rate = local_rate
                            line.local_payment = local_payment
                            line.provision = provision
                            line.landed_cost = landed_cost
                            line.cost_price = bank_payment + local_payment + landed_cost + provision
                else:
                    new_val_line_preview_costing = {
                        'product_id': val_line_values['product_id'],
                        'move_id': val_line_values['move_id'],
                        'cost_id': val_line_values['cost_id'],
                        'cost_line_id': val_line_values['cost_line_id'],
                        'product_average_price': get_product_changable_standard_price,
                        'bank_rate': bank_rate,
                        'bank_payment': bank_payment,
                        'local_rate': local_rate,
                        'local_payment': local_payment,
                        'provision': provision,
                        'landed_cost': landed_cost,
                        'cost_price': bank_payment + local_payment + landed_cost + provision
                    }
                    # new_all_line_preview_costing.append(new_val_line_preview_costing)
                    self.env['stock.preview.costing'].create(new_val_line_preview_costing)




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

            print(new_all_val_line_value)

            for line in cost.cost_lines:
                print(line.name)

                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                # for valuation in new_all_val_line_value:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price':
                            # per_unit = (line.price_unit / total_cost)
                            # value = valuation.former_cost * per_unit
                            for newValuation in new_all_val_line_value :

                                if newValuation['product_id']==valuation.product_id.id and newValuation['cost_line_id']==valuation.cost_line_id.id  :
                                    query="select bank_payment from account_move_line where move_id={} and product_id={}".format(self.vendor_bill_id.id,valuation.product_id.id)
                                    self._cr.execute(query=query)
                                    get_bank_payment=self._cr.fetchone()
                                    if line.name.__contains__('Overseas'):
                                        value=((line.price_unit/former_cost_overseas)*newValuation['total_local_payment'])
                                    else:
                                        if get_bank_payment[0]>0:
                                            # value = ((line.price_unit / former_cost_other) * (newValuation['total_local_payment']+newValuation['total_bank_payment']))
                                            value = ((line.price_unit / newValuation[
                                                    'total_bank_payment']) * (
                                                        newValuation['total_local_payment'] + newValuation[
                                                    'total_bank_payment']))
                                        else:
                                            value=(line.price_unit/newValuation['total_local_payment'])* (newValuation['total_local_payment']+newValuation['total_bank_payment'])
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
        # self.button_state = 'compute'
        amount = 0.0
        # for rec in self.cost_lines:
        #     amount += rec.price_unit
        cost_lines = []
        if self.cost_lines.ids:

            query="""select product_id,name,price_unit,account_id,partner,id,invoice_line_product_id from stock_landed_cost_lines where id in %s"""%str(tuple(self.cost_lines.ids)).replace(',)', ')')
            self._cr.execute(query=query)
            existing_item = self._cr.fetchall()
            for ei in existing_item:
                for rec in self.cost_lines:
                    if ei[0]==rec.id :
                        vals =(0,0, {
                            'product_id': ei[0],
                            'partner': ei[4],
                            'name': ei[1],
                            'account_id': ei[3],
                            'split_method': "by_current_cost_price",
                            'price_unit': ei[2],
                            'invoice_line_product_id':rec.invoice_line_product_id,
                            'invoice_line_product_name': rec.invoice_line_product_id,
                        })
                        cost_lines.append(vals)
            print(cost_lines)
            # self.cost_lines.unlink()


            if self.picking_ids:
                val = self.picking_ids.ids
                print(val)
                picking_ids =self.picking_ids.ids
                if len(picking_ids) == 1:
                    # query = """select po.currency_rate from stock_picking sp
                    #                    left join foreign_purchase_order po on po.name=sp.origin
                    #                    left join foreign_purchase_order_line pol on pol.order_id=po.id
                    #                    where sp.id = {}""".format(picking_ids[0])
                    # self._cr.execute(query=query)
                    # currency_rate = self._cr.fetchone()
                    query_total_unit_price = """select sum(po.amount_total) from stock_picking sp
                                       left join foreign_purchase_order po on po.name=sp.origin
    
                                       where sp.id = {}""".format(picking_ids[0])
                    self._cr.execute(query=query_total_unit_price)
                    total_unit_price = self._cr.fetchone()
                else:
                    # query = """select po.currency_rate from stock_picking sp
                    #                                        left join foreign_purchase_order po on po.name=sp.origin
                    #                                        left join foreign_purchase_order_line pol on pol.order_id=po.id
                    #                                        where sp.id = {}""".format(picking_ids[0])
                    # self._cr.execute(query=query)
                    # currency_rate = self._cr.fetchone()
                    query_total_unit_price = """select sum(po.amount_total) from stock_picking sp
                                                           left join foreign_purchase_order po on po.name=sp.origin
    
                                                           where sp.id in {}""".format(tuple(picking_ids))
                    self._cr.execute(query=query_total_unit_price)
                    total_unit_price = self._cr.fetchone()
                # print(total_amount)
                print(total_unit_price[0])

           # ********************************************* probational item get****************************************************
            query="select product_id,name,bank_payment,quantity,local_payment from account_move_line where move_id={} and account_internal_type!='payable' and quantity!={}".format(self.vendor_bill_id.id,0)
            self._cr.execute(query=query)
            get_products=self._cr.fetchall()
            flag = 0
            for ex in existing_item:

                if  not str(ex[1]).upper().__contains__('PROVISION'):
                    flag=1
                else:
                    flag=0
            if flag==1:
                product_wise_total_amount=dict()
                amount=0
                for line in self.cost_lines:
                    if line.invoice_line_product_id not  in product_wise_total_amount:
                        product_wise_total_amount[line.invoice_line_product_id]=list()
                    # else:
                    #     product_wise_total_amount[line.invoice_line_product_id]=amount+line.price_unit
                for key in product_wise_total_amount:
                    amount = 0
                    for line in self.cost_lines:
                        if line.invoice_line_product_id==key:
                            amount+=line.price_unit
                    product_wise_total_amount[key].append(amount)

                for product in get_products:
                    for key in product_wise_total_amount:
                        if product[0]==int(key):
                            product_tmpl_id=self.env['product.product'].search([('id','=',product[0])]).product_tmpl_id
                            # query="select sum(percentage)  from probational_attribute_setup where product_id={}".format(product_tmpl_id.id)
                            # self._cr.execute(query=query)
                            # get_sum_percentage=self._cr.fetchone()
                            query = "select ps.product_id,pt.name,ps.probational_product_id,ps.percentage  from probational_attribute_setup ps \
                                    left join product_template pt on pt.id=ps.product_id where ps.product_id={}".format(
                                    product_tmpl_id.id)
                            self._cr.execute(query=query)
                            get_provisional_product = self._cr.fetchall()

                            # provisional_product_product=self.env['product.product'].search([('product_tmpl_id','=',provisional_product_id.id)])
                            for line in get_provisional_product:
                                product_id = self.env['product.product'].search(
                                    [('product_tmpl_id', '=', line[0])])
                                provisional_product_id = self.env['product.product'].search(
                                    [('product_tmpl_id', '=', line[2])])
                                vals = (0, 0, {

                                            'product_id':provisional_product_id.id,
                                            'partner':0,
                                            # 'name':product[1].split(':')[1],
                                            'name': provisional_product_id.product_tmpl_id.name,
                                            'account_id':existing_item[0][3],
                                            'split_method':"by_current_cost_price",
                                            'price_unit':((product_wise_total_amount[key][0]+(product[2]*self.env.ref('base.main_company').currency_id.rate*product[3]))+(product[4]*product[3]*self.env.ref('base.main_company').currency_id.local_currency))*(line[3]/100),
                                            # 'price_unit':((product_wise_total_amount[key][0]+(product[4]*product[3]*self.env.ref('base.main_company').currency_id.local_currency)))*(get_sum_percentage[0]/100),
                                            'invoice_line_product_id':product_id.id,
                                            'invoice_line_product_name': product_id.id,
                                            # 'price_unit':0 if pi[2]==None else (total+total_unit_price[0])*(pi[2]/100),
                                        })
                                cost_lines.append(vals)
                self.update({
                    'cost_lines': cost_lines
                })

            if flag==0:
                product_wise_total_amount=dict()
                for line in self.cost_lines:
                    if line.invoice_line_product_id not  in product_wise_total_amount:
                        product_wise_total_amount[line.invoice_line_product_id]=list()
                    # else:
                    #     product_wise_total_amount[line.invoice_line_product_id]=amount+line.price_unit
                for key in product_wise_total_amount:
                    amount = 0
                    for line in self.cost_lines:
                        if line.invoice_line_product_id==key  and not str(line.name).upper().__contains__('PROVISION'):
                            amount+=line.price_unit
                    product_wise_total_amount[key].append(amount)
                provision_update=[]
                for line in self.cost_lines:
                    if line.product_id.product_tmpl_id.probational_cost_ok==True:
                        line.unlink()
                for product in get_products:
                    for key in product_wise_total_amount:
                        if product[0] == int(key):
                            product_tmpl_id = self.env['product.product'].search(
                                [('id', '=', product[0])]).product_tmpl_id
                            # query="select sum(percentage)  from probational_attribute_setup where product_id={}".format(product_tmpl_id.id)
                            # self._cr.execute(query=query)
                            # get_sum_percentage=self._cr.fetchone()
                            query = "select ps.product_id,pt.name,ps.probational_product_id,ps.percentage  from probational_attribute_setup ps \
                                                   left join product_template pt on pt.id=ps.product_id where ps.product_id={}".format(
                                product_tmpl_id.id)
                            self._cr.execute(query=query)
                            get_provisional_product = self._cr.fetchall()

                            # provisional_product_product=self.env['product.product'].search([('product_tmpl_id','=',provisional_product_id.id)])
                            for line in get_provisional_product:
                                product_id = self.env['product.product'].search(
                                    [('product_tmpl_id', '=', line[0])])
                                provisional_product_id = self.env['product.product'].search(
                                    [('product_tmpl_id', '=', line[2])])
                                vals = (0, 0, {

                                    'product_id': provisional_product_id.id,
                                    'partner': 0,
                                    # 'name':product[1].split(':')[1],
                                    'name': provisional_product_id.product_tmpl_id.name,
                                    'account_id': existing_item[0][3],
                                    'split_method': "by_current_cost_price",
                                    'price_unit': ((product_wise_total_amount[key][0] + (
                                                product[2] * self.env.ref('base.main_company').currency_id.rate *
                                                product[3])) + (product[4] * product[3] * self.env.ref(
                                        'base.main_company').currency_id.local_currency)) * (line[3] / 100),
                                    # 'price_unit':((product_wise_total_amount[key][0]+(product[4]*product[3]*self.env.ref('base.main_company').currency_id.local_currency)))*(get_sum_percentage[0]/100),
                                    'invoice_line_product_id': product_id.id,
                                    'invoice_line_product_name': product_id.id,
                                    # 'price_unit':0 if pi[2]==None else (total+total_unit_price[0])*(pi[2]/100),
                                })
                                cost_lines.append(vals)
                self.update({
                    'cost_lines': cost_lines
                })
                # for product in get_products:
                #     for key in product_wise_total_amount:
                #         if product[0]==int(key):
                #             product_tmpl_id=self.env['product.product'].search([('id','=',product[0])]).product_tmpl_id
                #             # query="select sum(percentage)  from probational_attribute_setup where product_id={}".format(product_tmpl_id.id)
                #             # self._cr.execute(query=query)
                #             # get_sum_percentage=self._cr.fetchone()
                #             query = "select ps.product_id,pt.name,ps.probational_product_id,ps.percentage  from probational_attribute_setup ps \
                #                     left join product_template pt on pt.id=ps.product_id where ps.product_id={}".format(
                #                     product_tmpl_id.id)
                #             self._cr.execute(query=query)
                #             get_provisional_product = self._cr.fetchall()
                #
                #             # provisional_product_product=self.env['product.product'].search([('product_tmpl_id','=',provisional_product_id.id)])
                #             for cost_line in self.cost_lines:
                #                 check_existency=0
                #                 for line in get_provisional_product:
                #                     product_id=self.env['product.product'].search(
                #                         [('product_tmpl_id', '=', line[0])])
                #                     provisional_product_id = self.env['product.product'].search(
                #                         [('product_tmpl_id', '=', line[2])])
                #                     if provisional_product_id.id==cost_line.product_id.id and product_id.id==cost_line.invoice_line_product_id and upper(provisional_product_id[0].name).__contains__("PROVISION"):
                #                         val = (1, cost_line.id, {
                #                             'price_unit': ((product_wise_total_amount[key][0]+(product[2]*self.env.ref('base.main_company').currency_id.rate*product[3]))+(product[4]*product[3]*self.env.ref('base.main_company').currency_id.local_currency))*(line[3]/100),
                #                         })
                #                         provision_update.append(val)
                #
                #
                #
                #
                # self.write({
                #     'cost_lines': provision_update
                # })
                # print(cost_lines)


                # get_provisional_product = self._cr.fetchall()
                #
                # product_wise_total_amount = dict()
                # amount = 0
                # for line in self.cost_lines:
                #     if line.invoice_line_product_id not in product_wise_total_amount:
                #         product_wise_total_amount[line.invoice_line_product_id] = list()
                #     # else:
                #     #     product_wise_total_amount[line.invoice_line_product_id]=amount+line.price_unit
                # for product in get_products:
                #     for key in product_wise_total_amount:
                #         amount = 0
                #         for line in self.cost_lines:
                #             if line.invoice_line_product_id == key and not upper(line.name).__contains__('PROVISION'):
                #                 amount += line.price_unit
                #         product_wise_total_amount[key].append(amount)
                #
                #     get_provisional_line=[]
                #     cost_line=self.env['stock.landed.cost.lines']
                #     for ex in self.cost_lines:
                #         if upper(ex.name).__contains__("PROVISION"):
                #             cost_line+=ex
                #             # get_provisional_line.append(ex)
                #     # get_provisional_line=existing_item.conta(lambda x:x[1]=='provision')
                #     provision_update=[]
                #     for pl in cost_line:
                #         # get_id=self.env['stock.landed.cost.lines'].search([('')])
                #         query = "select product_id,name,bank_payment,quantity,local_payment from account_move_line where move_id={} and product_id={} and account_internal_type!='payable' and quantity!={}".format(
                #             self.vendor_bill_id.id,pl.invoice_line_product_id, 0)
                #         self._cr.execute(query=query)
                #         get_products = self._cr.fetchone()
                #         # for product in get_products:
                #         #     if ex[1]=='provision':
                #         product_tmpl_id = self.env['product.product'].search([('id', '=', pl.invoice_line_product_id)]).product_tmpl_id
                #         # query = "select sum(percentage)  from probational_attribute_setup where product_probational_tmpl_id1={}".format(
                #         #     product_tmpl_id.id)
                #         # self._cr.execute(query=query)
                #         # get_sum_percentage = self._cr.fetchone()
                #         query = "select ps.product_id,pt.name,ps.probational_product_id,ps.percentage  from probational_attribute_setup ps \
                #                                           left join product_template pt on pt.id=ps.product_id where ps.product_id={}".format(
                #             product_tmpl_id.id)
                #         self._cr.execute(query=query)
                #         get_provisional_product = self._cr.fetchall()
                #         for line in get_provisional_product:
                #         # if get_provisional_product[0] != None:
                #             for key in product_wise_total_amount:
                #                 if key==pl.invoice_line_product_id:
                #                     val=(1, pl.id, {
                #                         'price_unit': ((product_wise_total_amount[key][0]+(product[2]*self.env.ref('base.main_company').currency_id.rate*product[3]))+(product[4]*product[3]*self.env.ref('base.main_company').currency_id.local_currency))*(line[3]/100),
                #                     })
                #                     provision_update.append(val)
                #
                #
                #     self.write({
                #         'cost_lines': provision_update
                #     })
                #     print(cost_lines)

            # self.update({
            #     'cost_lines':cost_lines
            # })
        else:

            # query = """select product_id,name,price_unit,account_id,partner,id from stock_landed_cost_lines where id in %s""" % str(
            #     tuple(self.cost_lines.ids)).replace(',)', ')')
            # self._cr.execute(query=query)
            # existing_item = self._cr.fetchall()
            total_unit_price=0.0
            if self.picking_ids:
                val = self.picking_ids.ids
                print(val)
                picking_ids =self.picking_ids.ids
                query_total_unit_price = """select sum(po.amount_total) from stock_picking sp
                                                                          left join foreign_purchase_order po on po.name=sp.origin
    
                                                                          where sp.id in %s"""%str(tuple(picking_ids)).replace(',)', ')')
                self._cr.execute(query=query_total_unit_price)
                total_unit_price = self._cr.fetchone()

            query = """select pp.id,pt.name,pt.percentage from product_template pt
                                         left join product_product pp on pp.product_tmpl_id=pt.id where pt.probational_cost_ok=true"""
            self._cr.execute(query=query)
            probational_item = self._cr.fetchall()
            total = 0

            for pi in probational_item:
                count = 0
                for cl in cost_lines:
                    if cl[2]['product_id'] == pi[0]:
                        count += 1
                if count == 0:
                    # total = cl[2]['price_unit']
                    vals = (0, 0, {

                        'product_id': pi[0],
                        'partner': 0,
                        'name': pi[1],
                        'account_id': 0,
                        'split_method': "by_current_cost_price",
                        'price_unit': amount*(pi[2]/100),
                    # if pi[2] == None else (total + total_unit_price[0]) * (pi[2] / 100)
                    })
                    cost_lines.append(vals)
                # else:
                #     # total = cl[2]['price_unit']
                #     cl[2]['price_unit']=
                # cl[2]['price_unit']=(total+total_unit_price[0])*(pi[2]/100)

            print(cost_lines)

            self.update({
                'cost_lines': cost_lines
            })

        print(self.cost_lines.ids)

class InheritStockValuationAdjustmentLines(models.Model):
    _inherit='stock.valuation.adjustment.lines'

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, qty_out, already_out_account_id):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        AccountMoveLine = []
        query="""select slcl.partner from stock_valuation_adjustment_lines sval
                left join stock_landed_cost_lines slcl on slcl.id=sval.cost_line_id where sval.id={}""".format(self.id)
        self._cr.execute(query=query)
        partner_id=self._cr.fetchone()
        print(partner_id)
        base_line = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': 0,
            'partner_id':partner_id[0],
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



