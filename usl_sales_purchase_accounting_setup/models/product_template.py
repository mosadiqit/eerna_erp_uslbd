from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class InheritProductTemplate(models.Model):
    _inherit = "product.template"

    def get_product_accounts(self, fiscal_pos=None):
        accounts = self._get_company_wise_accounts()
        accounts.update({'stock_journal': self.categ_id.property_stock_journal or False})
        if not fiscal_pos:
            fiscal_pos = self.env['account.fiscal.position']
        return fiscal_pos.map_accounts(accounts)

    def _get_company_wise_accounts(self):
        company_accounts=self.env['product.sale.accounting'].search([('company_id','=',self.env.user.company_id.id)])
        if company_accounts:
            # stock_valuation=self.env['account.account'].search([('id','=',company_accounts.stock_valuation_account.account_account_id),('company_id','=',self.env.user.company_id.id)])
            # if stock_valuation:
            return {'expense':self.env['account.account'].search([('id','=',company_accounts.expense_account.account_account_id),('company_id','=',self.env.user.company_id.id)]),
                          'income':self.env['account.account'].search([('id','=',company_accounts.income_account.account_account_id),('company_id','=',self.env.user.company_id.id)]),
                          'stock_input':self.env['account.account'].search([('id','=',company_accounts.stock_input_account.account_account_id),('company_id','=',self.env.user.company_id.id)]),
                          'stock_output':self.env['account.account'].search([('id','=',company_accounts.stock_output_account.account_account_id),('company_id','=',self.env.user.company_id.id)]),
                          'stock_valuation':self.env['account.account'].search([('id','=',company_accounts.stock_valuation_account.account_account_id),('company_id','=',self.env.user.company_id.id)])}
            # else:
            #     raise ValidationError(_("Stock valuation account id is not set for your company!!!"))
        else:
            raise ValidationError(_("Please set accounting for your company!!!"))

    # def write(self, vals):
    #     get_company_data = self.env['product.sale.accounting'].search([('company_id', '=', self.env.user.company_id.id)])
    #     if get_company_data:
    #         impacted_templates = {}
    #         move_vals_list = []
    #         Product = self.env['product.product']
    #         SVL = self.env['stock.valuation.layer']
    #
    #         if 'categ_id' in vals:
    #             # When a change of category implies a change of cost method, we empty out and replenish
    #             # the stock.
    #             new_product_category = self.env['product.category'].browse(vals.get('categ_id'))
    #
    #             for product_template in self:
    #                 valuation_impacted = False
    #                 if product_template.cost_method != new_product_category.property_cost_method:
    #                     valuation_impacted = True
    #                 if product_template.valuation != new_product_category.property_valuation:
    #                     valuation_impacted = True
    #                 if valuation_impacted is False:
    #                     continue
    #
    #                 # Empty out the stock with the current cost method.
    #                 description = _("Due to a change of product category (from %s to %s), the costing method\
    #                                 has changed for product template %s: from %s to %s.") %\
    #                     (product_template.categ_id.display_name, new_product_category.display_name, \
    #                      product_template.display_name, product_template.cost_method, new_product_category.property_cost_method)
    #                 out_svl_vals_list, products_orig_quantity_svl, products = Product\
    #                     ._svl_empty_stock(description, product_template=product_template)
    #                 out_stock_valuation_layers = SVL.create(out_svl_vals_list)
    #                 if get_company_data.property_valuation == 'real_time':
    #                     move_vals_list += Product._svl_empty_stock_am(out_stock_valuation_layers)
    #                 impacted_templates[product_template] = (products, description, products_orig_quantity_svl)
    #
    #         res = super(InheritProductTemplate, self).write(vals)
    #
    #         for product_template, (products, description, products_orig_quantity_svl) in impacted_templates.items():
    #             # Replenish the stock with the new cost method.
    #             in_svl_vals_list = products._svl_replenish_stock(description, products_orig_quantity_svl)
    #             in_stock_valuation_layers = SVL.create(in_svl_vals_list)
    #             if get_company_data.property_valuation == 'real_time':
    #                 move_vals_list += Product._svl_replenish_stock_am(in_stock_valuation_layers)
    #
    #         # Create the account moves.
    #         if move_vals_list:
    #             account_moves = self.env['account.move'].create(move_vals_list)
    #             account_moves.post()
    #         return res
    #     else:
    #         raise ValidationError(_("Please first set your company accounting setting!!!"))

