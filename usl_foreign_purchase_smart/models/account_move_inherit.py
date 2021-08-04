from datetime import date,datetime

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
class ForeignAccountMove(models.Model):
    _inherit = 'account.move'

    foreign_purchase_id = fields.Many2one('foreign.purchase.order', store=False, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  string='Purchase Order',
                                  help="Auto-complete from a past purchase order.")

    flag = fields.Boolean(string='Flag', compute='_compute_flag')
    landed_cost_count = fields.Integer( string='Bill Count',compute="_compute_landed_count",default=0)


    # @api.depends('invoice_line_ids')
    # def test(self):
    #     print(self)

    def button_draft(self):

        AccountMoveLine = self.env['account.move.line']
        excluded_move_ids = []
        active_model = self.env.context.get('active_model')
        if self._context.get('suspense_moves_mode'):
            excluded_move_ids = AccountMoveLine.search(AccountMoveLine._get_suspense_moves_domain() + [('move_id', 'in', self.ids)]).mapped('move_id').ids

        for move in self:
            if move in move.line_ids.mapped('full_reconcile_id.exchange_move_id'):
                raise UserError(_('You cannot reset to draft an exchange difference journal entry.'))
            if move.tax_cash_basis_rec_id:
                raise UserError(_('You cannot reset to draft a tax cash basis journal entry.'))
            if move.restrict_mode_hash_table and move.state == 'posted' and move.id not in excluded_move_ids:
                raise UserError(_('You cannot modify a posted entry of this journal because it is in strict mode.'))
            # We remove all the analytics entries for this journal
            # move.mapped('line_ids.analytic_line_ids').unlink()
            if active_model=='foreign.purchase.order':
                if move.state=='posted':
                    move.mapped('line_ids.analytic_line_ids').unlink()
                    move_id = self.env['stock.move'].search([('origin', '=', self.invoice_origin)])
                    for line in self.invoice_line_ids:
                        for stock_move_line in move_id.move_line_ids:
                            if line.product_id.id==stock_move_line.product_id.id:
                                product_id=line.product_id.id
                                qty=line.quantity
                                lim_stock=self.env['stock.warehouse'].search([('is_non_saleable_warehouse','=',True),('company_id','=',self.env.user.company_id.id)]).lot_stock_id
                                if line.product_id.product_tmpl_id.tracking=='serial':
                                    get_stock_move_line=self.env['stock.move.line'].search([('move_id','=',stock_move_line.move_id.id),('product_id','=',product_id),('qty_done','=',1)],order='id desc',limit=qty)
                                    for stock_move_line in get_stock_move_line:
                                        stock_move_line.qty_done = 0
                                        stock_move_line.state = 'assigned'
                                        stock_move_line.product_uom_qty = 1
                                else:
                                    get_stock_move_line=self.env['stock.move.line'].search([('move_id','=',stock_move_line.move_id.id),('product_id','=',product_id)],order='id desc')
                                    get_stock_move_line.qty_done = get_stock_move_line.qty_done - qty
                                self._cr.commit()
                                break


                        #         for stock_move_line in get_stock_move_line:
                        #             if stock_move_line.product_id.id==line.product_id.id:
                        #                 if line.product_id.product_tmpl_id.tracking=='serial':
                        #                     stock_move_line.qty_done=0
                        #                     stock_move_line.state='assigned'
                        #                     stock_move_line.product_uom_qty=1
                        #                 else:
                        #                     stock_move_line.qty_done=stock_move_line.qty_done-qty
                        #     self._cr.commit()
                        #     break
                                    # stock_move_line.product_uom_qty=stock_move_line.product_uom_qty+qty


                        # for stock_quant in get_stock_quant:
                        # query="""delete from stock_quant where id in {}""".format(tuple(all_line_stock_quant))
                        # self._cr.execute(query=query)

                        get_po_details=self.env['foreign.purchase.order'].search([('name','=',self.invoice_origin)])
                        for po_line in get_po_details:
                            for row in po_line.line_ids:
                                if row.product_id.id==line.product_id.id and row.invoiced_uom_qty>0:
                                    row.invoiced_uom_qty=row.invoiced_uom_qty-qty
                                    row.remaining_uom_qty=row.remaining_uom_qty+qty
                                    row.received_uom_qty=row.received_uom_qty-qty
                        self._cr.commit()

                            # stock_move_line.product_qty = 1
                        # get_stock_move_line=get_stock_move_line.search()
                        print(get_stock_move_line)

                    # for i in range(qty):



        return super(ForeignAccountMove, self).button_draft()
        # self.mapped('line_ids').remove_move_reconcile()
        # self.write({'state': 'draft'})

    def _compute_landed_count(self):
        # count = self.env['stock.landed.cost'].search([('vendor_bill_id', '=', self.id)])
        # self._cr.commit()
        # query="""select * from stock_landed_cost where vendor_bill_id={}""".format(self.id)
        # self._cr.execute(query=query)
        # foreign_vendor_bill = self._cr.fetchall()
        # if len(foreign_vendor_bill):
        #     query="""update stock_landed_cost set vendor_bill_id={} where vendor_bill_id_new={}""".format(self.id,self.id)
        #     self._cr.execute(query=query)
        #     self._cr.commit()
        # query="""select count(*) from stock_landed_cost where vendor_bill_id={}""".format(self.id)
        # self._cr.execute(query=query)
        # result=self._cr.fetchall()
        # 'vendor_bill_id', '=', self.id

        count = self.env['stock.landed.cost'].search_count([('vendor_bill_id','=',self.id)])
        print(self.id)
        # print(count)
        self.landed_cost_count = count

    def _compute_flag(self):
        active_model = self.env.context.get('active_model')
        print(active_model)
        if active_model == 'foreign.purchase.order':
            # self.landed_costs_ids=None
            self.flag = True

        else:
            self.flag = False

        # if self.state=='posted':
        #     get_account_move_line=self.invoice_line_ids
        #     get_purchase_line_id=self.foreign_purchase_id.line_ids
        #     if len(get_purchase_line_id)==0:
        #         get_purchase_line_id=self.env['foreign.purchase.order'].search([('name','=',self.invoice_origin)])
        #         for inv_pro in get_account_move_line:
        #             print(inv_pro.product_id.id)
        #             for pur_pro in get_purchase_line_id.line_ids:
        #                 print(pur_pro.product_id.id)
        #                 if inv_pro.product_id.id == pur_pro.product_id.id:
        #                     print(inv_pro.product_id.id, '-', inv_pro.quantity)
        #                     pur_pro.invoiced_uom_qty += inv_pro.quantity
        #                     pur_pro.received_uom_qty += inv_pro.quantity
        #                     pur_pro.remaining_uom_qty = pur_pro.original_uom_qty - pur_pro.received_uom_qty
        #     else:
        #         for inv_pro in get_account_move_line:
        #             print(inv_pro.product_id.id)
        #             for pur_pro in get_purchase_line_id:
        #                 print(pur_pro.product_id.id)
        #                 if inv_pro.product_id.id==pur_pro.product_id.id:
        #                     print(inv_pro.product_id.id,'-',inv_pro.quantity)
        #                     pur_pro.invoiced_uom_qty+=inv_pro.quantity
        #                     pur_pro.received_uom_qty+=inv_pro.quantity
        #                     pur_pro.remaining_uom_qty=pur_pro.original_uom_qty-pur_pro.received_uom_qty

    @api.model
    def _move_autocomplete_invoice_lines_create(self, vals_list):
        ''' During the create of an account.move with only 'invoice_line_ids' set and not 'line_ids', this method is called
        to auto compute accounting lines of the invoice. In that case, accounts will be retrieved and taxes, cash rounding
        and payment terms will be computed. At the end, the values will contains all accounting lines in 'line_ids'
        and the moves should be balanced.

        :param vals_list:   The list of values passed to the 'create' method.
        :return:            Modified list of values.
        '''
        # *******************************************OLD ONE****************************************************************
        new_vals_list = []
        for vals in vals_list:
            active_model = self.env.context.get('active_model')
            if active_model=='foreign.purchase.order':
                if vals.get('invoice_line_ids') != None:
                    for line in vals.get('line_ids'):
                        for inv_line in vals.get('invoice_line_ids'):
                            print(line)
                            print(line[2]['product_id'])
                            if inv_line[2]['product_id'] == line[2]['product_id']:
                                line[2]['bank_payment'] = inv_line[2]['bank_payment']
                                line[2]['local_payment'] = inv_line[2]['local_payment']
                                line[2]['original_uom_qty'] = inv_line[2]['original_uom_qty']
                                line[2]['invoiced_uom_qty'] = inv_line[2]['invoiced_uom_qty']
            if not vals.get('invoice_line_ids'):
                new_vals_list.append(vals)
                continue
            if vals.get('line_ids'):
                vals.pop('invoice_line_ids', None)
                new_vals_list.append(vals)
                continue
            if not vals.get('type') and not self._context.get('default_type'):
                vals.pop('invoice_line_ids', None)
                new_vals_list.append(vals)
                continue
            vals['type'] = vals.get('type', self._context.get('default_type', 'entry'))
            if not vals['type'] in self.get_invoice_types(include_receipts=True):
                new_vals_list.append(vals)
                continue

            vals['line_ids'] = vals.pop('invoice_line_ids')

            if vals.get('invoice_date') and not vals.get('date'):
                vals['date'] = vals['invoice_date']

            ctx_vals = {'default_type': vals.get('type') or self._context.get('default_type')}
            if vals.get('journal_id'):
                ctx_vals['default_journal_id'] = vals['journal_id']
                # reorder the companies in the context so that the company of the journal
                # (which will be the company of the move) is the main one, ensuring all
                # property fields are read with the correct company
                journal_company = self.env['account.journal'].browse(vals['journal_id']).company_id
                allowed_companies = self._context.get('allowed_company_ids', journal_company.ids)
                reordered_companies = sorted(allowed_companies, key=lambda cid: cid != journal_company.id)
                ctx_vals['allowed_company_ids'] = reordered_companies
            self_ctx = self.with_context(**ctx_vals)
            new_vals = self_ctx._add_missing_default_values(vals)

            move = self_ctx.new(new_vals)
            new_vals_list.append(move._move_autocomplete_invoice_lines_values())

        return new_vals_list
        # ***********************************************************************************************************
        # if 'invoice_line_ids' in vals_list[0].keys() and vals_list[0]['invoice_line_ids'][0][2]['original_uom_qty']!=0:
        #     if vals_list[0]['invoice_line_ids'][0][2]['original_uom_qty']<vals_list[0]['invoice_line_ids'][0][2]['invoiced_uom_qty']+vals_list[0]['invoice_line_ids'][0][2]['quantity']:
        #         raise ValidationError ("Invoiced quantity can not greater than original quantity")
        # else:
        #     new_vals_list = []
        #     for vals in vals_list:
        #         # new_vals_list.append(vals)
        #         # print(vals.get('invoice_line_ids')[0][2]['product_id'])
        #         if vals.get('invoice_line_ids') != None:
        #             for line in vals.get('line_ids'):
        #                 for inv_line in vals.get('invoice_line_ids'):
        #                     print(line)
        #                     print(line[2]['product_id'])
        #                     if inv_line[2]['product_id'] == line[2]['product_id']:
        #                         line[2]['bank_payment'] = inv_line[2]['bank_payment']
        #                         line[2]['local_payment'] = inv_line[2]['local_payment']
        #                         line[2]['original_uom_qty'] = inv_line[2]['original_uom_qty']
        #                         line[2]['invoiced_uom_qty'] = inv_line[2]['invoiced_uom_qty']
        #
        #             if not vals.get('invoice_line_ids'):
        #                 new_vals_list.append(vals)
        #                 continue
        #             if vals.get('line_ids'):
        #                 vals.pop('invoice_line_ids', None)
        #                 new_vals_list.append(vals)
        #                 continue
        #             if not vals.get('type') and not self._context.get('default_type'):
        #                 vals.pop('invoice_line_ids', None)
        #                 new_vals_list.append(vals)
        #                 continue
        #             vals['type'] = vals.get('type', self._context.get('default_type', 'entry'))
        #             if not vals['type'] in self.get_invoice_types(include_receipts=True):
        #                 new_vals_list.append(vals)
        #                 continue
        #
        #             vals['line_ids'] = vals.pop('invoice_line_ids')
        #
        #             if vals.get('invoice_date') and not vals.get('date'):
        #                 vals['date'] = vals['invoice_date']
        #
        #             ctx_vals = {'default_type': vals.get('type') or self._context.get('default_type')}
        #             if vals.get('journal_id'):
        #                 ctx_vals['default_journal_id'] = vals['journal_id']
        #                 # reorder the companies in the context so that the company of the journal
        #                 # (which will be the company of the move) is the main one, ensuring all
        #                 # property fields are read with the correct company
        #                 journal_company = self.env['account.journal'].browse(vals['journal_id']).company_id
        #                 allowed_companies = self._context.get('allowed_company_ids', journal_company.ids)
        #                 reordered_companies = sorted(allowed_companies, key=lambda cid: cid != journal_company.id)
        #                 ctx_vals['allowed_company_ids'] = reordered_companies
        #             self_ctx = self.with_context(**ctx_vals)
        #             new_vals = self_ctx._add_missing_default_values(vals)
        #
        #             move = self_ctx.new(new_vals)
        #             new_vals_list.append(move._move_autocomplete_invoice_lines_values())
        #
        #     return new_vals_list

    def action_view_relavent_costing(self):
        # invoice_id = self.env['foreign.stock.quant.without.serial'].search([('invoice_id', '=', self.id)], limit=1)
        return {
            'name': _('Costing'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.landed.cost',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('usl_foreign_purchase_smart.ic_foreign_invoice_tree').id, 'tree'),(self.env.ref('usl_foreign_purchase_smart.ic_invoice_form').id, 'form'),(False, 'kanban')],
            'domain': [('vendor_bill_id', '=', self.id)],
            # 'context': {'search_default_group_by_payment_method': 1}
        }

    def cal_landed_cost(self):
        invoice_id = self.env['stock.picking'].search([('origin', '=', self.invoice_origin)], limit=1)

        action = self.env.ref('usl_foreign_purchase_smart.ic_invoice_action').read()[0]
        # domain = [('id', 'in', self.landed_costs_ids.ids)]
        context = dict(self.env.context, default_vendor_bill_id=self.id, default_picking_ids=invoice_id.ids,default_vendor_bill_id_new=self.id)
        views = [(self.env.ref('usl_foreign_purchase_smart.ic_invoice_form').id, 'form'),(False, 'kanban'),(False,'tree')]
        return dict(action, context=context, views=views)
        # print("Here i am")
        # invoice_id = self.env['foreign.stock.quant.without.serial'].search([('invoice_id','=',self.id)], limit=1)
        # print(invoice_id)
        # compose_form = self.env.ref('usl_ci_wise_landed_cost.ic_invoice_form', raise_if_not_found=False).id
        # compose_tree= self.env.ref('usl_ci_wise_landed_cost.ci_invoice_tree', raise_if_not_found=False).id
        # return {
        #     'name': _('Costing'),
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'stock.landed.cost',
        #     'view_mode': 'form,tree',
        #     'view_id':False,
        #     'views': [(compose_form, 'form'), (compose_tree, 'tree')],
        #     # 'view_id': 'usl_ci_wise_landed_cost.ic_invoice_form',
        #     # 'domain': [('invoice_origin','=',self.name)],
        #     'context': {'default_transfer_foreign':invoice_id.id,
        #                 'default_vendor_bill_id':self.id}
        # }



    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        ''' Load from either an old purchase order, either an old vendor bill.

        When setting a 'purchase.bill.union' in 'purchase_vendor_bill_id':
        * If it's a vendor bill, 'invoice_vendor_bill_id' is set and the loading is done by '_onchange_invoice_vendor_bill'.
        * If it's a purchase order, 'purchase_id' is set and this method will load lines.

        /!\ All this not-stored fields must be empty at the end of this function.
        '''
        if self.purchase_vendor_bill_id.vendor_bill_id:
            self.invoice_vendor_bill_id = self.purchase_vendor_bill_id.vendor_bill_id
            self._onchange_invoice_vendor_bill()
        elif self.purchase_vendor_bill_id.purchase_order_id:
            self.purchase_id = self.purchase_vendor_bill_id.purchase_order_id
        self.purchase_vendor_bill_id = False

        if not self.purchase_id and not self.foreign_purchase_id:
            return

        # Copy partner.
        if self.purchase_id:
            self.partner_id = self.purchase_id.partner_id
            self.fiscal_position_id = self.purchase_id.fiscal_position_id
            self.invoice_payment_term_id = self.purchase_id.payment_term_id
            self.currency_id = self.purchase_id.currency_id

            # Copy purchase lines.
            po_lines = self.purchase_id.order_line - self.line_ids.mapped('purchase_line_id')
            new_lines = self.env['account.move.line']
            for line in po_lines.filtered(lambda l: not l.display_type):
                new_line = new_lines.new(line._prepare_account_move_line(self))
                new_line.account_id = new_line._get_computed_account()
                new_line._onchange_price_subtotal()
                new_lines += new_line
            new_lines._onchange_mark_recompute_taxes()

            # Compute invoice_origin.
            origins = set(self.line_ids.mapped('purchase_line_id.order_id.name'))
            self.invoice_origin = ','.join(list(origins))

            # Compute ref.
            refs = self._get_invoice_reference()
            self.ref = ', '.join(refs)

            # Compute invoice_payment_ref.
            if len(refs) == 1:
                self.invoice_payment_ref = refs[0]

            self.purchase_id = False
            self._onchange_currency()
            self.invoice_partner_bank_id = self.bank_partner_id.bank_ids and self.bank_partner_id.bank_ids[0]

        else:
            self.partner_id = self.foreign_purchase_id.partner_id
            self.fiscal_position_id = self.foreign_purchase_id.fiscal_position_id
            self.invoice_payment_term_id = self.foreign_purchase_id.payment_term_id
            self.currency_id = self.foreign_purchase_id.currency_id

            # Copy purchase lines.
            po_lines = self.foreign_purchase_id.line_ids - self.line_ids.mapped('foreign_purchase_line_id')
            new_lines = self.env['account.move.line']
            for line in po_lines.filtered(lambda l: not l.display_type):
                new_line = new_lines.new(line._prepare_account_move_line(self))
                new_line.account_id = new_line._get_computed_account()
                new_line._onchange_price_subtotal()
                new_lines += new_line
            new_lines._onchange_mark_recompute_taxes()

            # Compute invoice_origin.
            origins = set(self.line_ids.mapped('foreign_purchase_line_id.order_id.name'))
            self.invoice_origin = ','.join(list(origins))

            # Compute ref.
            refs = self._get_invoice_reference()
            self.ref = ', '.join(refs)

            # Compute invoice_payment_ref.
            if len(refs) == 1:
                self.invoice_payment_ref = refs[0]

            self.foreign_purchase_id = False
            self._onchange_currency()
            self.invoice_partner_bank_id = self.bank_partner_id.bank_ids and self.bank_partner_id.bank_ids[0]

    def _get_invoice_reference(self):
        self.ensure_one()
        if not self.foreign_purchase_id:
            vendor_refs = [ref for ref in set(self.line_ids.mapped('purchase_line_id.order_id.partner_ref')) if ref]
        else:
            self.invoice_origin=self.foreign_purchase_id.name
            vendor_refs = [ref for ref in set(self.line_ids.mapped('foreign_purchase_line_id.order_id.partner_ref')) if ref]
        if self.ref:
            return [ref for ref in self.ref.split(', ') if ref and ref not in vendor_refs] + vendor_refs
        return vendor_refs







    def write(self, vals):
        # OVERRIDE

        old_foreign_purchases = [move.mapped('foreign_purchase_id.line_ids.order_id') for move in self]


        res = super(ForeignAccountMove, self).write(vals)
        for i, move in enumerate(self):
            new_purchases = move.mapped('line_ids.foreign_purchase_line_id.order_id')
            if not new_purchases:
                continue
            diff_purchases = new_purchases - old_foreign_purchases[i]
            if diff_purchases:
                refs = ["<a href=# data-oe-model=purchase.order data-oe-id=%s>%s</a>" % tuple(name_get) for name_get in
                        diff_purchases.name_get()]
                message = _("This vendor bill has been modified from: %s") % ','.join(refs)
                move.message_post(body=message)
        return res



    def approve_invoice_order(self):
        if self.foreign_purchase_id:
            in_warehouse=self.env['stock.warehouse'].search([('is_non_saleable_warehouse','=',True),('company_id','=',self.env.user.company_id.id)])
            if in_warehouse!=None:
                user_default_warehouse=self.env['stock.location'].search([('location_id','=',in_warehouse.view_location_id.id),('name','=','Stock')]).id
            else:
                user_default_warehouse=self.env['stock.location'].search([('location_id','=',self.env.user.context_default_warehouse_id.view_location_id.id),('name','=','Stock')]).id
        else:
            user_default_warehouse = self.env['stock.location'].search(
                [('location_id', '=', self.env.user.context_default_warehouse_id.view_location_id.id),
                 ('name', '=', 'Stock')]).id
        vendor_id=self.env.user.property_stock_supplier.id

        res = super(ForeignAccountMove, self).action_post()
        self.env['account.move'].browse(self.env.context.get('active_ids'))
        for order in self:
            order.state = 'posted'
            display_message = '@{} Your sale order is Approved!'.format(order.user_id.name)
            # print(display_message)
            partner_ids = self.env['res.partner'].search([('name', 'ilike', order.user_id.name)], limit=1)
            # partner_ids = self.env['res.partner'].search(['name', '=', order.user_id.name])
            # print(partner_ids)
            order.message_post(body=display_message, subtype='mt_note', partner_ids=[(partner_ids.id)])
            # order.message_post(body=display_message, subtype='mt_note', moderator_id=order.user_id.id)
            # order.message_post(body=display_message, subtype='mt_comment')
            order.user_id.notify_success(message='Your invoice is Approved!')

        active_model = self.env.context.get('active_model')
        print(active_model)
        if active_model == 'foreign.purchase.order':
            move_id = self.env['stock.move'].search([('origin', '=', self.invoice_origin)])
            query_move = """update stock_move set state = 'done' where id in {}""".format(
                str(tuple(move_id.ids)).replace(',)', ')'))
            self._cr.execute(query=query_move)
            val_list=[]
            for account_line in self.invoice_line_ids:
                for move in move_id:
                    if move.product_id.id == account_line.product_id.id:
                        if account_line.product_id.tracking == 'serial':
                            get_undone = self.env['stock.move.line'].search([('move_id', '=', move.id),('qty_done','=',0),('product_id','=',move.product_id.id)],
                                                                            limit=account_line.quantity)

                            query_move_line = """update stock_move_line set qty_done = 1,product_qty=0,product_uom_qty=0, state='done', location_dest_id = {} where move_id = {} and product_id={} and id in {}""".format(
                                user_default_warehouse, move.id, move.product_id.id,
                                str(tuple(get_undone.ids)).replace(',)', ')'))
                            self._cr.execute(query=query_move_line)
                            self._cr.commit()

                            for stock_line in get_undone:
                                # stock_line.update({
                                #     'qty_done':1,
                                #     'product_qty':0,
                                #     'product_uom_qty':0,
                                #     'state':'done',
                                #     'location_dest_id':user_default_warehouse
                                # })
                                # query_move_line = """update stock_move_line set qty_done = 1,product_qty=0,product_uom_qty=0, state='done', location_dest_id = {} where move_id = {} and product_id={} and id={}""".format(
                                #     user_default_warehouse, move.id, stock_line.product_id.id,
                                #     stock_line.id)
                                # self._cr.execute(query=query_move_line)
                                # self._cr.commit()
                                stock_quant = self.env['stock.quant']

                                val_list = []
                                val = {
                                    'product_id': stock_line.product_id.id,
                                    'company_id': self.env.user.company_id.id,
                                    'location_id': user_default_warehouse,
                                    'quantity': 1,
                                    'in_date': datetime.today(),
                                    'create_uid': self.env.user.id,
                                    'create_date': datetime.today(),
                                    'write_uid': self.env.user.id,
                                    'write_date': datetime.today(),
                                    'inventory_quantity': 1
                                }
                                val_list.append(val)
                                val = {
                                    'product_id': stock_line.product_id.id,
                                    'company_id': self.env.user.company_id.id,
                                    'location_id': vendor_id,
                                    'quantity': -1,
                                    'in_date': datetime.today(),
                                    'create_uid': self.env.user.id,
                                    'create_date': datetime.today(),
                                    'write_uid': self.env.user.id,
                                    'write_date': datetime.today()
                                }
                                val_list.append(val)
                                stock_quant.sudo().create(val_list)

                            # if len(move_id.move_line_ids)==count:
                            # for i in range(int(account_line.quantity)):
                            #     k = 0
                            #     for stock_line in move_id.move_line_ids:
                            #         k += i
                            #         if k <= i:
                            #             if stock_line.product_id.id == account_line.product_id.id and stock_line.qty_done == 0 and stock_line.move_id.id == move.id:
                            #                 query_move_line = """update stock_move_line set qty_done = 1,product_qty=0,product_uom_qty=0, state='done', location_dest_id = {} where move_id = {} and product_id={} and id={}""".format(
                            #                     user_default_warehouse, move.id, stock_line.product_id.id,
                            #                     stock_line.id)
                            #                 self._cr.execute(query=query_move_line)
                            #                 self._cr.commit()
                            #                 stock_quant = self.env['stock.quant']
                            #
                            #                 val_list = []
                            #                 val = {
                            #                     'product_id': stock_line.product_id.id,
                            #                     'company_id': self.env.user.company_id.id,
                            #                     'location_id': user_default_warehouse,
                            #                     'quantity': 1,
                            #                     'in_date': datetime.today(),
                            #                     'create_uid': self.env.user.id,
                            #                     'create_date': datetime.today(),
                            #                     'write_uid': self.env.user.id,
                            #                     'write_date': datetime.today(),
                            #                     'inventory_quantity': 1
                            #                 }
                            #                 val_list.append(val)
                            #                 val = {
                            #                     'product_id': stock_line.product_id.id,
                            #                     'company_id': self.env.user.company_id.id,
                            #                     'location_id': vendor_id,
                            #                     'quantity': -1,
                            #                     'in_date': datetime.today(),
                            #                     'create_uid': self.env.user.id,
                            #                     'create_date': datetime.today(),
                            #                     'write_uid': self.env.user.id,
                            #                     'write_date': datetime.today()
                            #                 }
                            #                 val_list.append(val)
                            #                 stock_quant.sudo().create(val_list)
                            #                 # query_stock_quant_vendorLine="""insert into stock_quant values({},{},{},{},null,null,null,{},{},'{}',{},'{}',{},'{}',null,null,null,null)""".format(max_id,stock_line.product_id.id,self.env.user.company_id.id,vendor_id,-1,0,datetime.today(),self.env.user.id,datetime.today(),self.env.user.id,datetime.today(),None,None,None,None)
                            #                 # query_stock_quant_other = """insert into stock_quant values({},{},{},{},null,null,null,{},{},'{}',{},'{}',{},'{}',null,null,null,null)""".format(
                            #                 #     max_id+1, stock_line.product_id.id, self.env.user.company_id.id, user_default_warehouse,
                            #                 #      1, 0, datetime.today(), self.env.user.id,
                            #                 #     datetime.today(), self.env.user.id, datetime.today())
                            #                 # print(query_stock_quant_vendorLine)
                            #                 # self._cr.execute(query=query_stock_quant_vendorLine)
                            #                 # self._cr.execute(query=query_stock_quant_other)
                            #                 # self._cr.commit()
                            #                 k += 1
                            #
                            #             else:
                            #                 k = 0
                            #         else:
                            #             break
                        else:
                            qty_done = 0.0
                            # for value in move.move_line_ids:
                            #     if value.move_id.id==move.id:
                            qty_done = move.move_line_ids.qty_done + account_line.quantity
                            current_receive_qty = account_line.quantity
                            query_move_line = """update stock_move_line set qty_done = {},current_receive_qty={},product_qty=0,product_uom_qty=0, state='done', location_dest_id = {} where move_id = {} and product_id={} """.format(
                                qty_done, current_receive_qty, user_default_warehouse, move.id,
                                account_line.product_id.id)
                            self._cr.execute(query=query_move_line)
                            self._cr.commit()
                            neg_qty_done = 0.0
                            neg_qty_done = current_receive_qty * (-1)
                            stock_quant = self.env['stock.quant']

                            val_list = []
                            val = {
                                'product_id': move.product_id.id,
                                'company_id': self.env.user.company_id.id,
                                'location_id': user_default_warehouse,
                                'quantity': current_receive_qty,
                                'in_date': datetime.today(),
                                'create_uid': self.env.user.id,
                                'create_date': datetime.today(),
                                'write_uid': self.env.user.id,
                                'write_date': datetime.today(),
                                'inventory_quantity': current_receive_qty
                            }
                            val_list.append(val)
                            val = {
                                'product_id': move.product_id.id,
                                'company_id': self.env.user.company_id.id,
                                'location_id': vendor_id,
                                'quantity': neg_qty_done,
                                'in_date': datetime.today(),
                                'create_uid': self.env.user.id,
                                'create_date': datetime.today(),
                                'write_uid': self.env.user.id,
                                'write_date': datetime.today()

                            }
                            val_list.append(val)
                            stock_quant.sudo().create(val_list)

                # for move in move_id:
                #     if move.product_id.id==account_line.product_id.id:
                #         if account_line.product_id.tracking=='serial':
                #
                #             # if len(move_id.move_line_ids)==count:
                #             for i in range(int(account_line.quantity)):
                #                 k = 0
                #                 for stock_line in move_id.move_line_ids:
                #                      k += i
                #                      if k<=i:
                #                         if stock_line.product_id.id==account_line.product_id.id and stock_line.qty_done==0 and stock_line.move_id.id==move.id:
                #                             query_move_line = """update stock_move_line set qty_done = 1,product_qty=0,product_uom_qty=0, state='done', location_dest_id = {} where move_id = {} and product_id={} and id={}""".format(
                #                                 user_default_warehouse,move.id,stock_line.product_id.id,stock_line.id)
                #                             self._cr.execute(query=query_move_line)
                #                             self._cr.commit()
                #                             stock_quant=self.env['stock.quant']
                #
                #                             val_list=[]
                #                             val = {
                #                                 'product_id': stock_line.product_id.id,
                #                                 'company_id': self.env.user.company_id.id,
                #                                 'location_id': user_default_warehouse,
                #                                 'quantity': 1,
                #                                 'in_date': datetime.today(),
                #                                 'create_uid': self.env.user.id,
                #                                 'create_date': datetime.today(),
                #                                 'write_uid': self.env.user.id,
                #                                 'write_date': datetime.today(),
                #                                 'inventory_quantity': 1
                #                             }
                #                             val_list.append(val)
                #                             val = {
                #                                 'product_id': stock_line.product_id.id,
                #                                 'company_id': self.env.user.company_id.id,
                #                                 'location_id': vendor_id,
                #                                 'quantity': -1,
                #                                 'in_date': datetime.today(),
                #                                 'create_uid': self.env.user.id,
                #                                 'create_date': datetime.today(),
                #                                 'write_uid': self.env.user.id,
                #                                 'write_date': datetime.today()
                #                             }
                #                             val_list.append(val)
                #                             stock_quant.sudo().create(val_list)
                #                             # query_stock_quant_vendorLine="""insert into stock_quant values({},{},{},{},null,null,null,{},{},'{}',{},'{}',{},'{}',null,null,null,null)""".format(max_id,stock_line.product_id.id,self.env.user.company_id.id,vendor_id,-1,0,datetime.today(),self.env.user.id,datetime.today(),self.env.user.id,datetime.today(),None,None,None,None)
                #                             # query_stock_quant_other = """insert into stock_quant values({},{},{},{},null,null,null,{},{},'{}',{},'{}',{},'{}',null,null,null,null)""".format(
                #                             #     max_id+1, stock_line.product_id.id, self.env.user.company_id.id, user_default_warehouse,
                #                             #      1, 0, datetime.today(), self.env.user.id,
                #                             #     datetime.today(), self.env.user.id, datetime.today())
                #                             # print(query_stock_quant_vendorLine)
                #                             # self._cr.execute(query=query_stock_quant_vendorLine)
                #                             # self._cr.execute(query=query_stock_quant_other)
                #                             # self._cr.commit()
                #                             k+=1
                #
                #                         else:
                #                             k=0
                #                      else:
                #                         break
                #         else:
                #             qty_done=0.0
                #             # for value in move.move_line_ids:
                #             #     if value.move_id.id==move.id:
                #             qty_done=move.move_line_ids.qty_done+account_line.quantity
                #             current_receive_qty=account_line.quantity
                #             query_move_line = """update stock_move_line set qty_done = {},current_receive_qty={},product_qty=0,product_uom_qty=0, state='done', location_dest_id = {} where move_id = {} and product_id={} """.format(
                #                 qty_done,current_receive_qty,user_default_warehouse,move.id,account_line.product_id.id)
                #             self._cr.execute(query=query_move_line)
                #             self._cr.commit()
                #             neg_qty_done=0.0
                #             neg_qty_done=current_receive_qty*(-1)
                #             stock_quant = self.env['stock.quant']
                #
                #             val_list=[]
                #             val = {
                #                 'product_id': move.product_id.id,
                #                 'company_id': self.env.user.company_id.id,
                #                 'location_id': user_default_warehouse,
                #                 'quantity': current_receive_qty,
                #                 'in_date': datetime.today(),
                #                 'create_uid': self.env.user.id,
                #                 'create_date': datetime.today(),
                #                 'write_uid': self.env.user.id,
                #                 'write_date': datetime.today(),
                #                 'inventory_quantity': current_receive_qty
                #             }
                #             val_list.append(val)
                #             val = {
                #                 'product_id': move.product_id.id,
                #                 'company_id': self.env.user.company_id.id,
                #                 'location_id': vendor_id,
                #                 'quantity': neg_qty_done,
                #                 'in_date': datetime.today(),
                #                 'create_uid': self.env.user.id,
                #                 'create_date': datetime.today(),
                #                 'write_uid': self.env.user.id,
                #                 'write_date': datetime.today()
                #
                #             }
                #             val_list.append(val)
                #             stock_quant.sudo().create(val_list)




            if self.state == 'posted':
                get_account_move_line = self.invoice_line_ids
                get_purchase_line_id = self.foreign_purchase_id.line_ids
                if len(get_purchase_line_id) == 0:
                    get_purchase_line_id = self.env['foreign.purchase.order'].search(
                        [('name', '=', self.invoice_origin)])
                    for inv_pro in get_account_move_line:
                        print(inv_pro.product_id.id)
                        for pur_pro in get_purchase_line_id.line_ids:
                            print(pur_pro.product_id.id)
                            if inv_pro.product_id.id == pur_pro.product_id.id:
                                print(inv_pro.product_id.id, '-', inv_pro.quantity)
                                pur_pro.invoiced_uom_qty += inv_pro.quantity
                                pur_pro.received_uom_qty += inv_pro.quantity
                                pur_pro.remaining_uom_qty = pur_pro.original_uom_qty - pur_pro.received_uom_qty
                else:
                    for inv_pro in get_account_move_line:
                        print(inv_pro.product_id.id)
                        for pur_pro in get_purchase_line_id:
                            print(pur_pro.product_id.id)
                            if inv_pro.product_id.id == pur_pro.product_id.id:
                                print(inv_pro.product_id.id, '-', inv_pro.quantity)
                                pur_pro.invoiced_uom_qty += inv_pro.quantity
                                pur_pro.received_uom_qty += inv_pro.quantity
                                pur_pro.remaining_uom_qty = pur_pro.original_uom_qty - pur_pro.received_uom_qty
            picking_ids=self.env['stock.picking']
            self._cr.commit()
            picking_ids.button_validate_foreign(self.invoice_origin)
            move_line = self.invoice_line_ids
            stock_move_id=self.env['stock.move'].search([('origin','=',self.invoice_origin)]).ids
            account_move_for_purchase=self.env['account.move'].search([('stock_move_id','in',stock_move_id)]).invoice_line_ids.filtered(lambda ac:ac.account_id.id==move_line.account_id.id)
            move_line+=account_move_for_purchase
            move_line.check_full_reconcile_foreign()

        return res

    @api.model
    def _get_default_journal(self):
        ''' Get the default journal.
        It could either be passed through the context using the 'default_journal_id' key containing its id,
        either be determined by the default type.
        '''
        active_model = self.env.context.get('active_model')
        print(active_model)
        if active_model == 'foreign.purchase.order':
            move_type='entry'
        else:
            move_type = self._context.get('default_type', 'entry')
        journal_type = 'general'
        if move_type in self.get_sale_types(include_receipts=True):
            journal_type = 'sale'
        elif move_type in self.get_purchase_types(include_receipts=True):
            journal_type = 'purchase'

        if self._context.get('default_journal_id'):
            journal = self.env['account.journal'].browse(self._context['default_journal_id'])

            if move_type != 'entry' and journal.type != journal_type:
                raise UserError(_("Cannot create an invoice of type %s with a journal having %s as type.") % (
                move_type, journal.type))
        else:
            company_id = self._context.get('force_company',
                                           self._context.get('default_company_id', self.env.company.id))
            domain = [('company_id', '=', company_id), ('type', '=', journal_type)]

            journal = None
            if self._context.get('default_currency_id'):
                currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
                journal = self.env['account.journal'].search(currency_domain, limit=1)

            if not journal:
                journal = self.env['account.journal'].search(domain, limit=1)

            if not journal:
                error_msg = _('Please define an accounting miscellaneous journal in your company')
                if journal_type == 'sale':
                    error_msg = _('Please define an accounting sale journal in your company')
                elif journal_type == 'purchase':
                    error_msg = _('Please define an accounting purchase journal in your company')
                raise UserError(error_msg)
        return journal

class AccountMoveLine(models.Model):
    """ Override AccountInvoice_line to add the link to the purchase order line it is related to"""
    _inherit = 'account.move.line'
    foreign_purchase_line_id = fields.Many2one('foreign.purchase.order.line', 'Purchase Order Line', ondelete='set null', index=True)
    bank_payment = fields.Float(string='Bank Payment')
    local_payment = fields.Float(string='Local Payment')
    original_uom_qty=fields.Integer()
    invoiced_uom_qty=fields.Integer()


    total_bank_payment = fields.Monetary(compute='_compute_total_bank_payment', string='Total Bank Payment', store=True, digits=(12, 4))
    total_local_payment = fields.Monetary(compute='_compute_total_local_payment', store=True, string='Total Local Payment', digits=(12, 4))
    
    def _check_reconcile_validity(self):
        if self:
            return super(AccountMoveLine, self)._check_reconcile_validity()
    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue
            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())
            # active_model = self.env.context.get('active_model')
            # print(active_model)
            # if active_model == 'foreign.purchase.order':
            #     line.update(line._get_price_total_and_subtotal())
            #     line.update(line._get_fields_onchange_subtotal())
            # else:
            #     line.update(line._get_price_total_and_subtotal())
            #     line.update(line._get_fields_onchange_subtotal())

    # def _get_price_total_and_subtotal_foreign(self, price_unit=None, quantity=None, discount=None, currency=None, product=None,
    #                                   partner=None, taxes=None, move_type=None,bank_payment=None,local_payment=None):
    #     self.ensure_one()
    #     return self._get_price_total_and_subtotal_model_foreign(
    #         price_unit=price_unit or self.price_unit,
    #         quantity=quantity or self.quantity,
    #         discount=discount or self.discount,
    #         currency=currency or self.currency_id,
    #         product=product or self.product_id,
    #         partner=partner or self.partner_id,
    #         taxes=taxes or self.tax_ids,
    #         move_type=move_type or self.move_id.type,
    #         bank_payment=bank_payment or self.bank_payment,
    #         local_payment=local_payment or self.local_payment,
    #     )

    # @api.model
    # def _get_price_total_and_subtotal_model_foreign(self, price_unit, quantity, discount, currency, product, partner, taxes,
    #                                         move_type,bank_payment,local_payment):
    #     ''' This method is used to compute 'price_total' & 'price_subtotal'.
    #
    #     :param price_unit:  The current price unit.
    #     :param quantity:    The current quantity.
    #     :param discount:    The current discount.
    #     :param currency:    The line's currency.
    #     :param product:     The line's product.
    #     :param partner:     The line's partner.
    #     :param taxes:       The applied taxes.
    #     :param move_type:   The type of the move.
    #     :return:            A dictionary containing 'price_subtotal' & 'price_total'.
    #     '''
    #     res = {}
    #
    #     # Compute 'price_subtotal'.
    #     price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
    #     subtotal = quantity * price_unit_wo_discount
    #
    #     # Compute 'price_total'.
    #     if taxes:
    #         taxes_res = taxes._origin.compute_all(price_unit_wo_discount,
    #                                               quantity=quantity, currency=currency, product=product,
    #                                               partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
    #         res['price_subtotal'] = taxes_res['total_excluded']
    #         res['price_total'] = taxes_res['total_included']
    #     else:
    #         res['price_total'] = res['price_subtotal'] = subtotal
    #     # In case of multi currency, round before it's use for computing debit credit
    #     if currency:
    #         res = {k: self.round(v,bank_payment,local_payment) for k, v in res.items()}
    #     return res

    # def round(self,v=None,bank_payment=None,local_payment=None):
    #     return (bank_payment*self.env.ref('base.main_company').currency_id.rate*self.quantity)+(local_payment*self.env.ref('base.main_company').currency_id.local_currency*self.quantity)

    def check_full_reconcile_foreign(self):
        """
        This method check if a move is totally reconciled and if we need to create exchange rate entries for the move.
        In case exchange rate entries needs to be created, one will be created per currency present.
        In case of full reconciliation, all moves belonging to the reconciliation will belong to the same account_full_reconcile object.
        """
        # Get first all aml involved
        todo = self.env['account.partial.reconcile'].search_read(
            ['|', ('debit_move_id', 'in', self.ids), ('credit_move_id', 'in', self.ids)],
            ['debit_move_id', 'credit_move_id'])
        amls = set(self.ids)
        seen = set()
        while todo:
            aml_ids = [rec['debit_move_id'][0] for rec in todo if rec['debit_move_id']] + [rec['credit_move_id'][0] for
                                                                                           rec in todo if
                                                                                           rec['credit_move_id']]
            amls |= set(aml_ids)
            seen |= set([rec['id'] for rec in todo])
            todo = self.env['account.partial.reconcile'].search_read(
                ['&', '|', ('credit_move_id', 'in', aml_ids), ('debit_move_id', 'in', aml_ids), '!',
                 ('id', 'in', list(seen))], ['debit_move_id', 'credit_move_id'])
        partial_rec_ids = list(seen)
        if not amls:
            return
        else:
            amls = self.browse(list(amls))
        # If we have multiple currency, we can only base ourselves on debit-credit to see if it is fully reconciled
        currency = set([a.currency_id for a in amls if a.currency_id.id != False])
        multiple_currency = False
        if len(currency) != 1:
            currency = False
            multiple_currency = True
        else:
            currency = list(currency)[0]
        # Get the sum(debit, credit, amount_currency) of all amls involved
        total_debit = 0
        total_credit = 0
        total_amount_currency = 0
        maxdate = date.min
        to_balance = {}
        cash_basis_partial = self.env['account.partial.reconcile']
        for aml in amls:
            cash_basis_partial |= aml.move_id.tax_cash_basis_rec_id
            total_debit += aml.debit
            total_credit += aml.credit
            maxdate = max(aml.date, maxdate)
            total_amount_currency += aml.amount_currency
            # Convert in currency if we only have one currency and no amount_currency
            if not aml.amount_currency and currency:
                multiple_currency = True
                total_amount_currency += aml.company_id.currency_id._convert(aml.balance, currency, aml.company_id,
                                                                             aml.date)
            # If we still have residual value, it means that this move might need to be balanced using an exchange rate entry
            if aml.amount_residual != 0 or aml.amount_residual_currency != 0:
                if not to_balance.get(aml.currency_id):
                    to_balance[aml.currency_id] = [self.env['account.move.line'], 0]
                to_balance[aml.currency_id][0] += aml
                to_balance[aml.currency_id][
                    1] += aml.amount_residual != 0 and aml.amount_residual or aml.amount_residual_currency
        # Check if reconciliation is total
        # To check if reconciliation is total we have 3 different use case:
        # 1) There are multiple currency different than company currency, in that case we check using debit-credit
        # 2) We only have one currency which is different than company currency, in that case we check using amount_currency
        # 3) We have only one currency and some entries that don't have a secundary currency, in that case we check debit-credit
        #   or amount_currency.
        # 4) Cash basis full reconciliation
        #     - either none of the moves are cash basis reconciled, and we proceed
        #     - or some moves are cash basis reconciled and we make sure they are all fully reconciled
        digits_rounding_precision = amls[0].company_id.currency_id.rounding
        if (
                (
                        not cash_basis_partial or (
                        cash_basis_partial and all([p >= 1.0 for p in amls._get_matched_percentage().values()]))
                ) and
                (
                        currency and float_is_zero(total_amount_currency, precision_rounding=currency.rounding) or
                        multiple_currency or float_compare(total_debit, total_credit,
                                                            precision_rounding=digits_rounding_precision) == 0
                )
        ):
            exchange_move_id = False
            missing_exchange_difference = False
            # Eventually create a journal entry to book the difference due to foreign currency's exchange rate that fluctuates
            if to_balance and any(
                    [not float_is_zero(residual, precision_rounding=digits_rounding_precision) for aml, residual in
                     to_balance.values()]):
                if not self.env.context.get('no_exchange_difference'):
                    exchange_move_vals = self.env['account.full.reconcile']._prepare_exchange_diff_move(
                        move_date=maxdate, company=amls[0].company_id)
                    if len(amls.mapped('partner_id')) == 1 and amls[0].partner_id:
                        exchange_move_vals['partner_id'] = amls[0].partner_id.id
                    exchange_move = self.env['account.move'].with_context(default_type='entry').create(
                        exchange_move_vals)
                    part_reconcile = self.env['account.partial.reconcile']
                    for aml_to_balance, total in to_balance.values():
                        if total:
                            rate_diff_amls, rate_diff_partial_rec = part_reconcile.create_exchange_rate_entry(
                                aml_to_balance, exchange_move)
                            amls += rate_diff_amls
                            partial_rec_ids += rate_diff_partial_rec.ids
                        else:
                            aml_to_balance.reconcile()
                    exchange_move.post()
                    exchange_move_id = exchange_move.id
                else:
                    missing_exchange_difference = True
            if not missing_exchange_difference:
                # mark the reference of the full reconciliation on the exchange rate entries and on the entries
                self.env['account.full.reconcile'].create({
                    'partial_reconcile_ids': [(6, 0, partial_rec_ids)],
                    'reconciled_line_ids': [(6, 0, amls.ids)],
                    'exchange_move_id': exchange_move_id,
                })


    @api.depends('bank_payment')
    def _compute_total_bank_payment(self):
        for line in self:
            line.update({
                'total_bank_payment': line.quantity * line.bank_payment
            })

    @api.depends('local_payment')
    def _compute_total_local_payment(self):
        for line in self:
            line.update({
                'total_local_payment': line.quantity * line.local_payment
            })

    def _copy_data_extend_business_fields(self, values):
        # OVERRIDE to copy the 'purchase_line_id' field as well.
        super(AccountMoveLine, self)._copy_data_extend_business_fields(values)
        values['foreign_purchase_line_id'] = self.foreign_purchase_line_id.id

    def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None, partner=None, taxes=None, move_type=None):
        self.ensure_one()
        unit_price=self.price_unit
        unit_price_subtotal=0.0
        # if self.currency_id.name=='BDT':
        #     unit_price=self.price_unit
        #     unit_price_subtotal=unit_price*self.quantity
        #
        # if self.currency_id.name == 'USD':
        #     original_rate=self.env['res.currency.rate'].search([('currency_id','=',self.company_currency_id.id)]).rate
        #     unit_price=self.bank_payment*original_rate+self.local_payment*self.company_currency_id.local_currency
        #     unit_price_subtotal=unit_price*self.quantity

        return self._get_price_total_and_subtotal_model(
            price_unit=unit_price,
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            currency=currency or self.currency_id,
            product=product or self.product_id,
            partner=partner or self.partner_id,
            taxes=taxes or self.tax_ids,
            move_type=move_type or self.move_id.type,
        )
    def _get_fields_onchange_subtotal(self, price_subtotal=None, move_type=None, currency=None, company=None, date=None):
        self.ensure_one()
        return self._get_fields_onchange_subtotal_model_foreign(
            price_subtotal=price_subtotal or self.price_subtotal,
            move_type=move_type or self.move_id.type,
            currency=currency or self.currency_id,
            company=company or self.move_id.company_id,
            date=date or self.move_id.date,
        )
    @api.model
    def _get_fields_onchange_subtotal_model_foreign(self, price_subtotal, move_type, currency, company, date):
        ''' This method is used to recompute the values of 'amount_currency', 'debit', 'credit' due to a change made
        in some business fields (affecting the 'price_subtotal' field).

        :param price_subtotal:  The untaxed amount.
        :param move_type:       The type of the move.
        :param currency:        The line's currency.
        :param company:         The move's company.
        :param date:            The move's date.
        :return:                A dictionary containing 'debit', 'credit', 'amount_currency'.
        '''
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        price_subtotal *= sign
        unit_price=0.0
        if currency and currency != company.currency_id:
            active_model = self.env.context.get('active_model')
            print(active_model)
            if active_model == 'foreign.purchase.order':
            # if len(self.foreign_purchase_line_id)>0:
                # Multi-currencies.

                if self.currency_id.name == 'BDT':
                    unit_price = self.price_unit
                    # unit_price_subtotal = unit_price * self.original_uom_qty

                if self.currency_id.name == 'USD':
                    original_rate = self.env['res.currency.rate'].search(
                        [('currency_id', '=', self.company_currency_id.id)]).rate
                    unit_price = self.bank_payment * original_rate + self.local_payment * self.company_currency_id.local_currency
                     # unit_price_subtotal = unit_price * self.original_uom_qty
                balance=unit_price * self.quantity
            else:
                balance = currency._convert(price_subtotal, company.currency_id, company, date)
                return {
                    'amount_currency': price_subtotal,
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                }


            # balance = currency._convert(price_subtotal, company.currency_id, company, date)
            # balance=price_subtotal
            return {
                'amount_currency': price_subtotal,
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            }
        else:
            # Single-currency.
            return {
                'amount_currency': 0.0,
                'debit': price_subtotal > 0.0 and price_subtotal or 0.0,
                'credit': price_subtotal < 0.0 and -price_subtotal or 0.0,
            }

    # def create(self, vals_list):
    #     # active_model = self.env.context.get('active_model')
    #     # print(active_model)
    #     # if active_model == 'foreign.purchase.order':
    #     print('come')
    #     print(vals_list)
    #     User = self.env['res.users']
    #     # if len(vals_list)>0:
    #     get_type=type(vals_list)
    #     if isinstance(vals_list,list):
    #         for val in vals_list:
    #             branch = self.env['account.move'].search([('id', '=', val['move_id'])]).branch_id
    #             if 'branch_id' not in val.keys():
    #                 print(branch)
    #                 if branch:
    #                     val['branch_id'] = branch.id
    #                 else:
    #                     val['branch_id'] = User.browse(self.env.uid).branch_id.id or False
    #
    #         print(vals_list)
    #         return super(AccountMoveLine, self).create(vals_list)
    #     else:
    #         branch = self.env['account.move'].search([('id', '=', vals_list['move_id'])]).branch_id
    #         if 'branch_id' not in vals_list.keys():
    #             print(branch)
    #             if branch:
    #                 vals_list['branch_id'] = branch.id
    #             else:
    #                 vals_list['branch_id'] = User.browse(self.env.uid).branch_id.id or False
    #
    #         print(vals_list)
    #         return super(AccountMoveLine, self).create(vals_list)
