from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from collections import defaultdict


class InheritStockMove(models.Model):
    _inherit = "stock.move"


    # def _action_done(self, cancel_backorder=False):
    #     # Init a dict that will group the moves by valuation type, according to `move._is_valued_type`.
    #     valued_moves = {valued_type: self.env['stock.move'] for valued_type in self._get_valued_types()}
    #     for move in self:
    #         for valued_type in self._get_valued_types():
    #             if getattr(move, '_is_%s' % valued_type)():
    #                 valued_moves[valued_type] |= move
    #                 continue
    #
    #     # AVCO application
    #     valued_moves['in'].product_price_update_before_done()
    #
    #     res = super(InheritStockMove, self)._action_done(cancel_backorder=cancel_backorder)
    #
    #     # '_action_done' might have created an extra move to be valued
    #     for move in res - self:
    #         for valued_type in self._get_valued_types():
    #             if getattr(move, '_is_%s' % valued_type)():
    #                 valued_moves[valued_type] |= move
    #                 continue
    #
    #     stock_valuation_layers = self.env['stock.valuation.layer'].sudo()
    #     # Create the valuation layers in batch by calling `moves._create_valued_type_svl`.
    #     for valued_type in self._get_valued_types():
    #         todo_valued_moves = valued_moves[valued_type]
    #         if todo_valued_moves:
    #             todo_valued_moves._sanity_check_for_valuation()
    #             stock_valuation_layers |= getattr(todo_valued_moves, '_create_%s_svl' % valued_type)()
    #             continue
    #
    #     for svl in stock_valuation_layers.with_context(active_test=False):
    #         get_company_data = self.env['product.sale.accounting'].search([('company_id', '=', svl.company_id.id)])
    #         if get_company_data:
    #             if get_company_data.property_valuation=='real_time':
    #                 continue
    #         else:
    #             raise ValidationError(_("Please first set your company accounting setting!!!"))
    #         # if not svl.product_id.valuation == 'real_time':
    #         #     continue
    #         if svl.currency_id.is_zero(svl.value):
    #             continue
    #         svl.stock_move_id._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
    #
    #     stock_valuation_layers._check_company()
    #
    #     # For every in move, run the vacuum for the linked product.
    #     products_to_vacuum = valued_moves['in'].mapped('product_id')
    #     company = valued_moves['in'].mapped('company_id') and valued_moves['in'].mapped('company_id')[0] or self.env.company
    #     for product_to_vacuum in products_to_vacuum.with_context(active_test=False):
    #         product_to_vacuum._run_fifo_vacuum(company)
    #
    #     return res
    #
    # def _create_in_svl(self, forced_quantity=None):
    #     """Create a `stock.valuation.layer` from `self`.
    #
    #     :param forced_quantity: under some circunstances, the quantity to value is different than
    #         the initial demand of the move (Default value = None)
    #     """
    #     active_model = self.env.context.get('active_model')
    #     svl_vals_list = []
    #     for move in self:
    #         move = move.with_context(force_company=move.company_id.id)
    #         valued_move_lines = move._get_in_move_lines()
    #         valued_quantity = 0
    #         for valued_move_line in valued_move_lines:
    #             if active_model == 'foreign.purchase.order':
    #                 if move.product_id.tracking == 'serial':
    #                     valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
    #                                                                                          move.product_id.uom_id)
    #                 else:
    #                     valued_quantity += valued_move_line.product_uom_id._compute_quantity(
    #                         valued_move_line.current_receive_qty,
    #                         move.product_id.uom_id)
    #             else:
    #                 valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
    #                                                                                      move.product_id.uom_id)
    #         unit_cost = abs(move._get_price_unit())  # May be negative (i.e. decrease an out move).
    #
    #         get_company_costing_data=self.env['product.sale.accounting'].search([('company_id','=',move.company_id.id)])
    #         if get_company_costing_data:
    #             if get_company_costing_data.property_cost_method=='standard':
    #                 unit_cost = move.product_id.standard_price
    #         else:
    #             raise ValidationError(_("Please first set your company accounting setting!!!"))
    #         # if move.product_id.cost_method == 'standard':
    #         #     unit_cost = move.product_id.standard_price
    #         svl_vals = move.product_id._prepare_in_svl_vals(forced_quantity or valued_quantity, unit_cost)
    #         svl_vals.update(move._prepare_common_svl_vals())
    #         if forced_quantity:
    #             svl_vals[
    #                 'description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
    #         svl_vals_list.append(svl_vals)
    #     return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    ###############################################def _create_out_svl() Not necessary##############################################
    # def _create_out_svl(self, forced_quantity=None):
    #     """Create a `stock.valuation.layer` from `self`.
    #
    #     :param forced_quantity: under some circunstances, the quantity to value is different than
    #         the initial demand of the move (Default value = None)
    #     """
    #     svl_vals_list = []
    #     for move in self:
    #         move = move.with_context(force_company=move.company_id.id)
    #         valued_move_lines = move._get_out_move_lines()
    #         valued_quantity = 0
    #         for valued_move_line in valued_move_lines:
    #             valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
    #         if float_is_zero(forced_quantity or valued_quantity, precision_rounding=move.product_id.uom_id.rounding):
    #             continue
    #         svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id)
    #         svl_vals.update(move._prepare_common_svl_vals())
    #         if forced_quantity:
    #             svl_vals['description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
    #         svl_vals_list.append(svl_vals)
    #     return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def product_price_update_before_done(self, forced_qty=None):
        active_model = self.env.context.get('active_model')
        if active_model == 'foreign.purchase.order':
            tmpl_dict = defaultdict(lambda: 0.0)
            # adapt standard price on incomming moves if the product cost_method is 'average'
            std_price_update = {}
            for move in self.filtered(lambda move: move._is_in() and move.with_context(
                    force_company=move.company_id.id)):
                for company in self.env['product.sale.accounting'].search([]):
                    if move.company_id.id == company.company_id.id:
                        if company.property_cost_method == 'average':
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
                                # amount_unit = std_price_update.get(
                                #     (move.company_id.id, move.product_id.id)) or move.product_id.with_context(
                                #     force_company=move.company_id.id).standard_price
                                amount_unit = std_price_update.get(
                                    (move.company_id.id, move.product_id.id)) or move.product_id.with_context(
                                    force_company=move.company_id.id).changeable_standard_price
                                gt_p_u=move._get_price_unit()
                                new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (
                                        product_tot_qty_available + qty)
                                # new_std_price = ((amount_unit * product_tot_qty_available) + (amount_unit * qty)) / (
                                #         product_tot_qty_available + qty)

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
                        raise ValidationError(_("Please first set your company accounting setting!!!"))

        else:
            tmpl_dict = defaultdict(lambda: 0.0)
            # adapt standard price on incomming moves if the product cost_method is 'average'
            std_price_update = {}
            # for move in self.filtered(lambda move: move._is_in() and move.with_context(
            #         force_company=move.company_id.id).product_id.cost_method == 'average'):
            for move in self.filtered(lambda move: move._is_in()and move.with_context(
                    force_company=move.company_id.id)):
                for company in self.env['product.sale.accounting'].search([]):
                    if move.company_id.id == company.company_id.id:
                        if company.property_cost_method == 'average':
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
                            elif float_is_zero(product_tot_qty_available + move.product_qty,
                                               precision_rounding=rounding) or \
                                    float_is_zero(product_tot_qty_available + qty, precision_rounding=rounding):
                                new_std_price = move._get_price_unit()
                            else:
                                # Get the standard price
                                amount_unit = std_price_update.get(
                                    (move.company_id.id, move.product_id.id)) or move.product_id.with_context(
                                    force_company=move.company_id.id).standard_price
                                new_std_price = ((amount_unit * product_tot_qty_available) + (
                                            move._get_price_unit() * qty)) / (
                                                        product_tot_qty_available + qty)

                            tmpl_dict[move.product_id.id] += qty_done
                            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
                            move.product_id.with_context(force_company=move.company_id.id).sudo().write(
                                {'standard_price': new_std_price})
                            std_price_update[move.company_id.id, move.product_id.id] = new_std_price

                    else:
                        raise ValidationError(_("Please first set your company accounting setting!!!"))