class InheritProductProduct(models.Model):
    _inherit = "product.product"


    def _prepare_in_svl_vals(self, quantity, unit_cost):
        """Prepare the values for a stock valuation layer created by a receipt.

        :param quantity: the quantity to value, expressed in `self.uom_id`
        :param unit_cost: the unit cost to value `quantity`
        :return: values to use in a call to create
        :rtype: dict
        """
        self.ensure_one()
        vals = {
            'product_id': self.id,
            'value': unit_cost * quantity,
            'unit_cost': unit_cost,
            'quantity': quantity,
        }
        company_id=self.env.user.company_id.id
        get_company_data=self.env['product.sale.accounting'].search([('company_id','=',company_id)])
        if get_company_data:
            if get_company_data.property_cost_method in ('average', 'fifo'):
                vals['remaining_qty'] = quantity
                vals['remaining_value'] = vals['value']

        else:
            raise ValidationError(_("Please first set your company accounting setting!!!"))
        return vals

        # if self.cost_method in ('average', 'fifo'):
        #     vals['remaining_qty'] = quantity
        #     vals['remaining_value'] = vals['value']
        # return vals

    def _prepare_out_svl_vals(self, quantity, company):
        """Prepare the values for a stock valuation layer created by a delivery.

        :param quantity: the quantity to value, expressed in `self.uom_id`
        :return: values to use in a call to create
        :rtype: dict
        """
        self.ensure_one()
        # Quantity is negative for out valuation layers.
        quantity = -1 * quantity
        vals = {
            'product_id' : self.id,
            'value': quantity * self.standard_price,
            'unit_cost': self.standard_price,
            'quantity': quantity,
        }
        company_id = self.env.user.company_id.id
        get_company_data = self.env['product.sale.accounting'].search([('company_id', '=', company_id)])
        if get_company_data:
            if get_company_data.property_cost_method in ('average', 'fifo'):
                fifo_vals = self._run_fifo(abs(quantity), company)
                vals['remaining_qty'] = fifo_vals.get('remaining_qty')
                if get_company_data.property_cost_method == 'fifo':
                    vals.update(fifo_vals)
        else:
            raise ValidationError(_("Please first set your company accounting setting!!!"))
        # if self.cost_method in ('average', 'fifo'):
        #     fifo_vals = self._run_fifo(abs(quantity), company)
        #     vals['remaining_qty'] = fifo_vals.get('remaining_qty')
        #     if self.cost_method == 'fifo':
        #         vals.update(fifo_vals)
        return vals

    def _change_standard_price(self, new_price, counterpart_account_id=False):
        """Helper to create the stock valuation layers and the account moves
        after an update of standard price.

        :param new_price: new standard price
        """
        # Handle stock valuation layers.
        company_id = self.env.user.company_id.id
        get_company_data = self.env['product.sale.accounting'].search([('company_id', '=', company_id)],limit=1)
        if get_company_data:
            svl_vals_list = []
            company_id = self.env.company
            for product in self:
                if get_company_data.property_cost_method not in ('standard', 'average'):
                    continue
                quantity_svl = product.sudo().quantity_svl
                if float_is_zero(quantity_svl, precision_rounding=product.uom_id.rounding):
                    continue
                diff = new_price - product.standard_price
                value = company_id.currency_id.round(quantity_svl * diff)
                if company_id.currency_id.is_zero(value):
                    continue

                svl_vals = {
                    'company_id': company_id.id,
                    'product_id': product.id,
                    'description': _('Product value manually modified (from %s to %s)') % (product.standard_price, new_price),
                    'value': value,
                    'quantity': 0,
                }
                svl_vals_list.append(svl_vals)
            stock_valuation_layers = self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

            # Handle account moves.
            product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in self}
            am_vals_list = []
            for stock_valuation_layer in stock_valuation_layers:
                product = stock_valuation_layer.product_id
                value = stock_valuation_layer.value

                if get_company_data.property_valuation != 'real_time':
                    continue

                # Sanity check.
                if counterpart_account_id is False:
                    raise UserError(_('You must set a counterpart account.'))
                if not product_accounts[product.id].get('stock_valuation'):
                    raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))

                if value < 0:
                    debit_account_id = counterpart_account_id
                    credit_account_id = product_accounts[product.id]['stock_valuation'].id
                else:
                    debit_account_id = product_accounts[product.id]['stock_valuation'].id
                    credit_account_id = counterpart_account_id

                move_vals = {
                    'journal_id': product_accounts[product.id]['stock_journal'].id,
                    'company_id': company_id.id,
                    'ref': product.default_code,
                    'stock_valuation_layer_ids': [(6, None, [stock_valuation_layer.id])],
                    'line_ids': [(0, 0, {
                        'name': _('%s changed cost from %s to %s - %s') % (self.env.user.name, product.standard_price, new_price, product.display_name),
                        'account_id': debit_account_id,
                        'debit': abs(value),
                        'credit': 0,
                        'product_id': product.id,
                    }), (0, 0, {
                        'name': _('%s changed cost from %s to %s - %s') % (self.env.user.name, product.standard_price, new_price, product.display_name),
                        'account_id': credit_account_id,
                        'debit': 0,
                        'credit': abs(value),
                        'product_id': product.id,
                    })],
                }
                am_vals_list.append(move_vals)
            account_moves = self.env['account.move'].create(am_vals_list)
            if account_moves:
                account_moves.post()

            # Actually update the standard price.
            self.with_context(force_company=company_id.id).sudo().write({'standard_price': new_price})
        else:
            raise ValidationError(_("Please first set your company accounting setting!!!"))

    def _run_fifo(self, quantity, company):
        company_id = self.env.user.company_id.id
        get_company_data = self.env['product.sale.accounting'].search([('company_id', '=', company_id)], limit=1)
        if get_company_data:
            self.ensure_one()

            # Find back incoming stock valuation layers (called candidates here) to value `quantity`.
            qty_to_take_on_candidates = quantity
            candidates = self.env['stock.valuation.layer'].sudo().with_context(active_test=False).search([
                ('product_id', '=', self.id),
                ('remaining_qty', '>', 0),
                ('company_id', '=', company.id),
            ])
            new_standard_price = 0
            tmp_value = 0  # to accumulate the value taken on the candidates
            for candidate in candidates:
                qty_taken_on_candidate = min(qty_to_take_on_candidates, candidate.remaining_qty)

                candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
                new_standard_price = candidate_unit_cost
                value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
                value_taken_on_candidate = candidate.currency_id.round(value_taken_on_candidate)
                new_remaining_value = candidate.remaining_value - value_taken_on_candidate

                candidate_vals = {
                    'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                    'remaining_value': new_remaining_value,
                }

                candidate.write(candidate_vals)

                qty_to_take_on_candidates -= qty_taken_on_candidate
                tmp_value += value_taken_on_candidate
                if float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                    break

            # Update the standard price with the price of the last used candidate, if any.

            if new_standard_price and get_company_data.property_cost_method == 'fifo':
                self.sudo().with_context(force_company=company.id).standard_price = new_standard_price

            # If there's still quantity to value but we're out of candidates, we fall in the
            # negative stock use case. We chose to value the out move at the price of the
            # last out and a correction entry will be made once `_fifo_vacuum` is called.
            vals = {}
            if float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                vals = {
                    'value': -tmp_value,
                    'unit_cost': tmp_value / quantity,
                }
            else:
                assert qty_to_take_on_candidates > 0
                last_fifo_price = new_standard_price or self.standard_price
                negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
                tmp_value += abs(negative_stock_value)
                vals = {
                    'remaining_qty': -qty_to_take_on_candidates,
                    'value': -tmp_value,
                    'unit_cost': last_fifo_price,
                }
            return vals
        else:
            raise ValidationError(_("Please first set your company accounting setting!!!"))

    def _run_fifo_vacuum(self, company=None):
        """Compensate layer valued at an estimated price with the price of future receipts
        if any. If the estimated price is equals to the real price, no layer is created but
        the original layer is marked as compensated.

        :param company: recordset of `res.company` to limit the execution of the vacuum
        """
        company_id = self.env.user.company_id.id
        get_company_data = self.env['product.sale.accounting'].search([('company_id', '=', company_id)], limit=1)
        if get_company_data:
            self.ensure_one()
            if company is None:
                company = self.env.company
            svls_to_vacuum = self.env['stock.valuation.layer'].sudo().search([
                ('product_id', '=', self.id),
                ('remaining_qty', '<', 0),
                ('stock_move_id', '!=', False),
                ('company_id', '=', company.id),
            ], order='create_date, id')
            for svl_to_vacuum in svls_to_vacuum:
                domain = [
                    ('company_id', '=', svl_to_vacuum.company_id.id),
                    ('product_id', '=', self.id),
                    ('remaining_qty', '>', 0),
                    '|',
                        ('create_date', '>', svl_to_vacuum.create_date),
                        '&',
                            ('create_date', '=', svl_to_vacuum.create_date),
                            ('id', '>', svl_to_vacuum.id)
                ]
                candidates = self.env['stock.valuation.layer'].sudo().search(domain)
                if not candidates:
                    break
                qty_to_take_on_candidates = abs(svl_to_vacuum.remaining_qty)
                qty_taken_on_candidates = 0
                tmp_value = 0
                for candidate in candidates:
                    qty_taken_on_candidate = min(candidate.remaining_qty, qty_to_take_on_candidates)
                    qty_taken_on_candidates += qty_taken_on_candidate

                    candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
                    value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
                    value_taken_on_candidate = candidate.currency_id.round(value_taken_on_candidate)
                    new_remaining_value = candidate.remaining_value - value_taken_on_candidate

                    candidate_vals = {
                        'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                        'remaining_value': new_remaining_value
                    }
                    candidate.write(candidate_vals)

                    qty_to_take_on_candidates -= qty_taken_on_candidate
                    tmp_value += value_taken_on_candidate
                    if float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                        break

                # Get the estimated value we will correct.
                remaining_value_before_vacuum = svl_to_vacuum.unit_cost * qty_taken_on_candidates
                new_remaining_qty = svl_to_vacuum.remaining_qty + qty_taken_on_candidates
                corrected_value = remaining_value_before_vacuum - tmp_value
                svl_to_vacuum.write({
                    'remaining_qty': new_remaining_qty,
                })

                # Don't create a layer or an accounting entry if the corrected value is zero.
                if svl_to_vacuum.currency_id.is_zero(corrected_value):
                    continue

                corrected_value = svl_to_vacuum.currency_id.round(corrected_value)
                move = svl_to_vacuum.stock_move_id
                vals = {
                    'product_id': self.id,
                    'value': corrected_value,
                    'unit_cost': 0,
                    'quantity': 0,
                    'remaining_qty': 0,
                    'stock_move_id': move.id,
                    'company_id': move.company_id.id,
                    'description': 'Revaluation of %s (negative inventory)' % move.picking_id.name or move.name,
                    'stock_valuation_layer_id': svl_to_vacuum.id,
                }
                vacuum_svl = self.env['stock.valuation.layer'].sudo().create(vals)

                # If some negative stock were fixed, we need to recompute the standard price.
                product = self.with_context(force_company=company.id)
                if get_company_data.property_cost_method == 'average' and not float_is_zero(product.quantity_svl, precision_rounding=self.uom_id.rounding):
                    product.sudo().write({'standard_price': product.value_svl / product.quantity_svl})

                # Create the account move.
                if get_company_data.property_valuation != 'real_time':
                    continue
                vacuum_svl.stock_move_id._account_entry_move(
                    vacuum_svl.quantity, vacuum_svl.description, vacuum_svl.id, vacuum_svl.value
                )
        else:
            raise ValidationError(_("Please first set your company accounting setting!!!"))

    # -------------------------------------------------------------------------
    # Anglo saxon helpers
    # -------------------------------------------------------------------------
    @api.model
    def _anglo_saxon_sale_move_lines(self, name, product, uom, qty, price_unit, currency=False, amount_currency=False, fiscal_position=False, account_analytic=False, analytic_tags=False):
        """Prepare dicts describing new journal COGS journal items for a product sale.

        Returns a dict that should be passed to `_convert_prepared_anglosaxon_line()` to
        obtain the creation value for the new journal items.

        :param Model product: a product.product record of the product being sold
        :param Model uom: a product.uom record of the UoM of the sale line
        :param Integer qty: quantity of the product being sold
        :param Integer price_unit: unit price of the product being sold
        :param Model currency: a res.currency record from the order of the product being sold
        :param Interger amount_currency: unit price in the currency from the order of the product being sold
        :param Model fiscal_position: a account.fiscal.position record from the order of the product being sold
        :param Model account_analytic: a account.account.analytic record from the line of the product being sold
        """
        company_id = self.env.user.company_id.id
        get_company_data = self.env['product.sale.accounting'].search([('company_id', '=', company_id)], limit=1)
        if get_company_data:
            if product.type == 'product' and get_company_data.property_cost_method == 'real_time':
                accounts = product.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
                # debit account dacc will be the output account
                dacc = accounts['stock_output'].id
                # credit account cacc will be the expense account
                cacc = accounts['expense'].id
                if dacc and cacc:
                    return [
                        {
                            'type': 'src',
                            'name': name[:64],
                            'price_unit': price_unit,
                            'quantity': qty,
                            'price': price_unit * qty,
                            'currency_id': currency and currency.id,
                            'amount_currency': amount_currency,
                            'account_id': dacc,
                            'product_id': product.id,
                            'uom_id': uom.id,
                        },

                        {
                            'type': 'src',
                            'name': name[:64],
                            'price_unit': price_unit,
                            'quantity': qty,
                            'price': -1 * price_unit * qty,
                            'currency_id': currency and currency.id,
                            'amount_currency': -1 * amount_currency,
                            'account_id': cacc,
                            'product_id': product.id,
                            'uom_id': uom.id,
                            'account_analytic_id': account_analytic and account_analytic.id,
                            'analytic_tag_ids': analytic_tags and analytic_tags.ids and [(6, 0, analytic_tags.ids)] or False,
                        },
                    ]
            return []
        else:
            raise ValidationError(_("Please first set your company accounting setting!!!"))



