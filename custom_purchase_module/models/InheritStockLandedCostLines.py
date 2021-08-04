from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError


class InheritStockLandedCostLines(models.Model):
    _inherit='stock.landed.cost.lines'

    partner=fields.Many2one('res.partner',string="Partner")

    @api.onchange('product_id')
    def onchange_product_id(self):
        print(self.product_id.name)
        val = self._context.get('picking_ids')
        if self.product_id.name=='Overseas':
            if self._context.get('picking_ids'):
                val=self._context.get('picking_ids')
                print(val[0][2])
                picking_ids=val[0][2]
                if len(picking_ids)==1:
                    query="""select po.currency_rate from stock_picking sp
                            left join purchase_order po on po.name=sp.origin
                            left join purchase_order_line pol on pol.order_id=po.id
                            where sp.id = {}""".format(picking_ids[0])
                    self._cr.execute(query=query)
                    currency_rate = self._cr.fetchone()
                    query_total_os="""select sum(pol.total_os) from stock_picking sp
                            left join purchase_order po on po.name=sp.origin
                            left join purchase_order_line pol on pol.order_id=po.id
                            where sp.id = {}""".format(picking_ids[0])
                    self._cr.execute(query=query_total_os)
                    total_os = self._cr.fetchone()
                else:
                    query = """select po.currency_rate from stock_picking sp
                                                left join purchase_order po on po.name=sp.origin
                                                left join purchase_order_line pol on pol.order_id=po.id
                                                where sp.id = {}""".format(picking_ids[0])
                    self._cr.execute(query=query)
                    currency_rate = self._cr.fetchone()
                    query_total_os = """select sum(pol.total_os) from stock_picking sp
                                                left join purchase_order po on po.name=sp.origin
                                                left join purchase_order_line pol on pol.order_id=po.id
                                                where sp.id in {}""".format(tuple(picking_ids))
                    self._cr.execute(query=query_total_os)
                    total_os = self._cr.fetchone()
                print(currency_rate[0])
                print(total_os)
                if total_os[0]!=None and currency_rate[0]!=None:
                    price_unit=total_os[0]/currency_rate[0]
                else:
                    price_unit=0.0
                print(total_os)

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


