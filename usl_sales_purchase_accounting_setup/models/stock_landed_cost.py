from collections import defaultdict
from datetime import date

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_is_zero

class InheritStockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    def button_validate(self):
        get_company_data=self.env['product.sale.accounting'].search([('company_id','=',self.company_id.id)])
        if get_company_data:
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
                    remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                    linked_layer = line.move_id.stock_valuation_layer_ids[:1]

                    # Prorate the value at what's still in stock
                    cost_to_add = (remaining_qty / line.move_id.product_qty) * line.additional_landed_cost
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
                    if get_company_data.property_cost_method == 'average' and not float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
                        product.with_context(force_company=self.company_id.id).sudo().standard_price += cost_to_add / product.quantity_svl
                    # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                    # in stock.
                    qty_out = 0
                    if line.move_id._is_in():
                        qty_out = line.move_id.product_qty - remaining_qty
                    elif line.move_id._is_out():
                        qty_out = line.move_id.product_qty
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
                        all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()
            return True
        else:
            raise ValidationError(_("Please first set your company accounting setting!!!"))

    def get_valuation_lines(self):
        get_company_data = self.env['product.sale.accounting'].search([('company_id', '=', self.company_id.id)])
        if get_company_data:
            lines = []

            for move in self.mapped('picking_ids').mapped('move_lines'):
                # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
                if get_company_data.property_valuation != 'real_time' or get_company_data.property_cost_method not in ('fifo', 'average') or move.state == 'cancel':
                    continue
                vals = {
                    'product_id': move.product_id.id,
                    'move_id': move.id,
                    'quantity': move.product_qty,
                    'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                    'weight': move.product_id.weight * move.product_qty,
                    'volume': move.product_id.volume * move.product_qty
                }
                lines.append(vals)

            if not lines and self.mapped('picking_ids'):
                raise UserError(_("You cannot apply landed costs on the chosen transfer(s). Landed costs can only be applied for products with automated inventory valuation and FIFO or average costing method."))
            return lines
        else:
            raise ValidationError(_("Please first set your company accounting setting!!!"))


    def button_validate_foreign(self):
        get_company_data = self.env['product.sale.accounting'].search([('company_id', '=', self.company_id.id)])
        if get_company_data:
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
                    remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                    linked_layer = line.move_id.stock_valuation_layer_ids[:1]
                    cost_to_add = (remaining_qty / remaining_qty) * line.additional_landed_cost

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
                    if get_company_data.property_cost_method == 'average' and not float_is_zero(product.quantity_svl,
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
        else:
            raise ValidationError(_("Please first set your company accounting setting!!!"))

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
                    if  get_company_data.property_valuation != 'real_time' or get_company_data.property_cost_method not in ('fifo', 'average') or move.state == 'cancel':
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
                        'former_cost_other': total_invoice_amount_other * self.env.ref('base.main_company').currency_id.rate,

                        'weight': move.product_id.weight * total_bank_local[3],
                        'volume': move.product_id.volume * total_bank_local[3],
                        'bank_payment':(total_bank_local[0]/total_bank_local[3])* self.env.ref('base.main_company').currency_id.rate,
                        'total_bank_payment': total_bank_local[0] * self.env.ref('base.main_company').currency_id.rate,
                        'local_payment':(total_bank_local[1]/total_bank_local[3])*self.env['res.currency'].search(
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
