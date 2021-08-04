from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class InheritAccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_computed_account(self):
        self.ensure_one()
        self = self.with_context(force_company=self.move_id.journal_id.company_id.id)

        if not self.product_id:
            return

        fiscal_position = self.move_id.fiscal_position_id
        accounts = self.get_sales_purchase_accounts(fiscal_pos=fiscal_position)
        if self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            return accounts['income']
        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            # return accounts['expense']
            return accounts['stock_input']

    def get_sales_purchase_accounts(self, fiscal_pos=None):
        print('****')
        get_all_account=self.env['product.sale.accounting'].search([('company_id','=',self.env.user.company_id.id)],limit=1)
        if get_all_account:
            expense_account=get_all_account.expense_account.account_account_id
            income_account=get_all_account.income_account.account_account_id
            stock_input = get_all_account.stock_input_account.account_account_id
            stock_output=get_all_account.stock_output_account.account_account_id
            stock_valuation=get_all_account.stock_valuation_account.account_account_id
            # if  income_account==None or income_account==0:
            #     raise ValidationError(_('Income account is not set for your company, Please set it first for further procedure!!!'))
            # if  expense_account==None or expense_account==0:
            #     raise ValidationError(_('Expense account is not set for your company, Please set it first for further procedure!!!'))
            # if stock_input == None or stock_input==0:
            #     raise ValidationError(
            #         _('Stock input account is not set for your company, Please set it first for further procedure!!!'))
            # if  stock_output==None or stock_output==0:
            #     raise ValidationError(_('Stock output account is not set for your company, Please set it first for further procedure!!!'))
            #
            # if  stock_valuation==None or stock_valuation==0:
            #     raise ValidationError(_('Stock valuation account is not set for your company, Please set it first for further procedure!!!'))
            accounts={'expense':self.env['account.account'].search([('id','=',expense_account),('company_id','=',get_all_account.company_id.id)]),
                      'income':self.env['account.account'].search([('id','=',income_account),('company_id','=',get_all_account.company_id.id)]),
                      'stock_input':self.env['account.account'].search([('id','=',stock_input),('company_id','=',get_all_account.company_id.id)]),
                      'stock_output':self.env['account.account'].search([('id','=',stock_output),('company_id','=',get_all_account.company_id.id)]),
                      'stock_valuation':self.env['account.account'].search([('id','=',stock_valuation),('company_id','=',get_all_account.company_id.id)])}
            if not fiscal_pos:
                fiscal_pos = self.env['account.fiscal.position']
            return fiscal_pos.map_accounts(accounts)
        else:
            raise UserError(_("Please set accounting for your company!!!"))