class InheritStockLandedCost(models.Model):
    _inherit='stock.landed.cost'

    def get_valuation_lines(self):
        lines = []
        total_invoice_amount=0.0
        total_invoice_amount_overseas=0.0
        total_invoice_amount_other = 0.0
        # for rec in self.cost_lines:
        #     print(rec.name)
        for move in self.mapped('picking_ids').mapped('move_lines'):
            query="""select pol.total_os,pol.total_po,po.currency_rate,pol.price_unit from stock_move sm
                        left join purchase_order po on po.name=sm.origin
                        left join purchase_order_line pol on pol.order_id=po.id
                        where sm.id ={} and pol.product_id=sm.product_id""".format(move.id)
            self._cr.execute(query=query)
            total_os_po=self._cr.fetchone()
            total_invoice_amount+=total_os_po[3]
            total_invoice_amount_overseas+=0 if total_os_po[0]==None else total_os_po[0]
            total_invoice_amount_other+=0 if total_os_po[1]==None else total_os_po[1]
        for move in self.mapped('picking_ids').mapped('move_lines'):
            query="""select pol.total_os,pol.total_po,po.currency_rate,pol.price_unit from stock_move sm
                        left join purchase_order po on po.name=sm.origin
                        left join purchase_order_line pol on pol.order_id=po.id
                        where sm.id ={} and pol.product_id=sm.product_id""".format(move.id)
            self._cr.execute(query=query)
            total_os_po=self._cr.fetchone()
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            if move.product_id.valuation != 'real_time' or move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel':
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                # 'former_cost': total_invoice_amount/total_os_po[2],
                'former_cost_overseas': total_invoice_amount_overseas/total_os_po[2],
                'former_cost_other': total_invoice_amount_other/total_os_po[2],

                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty,
                'total_os':total_os_po[0]/total_os_po[2],
                'total_po':total_os_po[1]/total_os_po[2]
            }
            lines.append(vals)

        if not lines and self.mapped('picking_ids'):
            raise UserError(_("You cannot apply landed costs on the chosen transfer(s). Landed costs can only be applied for products with automated inventory valuation and FIFO or average costing method."))
        return lines

    def compute_landed_cost(self):
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
            all_val_line_values = cost.get_valuation_lines()

            for val_line_values in all_val_line_values:

                for cost_line in cost.cost_lines:
                    new_val_line_values={}
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
                        'former_cost': val_line_values['former_cost'],
                        'weight': val_line_values['weight'],
                        'volume': val_line_values['volume'],
                        'cost_id': val_line_values['cost_id'],
                        'cost_line_id': val_line_values['cost_line_id'],
                        'total_po':val_line_values['total_po'],
                        'total_os': val_line_values['total_os'],
                    }
                    print(new_val_line_values)
                    new_all_val_line_value.append(new_val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)

                former_cost = val_line_values.get('former_cost', 0.0)
                former_cost_overseas = val_line_values.get('former_cost_overseas', 0.0)
                former_cost_other = val_line_values.get('former_cost_other', 0.0)
                total_po=val_line_values.get('total_po',0.0)
                total_os = val_line_values.get('total_os', 0.0)
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
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            # per_unit = (line.price_unit / total_cost)
                            # value = valuation.former_cost * per_unit
                            for newValuation in new_all_val_line_value:
                                if newValuation['product_id']==valuation.product_id.id and newValuation['cost_line_id']==valuation.cost_line_id.id:
                                    if line.name.__contains__('Overseas'):
                                        value=((line.price_unit/former_cost_overseas)*newValuation['total_os'])
                                    else:
                                        value = ((line.price_unit / former_cost_other) * newValuation['total_po'])
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

    @api.onchange('picking_ids')
    def lineCustomDuty(self):
        # print(self.)
        print(self.picking_ids.ids)
        cost_lines=[]
        if self.picking_ids.ids:
            if len(self.picking_ids.ids)==1:
                picking_ids=list(self.picking_ids.ids)
                picking_ids.append(0)
                print(tuple(picking_ids))
            else:
                picking_ids=self.picking_ids.ids
            query="""select aml.product_id,pt.name,aml.price_subtotal,phcl.assessable_rate,phcl.tax_type_id,pt.categ_id from stock_picking sp
                    left join account_move am on am.invoice_origin=sp.origin
                    left join account_move_line aml on aml.move_id=am.id
                    left join product_product pp on pp.id=aml.product_id 
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join product_hs_code phc on phc.id=pt.product_hs_code_id 
                    left join product_hs_code_line phcl on phcl.hs_code_line_id=phc.id
                    where sp.id in {} and aml.price_subtotal!=0 and aml.account_root_id=49049 and pt.product_hs_code_id!=0""".format(tuple(picking_ids))
            print(query)
            self._cr.execute(query=query)
            result=self._cr.fetchall()



            for res in result:
                res_id='product.category,'+str(res[5])
                query = """select value_reference from ir_property where name = 'property_stock_account_input_categ_id' and company_id={}""".format(self.env.user.company_id.id )
                self._cr.execute(query=query)
                account_id=self._cr.fetchone()
                account_id=account_id[0].split(',')
                custom_duty_amount=(res[2]*res[3])/100
                vals=(0,0,{
                    'product_id': res[4],
                    'partner': 0,
                    'name': res[1],
                    'account_id': int(account_id[1]),
                    'split_method': "by_current_cost_price",
                    'price_unit': custom_duty_amount,
                })
                cost_lines.append(vals)
            print(cost_lines)
            self.update({
                'cost_lines': cost_lines
            })

        # products=self.env['stock.move.line'].search([('picking_id','in',self.picking_ids.ids)])
        #
        # for pro_id in products:
        #
        #     if pro_id.product_id.product_tmpl_id.product_hs_code_id.id:
        #         print('product:',pro_id.product_id.product_tmpl_id)
        #         productwise_subtotal=self.env['']
        #         hs_assessable_rate=self.env['product.hs.code'].search([('id','=',pro_id.product_id.product_tmpl_id.product_hs_code_id.id)]).hs_code_line.assessable_rate
        #
        # print(products)

    def apply_probational_cost(self):

        cost_lines = []
        query="""select product_id,name,price_unit,account_id,partner,id from stock_landed_cost_lines where id in {}""".format(tuple(self.cost_lines.ids))
        self._cr.execute(query=query)
        existing_item = self._cr.fetchall()
        for ei in existing_item:
            vals =(0,0, {

                'product_id': ei[0],
                'partner': ei[4],
                'name': ei[1],
                'account_id': ei[3],
                'split_method': "by_current_cost_price",
                'price_unit': ei[2],
            })
            cost_lines.append(vals)
        print(cost_lines)
        self.cost_lines.unlink()


        if self.picking_ids:
            val = self.picking_ids.ids
            print(val)
            picking_ids =self.picking_ids.ids
            if len(picking_ids) == 1:
                query = """select po.currency_rate from stock_picking sp
                                   left join purchase_order po on po.name=sp.origin
                                   left join purchase_order_line pol on pol.order_id=po.id
                                   where sp.id = {}""".format(picking_ids[0])
                self._cr.execute(query=query)
                currency_rate = self._cr.fetchone()
                query_total_unit_price = """select sum(po.amount_total) from stock_picking sp
                                   left join purchase_order po on po.name=sp.origin

                                   where sp.id = {}""".format(picking_ids[0])
                self._cr.execute(query=query_total_unit_price)
                total_unit_price = self._cr.fetchone()
            else:
                query = """select po.currency_rate from stock_picking sp
                                                       left join purchase_order po on po.name=sp.origin
                                                       left join purchase_order_line pol on pol.order_id=po.id
                                                       where sp.id = {}""".format(picking_ids[0])
                self._cr.execute(query=query)
                currency_rate = self._cr.fetchone()
                query_total_unit_price = """select sum(po.amount_total) from stock_picking sp
                                                       left join purchase_order po on po.name=sp.origin

                                                       where sp.id in {}""".format(tuple(picking_ids))
                self._cr.execute(query=query_total_unit_price)
                total_unit_price = self._cr.fetchone()
            # print(total_amount)
            print(total_unit_price[0])

        query = """select pp.id,pt.name,pt.percentage from product_template pt
                         left join product_product pp on pp.product_tmpl_id=pt.id where pt.probational_cost_ok=true"""
        self._cr.execute(query=query)
        probational_item = self._cr.fetchall()
        total=0


        for pi in probational_item:
            count = 0
            for cl in cost_lines:
                if cl[2]['product_id']==pi[0]:
                    count+=1
            if count==0:
                total=cl[2]['price_unit']
                vals=(0,0,{

                    'product_id':pi[0],
                    'partner':0,
                    'name':pi[1],
                    'account_id':existing_item[0][3],
                    'split_method':"by_current_cost_price",
                    'price_unit':0 if pi[2]==None else (total+total_unit_price[0])*(pi[2]/100),
                })
                cost_lines.append(vals)
            # else:
            #     # total = cl[2]['price_unit']
            #     cl[2]['price_unit']=
                # cl[2]['price_unit']=(total+total_unit_price[0])*(pi[2]/100)


        print(cost_lines)

        self.update({
            'cost_lines':cost_lines
        })

        # print(self.cost_lines.ids)

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


