from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from collections import defaultdict


class InheritStockPicking_Foreign(models.Model):
    _inherit = "stock.move"

    def _get_in_move_lines(self):
        """ Returns the `stock.move.line` records of `self` considered as incoming. It is done thanks
        to the `_should_be_valued` method of their source and destionation location as well as their
        owner.

        :returns: a subset of `self` containing the incoming records
        :rtype: recordset
        """
        sum_product_qty = 0
        if len(self.stock_valuation_layer_ids) > 0:
            for qty in self.stock_valuation_layer_ids:
                sum_product_qty += qty.quantity
        active_model = self.env.context.get('active_model')
        print(active_model)
        if active_model == 'foreign.purchase.order':
            if self.move_line_ids.product_id.tracking=='serial':
                res = self.env['stock.move.line']
                if len(self.move_line_ids.filtered(lambda s:s.qty_done>0)) == int(sum_product_qty):
                    for move_line in self.move_line_ids:
                        if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
                            continue
                        if not move_line.location_id._should_be_valued() and move_line.location_dest_id._should_be_valued() and move_line.qty_done > 0:
                            res |= move_line
                    return res
                else:
                    for move_line in self.move_line_ids[int(sum_product_qty)::]:
                        if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
                            continue
                        if not move_line.location_id._should_be_valued() and move_line.location_dest_id._should_be_valued() and move_line.qty_done > 0:
                            res |= move_line

                    return res
            else:
                self.ensure_one()
                res = self.env['stock.move.line']
                for move_line in self.move_line_ids:
                    if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
                        continue
                    if not move_line.location_id._should_be_valued() and move_line.location_dest_id._should_be_valued():
                        res |= move_line
                return res

        else:
            self.ensure_one()
            res = self.env['stock.move.line']
            for move_line in self.move_line_ids:
                if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
                    continue
                if not move_line.location_id._should_be_valued() and move_line.location_dest_id._should_be_valued():
                    res |= move_line
            return res

    def _account_entry_move(self, qty, description, svl_id, cost):

        """ Accounting Valuation Entries """
        active_model = self.env.context.get('active_model')
        self.ensure_one()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return False
        if self.restrict_partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return False

        location_from = self.location_id
        location_to = self.location_dest_id
        company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
        if active_model == 'foreign.purchase.order':
            company_to = self._is_in_foreign() and self.mapped('move_line_ids.location_dest_id.company_id') or False
        else:
            company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False
        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if active_model == 'foreign.purchase.order':
            if self._is_in_foreign():
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
                if location_from and location_from.usage == 'customer':  # goods returned from customer
                    self.with_context(force_company=company_to.id)._create_account_move_line(acc_dest, acc_valuation,
                                                                                             journal_id, qty, description,
                                                                                             svl_id, cost)
                else:
                    self.with_context(force_company=company_to.id)._create_account_move_line(acc_src, acc_valuation,
                                                                                             journal_id, qty, description,
                                                                                             svl_id, cost)
        else:
            if self._is_in():
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
                if location_from and location_from.usage == 'customer':  # goods returned from customer
                    self.with_context(force_company=company_to.id)._create_account_move_line(acc_dest, acc_valuation,
                                                                                             journal_id, qty, description,
                                                                                             svl_id, cost)
                else:
                    self.with_context(force_company=company_to.id)._create_account_move_line(acc_src, acc_valuation,
                                                                                             journal_id, qty, description,
                                                                                             svl_id, cost)

        # Create Journal Entry for products leaving the company
        if self._is_out():
            cost = -1 * cost
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if location_to and location_to.usage == 'supplier':  # goods returned to supplier
                self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_src,
                                                                                           journal_id, qty, description,
                                                                                           svl_id, cost)
            else:
                self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_dest,
                                                                                           journal_id, qty, description,
                                                                                           svl_id, cost)

        if self.company_id.anglo_saxon_accounting:
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if self._is_dropshipped():
                if cost > 0:
                    self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_src,
                                                                                                  acc_valuation,
                                                                                                  journal_id, qty,
                                                                                                  description, svl_id,
                                                                                                  cost)
                else:
                    cost = -1 * cost
                    self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation,
                                                                                                  acc_dest, journal_id,
                                                                                                  qty, description,
                                                                                                  svl_id, cost)
            elif self._is_dropshipped_returned():
                if cost > 0:
                    self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation,
                                                                                                  acc_src, journal_id,
                                                                                                  qty, description,
                                                                                                  svl_id, cost)
                else:
                    cost = -1 * cost
                    self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_dest,
                                                                                                  acc_valuation,
                                                                                                  journal_id, qty,
                                                                                                  description, svl_id,
                                                                                                  cost)

        if self.company_id.anglo_saxon_accounting:
            # eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
            self._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=self.product_id)


    def _is_in_foreign(self):
        """Check if the move should be considered as entering the company so that the cost method
        will be able to apply the correct logic.

        :returns: True if the move is entering the company else False
        :rtype: bool
        """
        self.ensure_one()
        if self._get_in_move_lines_foreign():
            return True
        return False

    def _get_in_move_lines_foreign(self):
        """ Returns the `stock.move.line` records of `self` considered as incoming. It is done thanks
        to the `_should_be_valued` method of their source and destionation location as well as their
        owner.

        :returns: a subset of `self` containing the incoming records
        :rtype: recordset
        """
        sum_product_qty = 0
        if len(self.stock_valuation_layer_ids) > 0:
            for qty in self.stock_valuation_layer_ids:
                sum_product_qty += qty.quantity

        res = self.env['stock.move.line']
        for line in self:
            if line.product_id.tracking=='serial':
                for move_line in line.move_line_ids[0:int(sum_product_qty)]:
                    if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
                        continue
                    if not move_line.location_id._should_be_valued() and move_line.location_dest_id._should_be_valued() and move_line.qty_done > 0:
                        res |= move_line
            else:
                for move_line in line.move_line_ids:
                    if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
                        continue
                    if not move_line.location_id._should_be_valued() and move_line.location_dest_id._should_be_valued() and move_line.qty_done > 0:
                        res |= move_line
        # for move_line in self.move_line_ids[0:int(sum_product_qty)]:
        #     if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
        #         continue
        #     if not move_line.location_id._should_be_valued() and move_line.location_dest_id._should_be_valued() and move_line.qty_done > 0:
        #         res |= move_line

        return res

    def _create_in_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        active_model = self.env.context.get('active_model')
        svl_vals_list = []
        for move in self:
            move = move.with_context(force_company=move.company_id.id)
            valued_move_lines = move._get_in_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                if active_model=='foreign.purchase.order':
                    if move.product_id.tracking=='serial':
                        valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                             move.product_id.uom_id)
                    else:
                        valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.current_receive_qty,
                                                                                             move.product_id.uom_id)
                else:
                    valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
            unit_cost = abs(move._get_price_unit())  # May be negative (i.e. decrease an out move).
            if move.product_id.cost_method == 'standard':
                unit_cost = move.product_id.standard_price
            svl_vals = move.product_id._prepare_in_svl_vals(forced_quantity or valued_quantity, unit_cost)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                svl_vals['description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def product_price_update_before_done(self, forced_qty=None):
        active_model = self.env.context.get('active_model')
        if active_model == 'foreign.purchase.order':
            tmpl_dict = defaultdict(lambda: 0.0)
            # adapt standard price on incomming moves if the product cost_method is 'average'
            std_price_update = {}
            for move in self.filtered(lambda move: move._is_in() and move.with_context(
                    force_company=move.company_id.id).product_id.cost_method == 'average'):
                product_tot_qty_available = move.product_id.sudo().with_context(
                    force_company=move.company_id.id).quantity_svl + tmpl_dict[move.product_id.id]
                rounding = move.product_id.uom_id.rounding

                valued_move_lines = move._get_in_move_lines()
                qty_done = 0
                for valued_move_line in valued_move_lines:
                    if  valued_move_line.product_id.tracking!='serial' :
                        qty_done+=valued_move_line.current_receive_qty
                    else:
                        qty_done += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                  move.product_id.uom_id)

                qty = forced_qty or qty_done
                # if move.product_id.tracking!='serial' and product_tot_qty_available!=0:
                #     product_tot_qty_available+=qty
                #     qty=product_tot_qty_available
                if float_is_zero(product_tot_qty_available, precision_rounding=rounding):
                    new_std_price = move._get_price_unit()
                elif float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding) or \
                        float_is_zero(product_tot_qty_available + qty, precision_rounding=rounding):
                    new_std_price = move._get_price_unit()
                else:
                    # Get the standard price
                    amount_unit = std_price_update.get(
                        (move.company_id.id, move.product_id.id)) or move.product_id.with_context(
                        force_company=move.company_id.id).standard_price
                    new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (
                            product_tot_qty_available + qty)

                tmpl_dict[move.product_id.id] += qty_done
                # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
                # move.product_id.with_context(force_company=move.company_id.id).sudo().write(
                #     {'standard_price': new_std_price})
                if active_model == 'foreign.purchase.order' and product_tot_qty_available != 0:
                    move.product_id.with_context(force_company=move.company_id.id).sudo().write(
                        {'changeable_standard_price': new_std_price})
                else:
                    move.product_id.with_context(force_company=move.company_id.id).sudo().write(
                        {'standard_price': new_std_price, 'changeable_standard_price': new_std_price})
                std_price_update[move.company_id.id, move.product_id.id] = new_std_price

        else:
            tmpl_dict = defaultdict(lambda: 0.0)
            # adapt standard price on incomming moves if the product cost_method is 'average'
            std_price_update = {}
            for move in self.filtered(lambda move: move._is_in() and move.with_context(
                    force_company=move.company_id.id).product_id.cost_method == 'average'):
                product_tot_qty_available = move.product_id.sudo().with_context(
                    force_company=move.company_id.id).quantity_svl + tmpl_dict[move.product_id.id]
                rounding = move.product_id.uom_id.rounding

                valued_move_lines = move._get_in_move_lines()
                qty_done = 0
                for valued_move_line in valued_move_lines:
                    qty_done += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                  move.product_id.uom_id)

                qty = forced_qty or qty_done
                if float_is_zero(product_tot_qty_available, precision_rounding=rounding):
                    new_std_price = move._get_price_unit()
                elif float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding) or \
                        float_is_zero(product_tot_qty_available + qty, precision_rounding=rounding):
                    new_std_price = move._get_price_unit()
                else:
                    # Get the standard price
                    amount_unit = std_price_update.get(
                        (move.company_id.id, move.product_id.id)) or move.product_id.with_context(
                        force_company=move.company_id.id).standard_price
                    new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (
                                product_tot_qty_available + qty)

                tmpl_dict[move.product_id.id] += qty_done
                # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
                move.product_id.with_context(force_company=move.company_id.id).sudo().write(
                    {'standard_price': new_std_price})
                std_price_update[move.company_id.id, move.product_id.id] = new_std_price

    # def _action_done(self, cancel_backorder=False):
    #     active_model = self.env.context.get('active_model')
    #     self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
    #     if active_model == 'foreign.purchase.order':
    #         moves = self.exists().filtered(lambda x: x.state  in ('done', 'cancel'))
    #     else:
    #         moves = self.exists().filtered(lambda x: x.state not in ('done', 'cancel'))
    #     moves_todo = self.env['stock.move']
    #
    #     # Cancel moves where necessary ; we should do it before creating the extra moves because
    #     # this operation could trigger a merge of moves.
    #     for move in moves:
    #         if move.quantity_done <= 0:
    #             if float_compare(move.product_uom_qty, 0.0,
    #                              precision_rounding=move.product_uom.rounding) == 0 or cancel_backorder:
    #                 move._action_cancel()
    #
    #     # Create extra moves where necessary
    #     for move in moves:
    #         if move.state == 'cancel' or move.quantity_done <= 0:
    #             continue
    #
    #         moves_todo |= move._create_extra_move()
    #
    #     moves_todo._check_company()
    #     # Split moves where necessary and move quants
    #     for move in moves_todo:
    #         # To know whether we need to create a backorder or not, round to the general product's
    #         # decimal precision and not the product's UOM.
    #         rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
    #             # Need to do some kind of conversion here
    #             qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done,
    #                                                            move.product_id.uom_id, rounding_method='HALF-UP')
    #             new_move = move._split(qty_split)
    #             move._unreserve_initial_demand(new_move)
    #             if cancel_backorder:
    #                 self.env['stock.move'].browse(new_move)._action_cancel()
    #     moves_todo.mapped('move_line_ids').sorted()._action_done()
    #     # Check the consistency of the result packages; there should be an unique location across
    #     # the contained quants.
    #     for result_package in moves_todo \
    #             .mapped('move_line_ids.result_package_id') \
    #             .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
    #         if len(result_package.quant_ids.filtered(
    #                 lambda q: not float_is_zero(abs(q.quantity) + abs(q.reserved_quantity),
    #                                             precision_rounding=q.product_uom_id.rounding)).mapped(
    #                 'location_id')) > 1:
    #             raise UserError(_(
    #                 'You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
    #     picking = moves_todo.mapped('picking_id')
    #     moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})
    #
    #     move_dests_per_company = defaultdict(lambda: self.env['stock.move'])
    #     for move_dest in moves_todo.move_dest_ids:
    #         move_dests_per_company[move_dest.company_id.id] |= move_dest
    #     for company_id, move_dests in move_dests_per_company.items():
    #         move_dests.sudo().with_context(force_company=company_id)._action_assign()
    #
    #     # We don't want to create back order for scrap moves
    #     # Replace by a kwarg in master
    #     if self.env.context.get('is_scrap'):
    #         return moves_todo
    #
    #     if picking and not cancel_backorder:
    #         picking._create_backorder()
    #     return moves_todo

    # def _split(self, qty, restrict_partner_id=False):
    #     """ Splits qty from move move into a new move
    #
    #     :param qty: float. quantity to split (given in product UoM)
    #     :param restrict_partner_id: optional partner that can be given in order to force the new move to restrict its choice of quants to the ones belonging to this partner.
    #     :param context: dictionay. can contains the special key 'source_location_id' in order to force the source location when copying the move
    #     :returns: id of the backorder move created """
    #     active_model = self.env.context.get('active_model')
    #
    #     self = self.with_prefetch() # This makes the ORM only look for one record and not 300 at a time, which improves performance
    #     if self.state in ('done', 'cancel'):
    #         if active_model != 'foreign.purchase.order':
    #             raise UserError(_('You cannot split a stock move that has been set to \'Done\'.'))
    #
    #
    #
    #     elif self.state == 'draft':
    #         # we restrict the split of a draft move because if not confirmed yet, it may be replaced by several other moves in
    #         # case of phantom bom (with mrp module). And we don't want to deal with this complexity by copying the product that will explode.
    #         raise UserError(_('You cannot split a draft move. It needs to be confirmed first.'))
    #     if float_is_zero(qty, precision_rounding=self.product_id.uom_id.rounding) or self.product_qty <= qty:
    #         return self.id
    #
    #     decimal_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #
    #     # `qty` passed as argument is the quantity to backorder and is always expressed in the
    #     # quants UOM. If we're able to convert back and forth this quantity in the move's and the
    #     # quants UOM, the backordered move can keep the UOM of the move. Else, we'll create is in
    #     # the UOM of the quants.
    #     uom_qty = self.product_id.uom_id._compute_quantity(qty, self.product_uom, rounding_method='HALF-UP')
    #     if float_compare(qty, self.product_uom._compute_quantity(uom_qty, self.product_id.uom_id, rounding_method='HALF-UP'), precision_digits=decimal_precision) == 0:
    #         defaults = self._prepare_move_split_vals(uom_qty)
    #     else:
    #         defaults = self.with_context(force_split_uom_id=self.product_id.uom_id.id)._prepare_move_split_vals(qty)
    #
    #     if restrict_partner_id:
    #         defaults['restrict_partner_id'] = restrict_partner_id
    #
    #     # TDE CLEANME: remove context key + add as parameter
    #     if self.env.context.get('source_location_id'):
    #         defaults['location_id'] = self.env.context['source_location_id']
    #     new_move = self.with_context(rounding_method='HALF-UP').copy(defaults)
    #
    #     # FIXME: pim fix your crap
    #     # Update the original `product_qty` of the move. Use the general product's decimal
    #     # precision and not the move's UOM to handle case where the `quantity_done` is not
    #     # compatible with the move's UOM.
    #     new_product_qty = self.product_id.uom_id._compute_quantity(self.product_qty - qty, self.product_uom, round=False)
    #     new_product_qty = float_round(new_product_qty, precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure'))
    #     self.with_context(do_not_unreserve=True, rounding_method='HALF-UP').write({'product_uom_qty': new_product_qty})
    #     new_move = new_move._action_confirm(merge=False)
    #     return new_move.id