# class InheritAccountMove(models.Model):
#     _inherit = "account.move"
#
#     def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
#         property_valuation=self.env['product.sale.accounting'].search([('company_id','=',self.env.user.company_id.id)],limit=1)
#         if property_valuation :
#             lines_vals_list = []
#             for move in self:
#                 if not move.is_sale_document(include_receipts=True) or not move.company_id.anglo_saxon_accounting:
#                     continue
#
#                 for line in move.invoice_line_ids:
#
#                     # Filter out lines being not eligible for COGS.
#                     if line.product_id.type != 'product' or property_valuation.property_valuation != 'real_time':
#                         continue
#
#                     # Retrieve accounts needed to generate the COGS.
#                     accounts = (
#                         line.get_sales_purchase_accounts(fiscal_pos=move.fiscal_position_id)
#                     )
#                     debit_interim_account = accounts['stock_output']
#                     credit_expense_account = accounts['expense']
#                     if not debit_interim_account or not credit_expense_account:
#                         continue
#
#                     # Compute accounting fields.
#                     sign = -1 if move.type == 'out_refund' else 1
#                     price_unit = line._stock_account_get_anglo_saxon_price_unit()
#                     balance = sign * line.quantity * price_unit
#
#                     # Add interim account line.
#                     lines_vals_list.append({
#                         'name': line.name[:64],
#                         'move_id': move.id,
#                         'product_id': line.product_id.id,
#                         'product_uom_id': line.product_uom_id.id,
#                         'quantity': line.quantity,
#                         'price_unit': price_unit,
#                         'debit': balance < 0.0 and -balance or 0.0,
#                         'credit': balance > 0.0 and balance or 0.0,
#                         'account_id': debit_interim_account.id,
#                         'exclude_from_invoice_tab': True,
#                         'is_anglo_saxon_line': True,
#                     })
#
#                     # Add expense account line.
#                     lines_vals_list.append({
#                         'name': line.name[:64],
#                         'move_id': move.id,
#                         'product_id': line.product_id.id,
#                         'product_uom_id': line.product_uom_id.id,
#                         'quantity': line.quantity,
#                         'price_unit': -price_unit,
#                         'debit': balance > 0.0 and balance or 0.0,
#                         'credit': balance < 0.0 and -balance or 0.0,
#                         'account_id': credit_expense_account.id,
#                         'analytic_account_id': line.analytic_account_id.id,
#                         'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                         'exclude_from_invoice_tab': True,
#                         'is_anglo_saxon_line': True,
#                     })
#             return lines_vals_list
#         else:
#             raise ValidationError(_("Please first set your company accounting setting!!!"))
#
#     def _stock_account_prepare_anglo_saxon_in_lines_vals(self):
#         ''' Prepare values used to create the journal items (account.move.line) corresponding to the price difference
#          lines for vendor bills.
#
#         Example:
#
#         Buy a product having a cost of 9 and a supplier price of 10 and being a storable product and having a perpetual
#         valuation in FIFO. The vendor bill's journal entries looks like:
#
#         Account                                     | Debit | Credit
#         ---------------------------------------------------------------
#         101120 Stock Interim Account (Received)     | 10.0  |
#         ---------------------------------------------------------------
#         101100 Account Payable                      |       | 10.0
#         ---------------------------------------------------------------
#
#         This method computes values used to make two additional journal items:
#
#         ---------------------------------------------------------------
#         101120 Stock Interim Account (Received)     |       | 1.0
#         ---------------------------------------------------------------
#         xxxxxx Price Difference Account             | 1.0   |
#         ---------------------------------------------------------------
#
#         :return: A list of Python dictionary to be passed to env['account.move.line'].create.
#         '''
#         get_company_data = self.env['product.sale.accounting'].search(
#             [('company_id', '=', self.env.user.company_id.id)], limit=1)
#         if get_company_data:
#             lines_vals_list = []
#
#             for move in self:
#                 if move.type not in ('in_invoice', 'in_refund', 'in_receipt') or not move.company_id.anglo_saxon_accounting:
#                     continue
#
#                 for line in move.invoice_line_ids.filtered(lambda line: line.product_id.type == 'product' and get_company_data.property_valuation == 'real_time'):
#
#                     # Filter out lines being not eligible for price difference.
#                     if line.product_id.type != 'product' or get_company_data.property_valuation != 'real_time':
#                         continue
#
#                     # Retrieve accounts needed to generate the price difference.
#                     debit_pdiff_account = line.product_id.property_account_creditor_price_difference \
#                                     or line.product_id.categ_id.property_account_creditor_price_difference_categ
#                     debit_pdiff_account = move.fiscal_position_id.map_account(debit_pdiff_account)
#
#                     if get_company_data.property_cost_method != 'standard' and line.purchase_line_id:
#                         po_currency = line.purchase_line_id.currency_id
#                         po_company = line.purchase_line_id.company_id
#
#                         # Retrieve stock valuation moves.
#                         valuation_stock_moves = self.env['stock.move'].search([
#                             ('purchase_line_id', '=', line.purchase_line_id.id),
#                             ('state', '=', 'done'),
#                             ('product_qty', '!=', 0.0),
#                         ])
#                         if move.type == 'in_refund':
#                             valuation_stock_moves = valuation_stock_moves.filtered(lambda stock_move: stock_move._is_out())
#                         else:
#                             valuation_stock_moves = valuation_stock_moves.filtered(lambda stock_move: stock_move._is_in())
#
#                         if valuation_stock_moves:
#                             valuation_price_unit_total = 0
#                             valuation_total_qty = 0
#                             for val_stock_move in valuation_stock_moves:
#                                 # In case val_stock_move is a return move, its valuation entries have been made with the
#                                 # currency rate corresponding to the original stock move
#                                 valuation_date = val_stock_move.origin_returned_move_id.date or val_stock_move.date
#                                 svl = val_stock_move.mapped('stock_valuation_layer_ids').filtered(lambda l: l.quantity)
#                                 layers_qty = sum(svl.mapped('quantity'))
#                                 layers_values = sum(svl.mapped('value'))
#                                 valuation_price_unit_total += line.company_currency_id._convert(
#                                     layers_values, move.currency_id,
#                                     move.company_id, valuation_date, round=False,
#                                 )
#                                 valuation_total_qty += layers_qty
#                             valuation_price_unit = valuation_price_unit_total / valuation_total_qty
#                             valuation_price_unit = line.product_id.uom_id._compute_price(valuation_price_unit, line.product_uom_id)
#
#                         elif get_company_data.property_cost_method == 'fifo':
#                             # In this condition, we have a real price-valuated product which has not yet been received
#                             valuation_price_unit = po_currency._convert(
#                                 line.purchase_line_id.price_unit, move.currency_id,
#                                 po_company, move.date, round=False,
#                             )
#                         else:
#                             # For average/fifo/lifo costing method, fetch real cost price from incoming moves.
#                             price_unit = line.purchase_line_id.product_uom._compute_price(line.purchase_line_id.price_unit, line.product_uom_id)
#                             valuation_price_unit = po_currency._convert(
#                                 price_unit, move.currency_id,
#                                 po_company, move.date, round=False
#                             )
#
#                     else:
#                         # Valuation_price unit is always expressed in invoice currency, so that it can always be computed with the good rate
#                         price_unit = line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_uom_id)
#                         valuation_price_unit = line.company_currency_id._convert(
#                             price_unit, move.currency_id,
#                             move.company_id, fields.Date.today(), round=False
#                         )
#
#                     invoice_cur_prec = move.currency_id.decimal_places
#
#                     price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#                     if line.tax_ids:
#                         price_unit = line.tax_ids.compute_all(
#                             price_unit, currency=move.currency_id, quantity=1.0, is_refund=move.type == 'in_refund')['total_excluded']
#
#                     if float_compare(valuation_price_unit, price_unit, precision_digits=invoice_cur_prec) != 0 \
#                             and float_compare(line['price_unit'], line.price_unit, precision_digits=invoice_cur_prec) == 0:
#
#                         price_unit_val_dif = price_unit - valuation_price_unit
#
#                         if move.currency_id.compare_amounts(price_unit, valuation_price_unit) != 0 and debit_pdiff_account:
#                             # Add price difference account line.
#                             vals = {
#                                 'name': line.name[:64],
#                                 'move_id': move.id,
#                                 'currency_id': line.currency_id.id,
#                                 'product_id': line.product_id.id,
#                                 'product_uom_id': line.product_uom_id.id,
#                                 'quantity': line.quantity,
#                                 'price_unit': price_unit_val_dif,
#                                 'price_subtotal': line.quantity * price_unit_val_dif,
#                                 'account_id': debit_pdiff_account.id,
#                                 'analytic_account_id': line.analytic_account_id.id,
#                                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                                 'exclude_from_invoice_tab': True,
#                                 'is_anglo_saxon_line': True,
#                             }
#                             vals.update(line._get_fields_onchange_subtotal(price_subtotal=vals['price_subtotal']))
#                             lines_vals_list.append(vals)
#
#                             # Correct the amount of the current line.
#                             vals = {
#                                 'name': line.name[:64],
#                                 'move_id': move.id,
#                                 'currency_id': line.currency_id.id,
#                                 'product_id': line.product_id.id,
#                                 'product_uom_id': line.product_uom_id.id,
#                                 'quantity': line.quantity,
#                                 'price_unit': -price_unit_val_dif,
#                                 'price_subtotal': line.quantity * -price_unit_val_dif,
#                                 'account_id': line.account_id.id,
#                                 'analytic_account_id': line.analytic_account_id.id,
#                                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                                 'exclude_from_invoice_tab': True,
#                                 'is_anglo_saxon_line': True,
#                             }
#                             vals.update(line._get_fields_onchange_subtotal(price_subtotal=vals['price_subtotal']))
#                             lines_vals_list.append(vals)
#             return lines_vals_list
#
#         else:
#             raise ValidationError(_("Please first set your company accounting setting!!!"))
#
#     def _stock_account_anglo_saxon_reconcile_valuation(self, product=False):
#         """ Reconciles the entries made in the interim accounts in anglosaxon accounting,
#         reconciling stock valuation move lines with the invoice's.
#         """
#         property_valuation = self.env['product.sale.accounting'].search(
#             [('company_id', '=', self.env.user.company_id.id)], limit=1)
#         if property_valuation:
#             for move in self:
#                 if not move.is_invoice():
#                     continue
#                 if not move.company_id.anglo_saxon_accounting:
#                     continue
#
#                 stock_moves = move._stock_account_get_last_step_stock_moves()
#
#                 if not stock_moves:
#                     continue
#
#                 products = product or move.mapped('invoice_line_ids.product_id')
#                 for product in products:
#                     if property_valuation.property_valuation != 'real_time':
#                         continue
#
#                     # We first get the invoices move lines (taking the invoice and the previous ones into account)...
#                     product_accounts = product.product_tmpl_id._get_product_accounts()
#                     if move.is_sale_document():
#                         product_interim_account = product_accounts['stock_output']
#                     else:
#                         product_interim_account = product_accounts['stock_input']
#
#                     if product_interim_account.reconcile:
#                         # Search for anglo-saxon lines linked to the product in the journal entry.
#                         product_account_moves = move.line_ids.filtered(
#                             lambda line: line.product_id == product and line.account_id == product_interim_account and not line.reconciled)
#
#                         # Search for anglo-saxon lines linked to the product in the stock moves.
#                         product_stock_moves = stock_moves.filtered(lambda stock_move: stock_move.product_id == product)
#                         product_account_moves += product_stock_moves.mapped('account_move_ids.line_ids')\
#                             .filtered(lambda line: line.account_id == product_interim_account and not line.reconciled)
#
#                         # Reconcile.
#                         product_account_moves.reconcile()
#         else:
#             raise ValidationError(_("Please first set your company accounting setting!!!"))