class InheritStockMoveLine_Foreign(models.Model):
    _inherit = "stock.move.line"

    current_receive_qty=fields.Float()

    # def _action_done(self):
    #
    #     """ This method is called during a move's `action_done`. It'll actually move a quant from
    #     the source location to the destination location, and unreserve if needed in the source
    #     location.
    #
    #     This method is intended to be called on all the move lines of a move. This method is not
    #     intended to be called when editing a `done` move (that's what the override of `write` here
    #     is done.
    #     """
    #     active_model = self.env.context.get('active_model')
    #     Quant = self.env['stock.quant']
    #
    #     # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
    #     # be negative and, according to the presence of a picking type or a linked inventory
    #     # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
    #     # the line. It is mandatory in order to free the reservation and correctly apply
    #     # `action_done` on the next move lines.
    #     ml_to_delete = self.env['stock.move.line']
    #     for ml in self:
    #         # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
    #         uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
    #         precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
    #         if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
    #             raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
    #                                  defined on the unit of measure "%s". Please change the quantity done or the \
    #                                  rounding precision of your unit of measure.') % (
    #             ml.product_id.display_name, ml.product_uom_id.name))
    #
    #         qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
    #         if qty_done_float_compared > 0:
    #             if ml.product_id.tracking != 'none':
    #                 picking_type_id = ml.move_id.picking_type_id
    #                 if picking_type_id:
    #                     if picking_type_id.use_create_lots:
    #                         # If a picking type is linked, we may have to create a production lot on
    #                         # the fly before assigning it to the move line if the user checked both
    #                         # `use_create_lots` and `use_existing_lots`.
    #                         if ml.lot_name and not ml.lot_id:
    #                             lot = self.env['stock.production.lot'].create(
    #                                 {'name': ml.lot_name, 'product_id': ml.product_id.id,
    #                                  'company_id': ml.move_id.company_id.id}
    #                             )
    #                             ml.write({'lot_id': lot.id})
    #                     elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
    #                         # If the user disabled both `use_create_lots` and `use_existing_lots`
    #                         # checkboxes on the picking type, he's allowed to enter tracked
    #                         # products without a `lot_id`.
    #                         continue
    #                 elif ml.move_id.inventory_id:
    #                     # If an inventory adjustment is linked, the user is allowed to enter
    #                     # tracked products without a `lot_id`.
    #                     continue
    #
    #                 if not ml.lot_id:
    #                     if active_model == 'foreign.purchase.order':
    #                         continue
    #                     else:
    #                         raise UserError(
    #                             _('You need to supply a Lot/Serial number for product %s.') % ml.product_id.display_name)
    #         elif qty_done_float_compared < 0:
    #             raise UserError(_('No negative quantities allowed'))
    #         else:
    #             ml_to_delete |= ml
    #     ml_to_delete.unlink()
    #
    #     (self - ml_to_delete)._check_company()
    #
    #     # Now, we can actually move the quant.
    #     done_ml = self.env['stock.move.line']
    #     for ml in self - ml_to_delete:
    #         if ml.product_id.type == 'product':
    #             rounding = ml.product_uom_id.rounding
    #
    #             # if this move line is force assigned, unreserve elsewhere if needed
    #             if not ml._should_bypass_reservation(ml.location_id) and float_compare(ml.qty_done, ml.product_uom_qty,
    #                                                                                    precision_rounding=rounding) > 0:
    #                 qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id,
    #                                                                            rounding_method='HALF-UP')
    #                 extra_qty = qty_done_product_uom - ml.product_qty
    #                 ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id,
    #                                      package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
    #             # unreserve what's been reserved
    #             if not ml._should_bypass_reservation(
    #                     ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
    #                 try:
    #                     Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty,
    #                                                     lot_id=ml.lot_id, package_id=ml.package_id,
    #                                                     owner_id=ml.owner_id, strict=True)
    #                 except UserError:
    #                     Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False,
    #                                                     package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #
    #             # move what's been actually done
    #             quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,
    #                                                            rounding_method='HALF-UP')
    #             available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity,
    #                                                                       lot_id=ml.lot_id, package_id=ml.package_id,
    #                                                                       owner_id=ml.owner_id)
    #             if available_qty < 0 and ml.lot_id:
    #                 # see if we can compensate the negative quants with some untracked quants
    #                 untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False,
    #                                                               package_id=ml.package_id, owner_id=ml.owner_id,
    #                                                               strict=True)
    #                 if untracked_qty:
    #                     taken_from_untracked_qty = min(untracked_qty, abs(quantity))
    #                     Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty,
    #                                                      lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
    #                     Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty,
    #                                                      lot_id=ml.lot_id, package_id=ml.package_id,
    #                                                      owner_id=ml.owner_id)
    #             Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id,
    #                                              package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
    #         done_ml |= ml
    #     # Reset the reserved quantity as we just moved it to the destination location.
    #     (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
    #         'product_uom_qty': 0.00,
    #         'date': fields.Datetime.now(),
    #     })



