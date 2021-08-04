from odoo import fields, models, api
from collections import Counter

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero


class ModelName(models.Model):
    _inherit = 'stock.move.line'

    replica_lot_id=fields.Float()
    #changed


    def check_lot_id_reserve_or_not(self, lot_id=None, lot_name=None):
        print('check_lot_id_reserve_or_not')
        if lot_id==False:
            # return True
            raise ValidationError(_("Please Provide Lot/Serial Number!!!"))
        if lot_name and not lot_id:
            lot_id = self.env['stock.production.lot'].sudo().search('name', '=', lot_name)
        lot_get_id = self.env['stock.quant'].sudo().search([('lot_id', '=', lot_id), ('location_id','=',self.location_id.id),('reserved_quantity', '=', 1)])

        if lot_get_id:
            if lot_get_id.write_uid.id==self.env.user.id:
                return True
            else:
                # query="""select p.name from res_"""
                get_ref=self.env['stock.move.line'].search([('lot_id','=',lot_id),('location_id','=',self.location_id.id)],limit=1)
                get_who_reserved=get_ref.write_uid.name
                reference=get_ref.reference
                raise ValidationError(_("This product reserved by: '"+get_who_reserved+ "',in delivery number: '"+reference+"'"))
        # else:
        #     get_ref = self.env['stock.move.line'].search(
        #         [('lot_id', '=', lot_id), ('location_id', '=', self.location_id.id)], limit=1)
        #     if get_ref:
        #         get_who_reserved = get_ref.write_uid.name
        #         reference = get_ref.reference
        #         raise ValidationError(
        #             _("This product reserved by: '" + get_who_reserved + "',in delivery number: '" + reference + "'"))
        #     else:
        #         return False
        return False

    # @api.onchange('lot_name', 'lot_id')
    # def onchange_serial_number(self):
    #     """ When the user is encoding a move line for a tracked product, we apply some logic to
    #     help him. This includes:
    #         - automatically switch `qty_done` to 1.0
    #         - warn if he has already encoded `lot_name` in another move line
    #     """
    #     res = {}
    #     if self.product_id.tracking == 'serial':
    #         # if not self.qty_done:
    #         #     self.qty_done = 1
    #         if not self.product_uom_qty:
    #             self.product_uom_qty = 1
    #
    #         message = None
    #         if self.lot_name or self.lot_id:
    #             move_lines_to_check = self._get_similar_move_lines() - self
    #             if self.lot_name:
    #                 counter = Counter([line.lot_name for line in move_lines_to_check])
    #                 if counter.get(self.lot_name) and counter[self.lot_name] > 1:
    #                     message = _(
    #                         'You cannot use the same serial number twice. Please correct the serial numbers encoded.')
    #                 if self.check_lot_id_reserve_or_not(self.lot_name):
    #                     message = _(
    #                         'this lot id is reserved')
    #
    #             elif self.lot_id:
    #                 counter = Counter([line.lot_id.id for line in move_lines_to_check])
    #                 if counter.get(self.lot_id.id) and counter[self.lot_id.id] > 1:
    #                     message = _(
    #                         'You cannot use the same serial number twice. Please correct the serial numbers encoded.')
    #                 if self.check_lot_id_reserve_or_not(self.lot_id.id):
    #                     message = _(
    #                         'this lot id is reserved')
    #
    #         if message:
    #             res['warning'] = {'title': _('Warning'), 'message': message}
    #     return res

    @api.onchange('lot_name', 'lot_id')
    def onchange_serial_number(self):
        """ When the user is encoding a move line for a tracked product, we apply some logic to
        help him. This includes:
            - automatically switch `qty_done` to 1.0
            - warn if he has already encoded `lot_name` in another move line
        """
        # active_model=self.env.context.get("active_model")
        if  self.picking_code!='incoming':
            if self.ids:
                query = """select lot_id from stock_move_line where id={}""".format(self.ids[0])
                self._cr.execute(query=query)
                previous_lot = self._cr.fetchone()
                previous_lot_details = self.env['stock.production.lot'].search([('id', '=', previous_lot[0])])

            if self.picking_id.show_operations:
                for rec in self.move_id.move_line_ids.lot_id:
                    if self.lot_id.id == rec.id:
                        raise ValidationError("This Product is already selected in this transfer !")

            res = {}
            if self.product_id.tracking == 'serial':
                if self.picking_code == 'incoming':
                    if not self.qty_done:
                        self.qty_done = 1
                if self.picking_code == 'internal':
                    if not self.product_uom_qty:
                        self.product_uom_qty = 1
                        self.qty_done = 1
                    if self.lot_id:
                        if self.check_lot_id_reserve_or_not(self.lot_id.id):
                            quant_quantity_zero_or_not = self.env['stock.quant'].search(
                                [('lot_id', '=', previous_lot_details.id), ('location_id', '=', self.location_id.id)])
                            if quant_quantity_zero_or_not.quantity > 0 and quant_quantity_zero_or_not.reserved_quantity > 0:
                                stock_picking = self.env['stock.quant']
                                stock_picking._update_reserved_quantity(self.product_id, self.location_id, -1,
                                                                        previous_lot_details,
                                                                        None, None, True)

                            # if self.lot_id:
                            # lot_get_id = self.env['stock.quant'].sudo().search(
                            #     [('lot_id', '=', self.lot_id.id), ('location_id', '=', self.location_id.id),
                            #      ('reserved_quantity', '=', 1)]).id
                            # query = """update stock_quant set reserved_quantity = 0 where id = {}""".format(lot_get_id)
                            # self._cr.execute(query=query)
                            #
                            # query = """update stock_quant set reserved_quantity = 1 where id = {}""".format(lot_get_id)
                            # self._cr.execute(query=query)

                            query = """update stock_move_line set product_uom_qty=1 ,lot_id={} where id={}""".format(
                                self.lot_id.id, self.ids[0])
                            self._cr.execute(query=query)
                            # else:
                            #     query = """update stock_move_line set product_uom_qty=1 ,lot_id=null where id={}""".format(
                            #          self.ids[0])
                            #     self._cr.execute(query=query)





                        else:
                            stock_picking = self.env['stock.quant']
                            get_stock_quant=self.env['stock.quant'].search([('lot_id','=',previous_lot_details.id),('location_id','=',self.location_id.id)])
                            if  get_stock_quant.quantity!=0 and get_stock_quant.reserved_quantity!=0:
                                stock_picking._update_reserved_quantity(self.product_id, self.location_id, -1, previous_lot_details,
                                                                        None, None, True)
                            query = """update stock_move_line set product_uom_qty=1 ,lot_id={} where id={}""".format(
                                self.lot_id.id, self.ids[0])
                            self._cr.execute(query=query)
                            query = """update stock_quant set reserved_quantity=1 where lot_id = {} and location_id = {}""".format(
                                self.lot_id.id, self.location_id.id)
                            self._cr.execute(query=query)
                    #     lot_name = self.env['stock.production.lot'].search([('id', '=', self.lot_id.id)]).name
                    #     lot_get_id = self.env['stock.quant'].sudo().search(
                    #         [('lot_id', '=', self.lot_id.id), ('location_id', '=', self.location_id.id),
                    #          ('reserved_quantity', '=', 1)]).id
                    #     query = """update stock_quant set reserved_quantity = 0 where id = {}""".format(lot_get_id)
                    #     self._cr.execute(query=query)
                    #     # self._cr.commit()
                    #     lot_set_id = self.env['stock.production.lot'].search([('id', '=', self.lot_id.id)])
                    #     # query = """select lot_id from stock_move_line where lot_id = {} and reference like '%OUT%'""".format(
                    #     #     lot_set_id.id)
                    #     # self._cr.execute(query=query)
                    #     # result = self._cr.fetchone()
                    #
                    #     query = """update stock_move_line set lot_id = null where lot_id = {} and reference like '%OUT%'""".format(
                    #         lot_set_id.id)
                    #     self._cr.execute(query=query)
                    #     # self._cr.commit()
                    #     # query = """update stock_quant set reserved_quantity = 1 where id = {}""".format(lot_get_id)
                    #     # self._cr.execute(query=query)
                    #     # self._cr.commit()
                    #
                    #     # existing_lot_name = self.env['stock.production.lot'].search([('id', '=', result[0])]).name
                    #     # for rec in self.move_id.move_line_ids.lot_id:
                    #     #     if rec.name == lot_name:
                    #     #         rec = lot_set_id.id
                    #
                    #     # raise ValidationError('this serial is already reserved by some one')
                    # else:
                    #     query = """update stock_quant set reserved_quantity=1 where lot_id = {} and location_id = {}""".format(
                    #         self.lot_id.id, self.location_id.id)
                    #     self._cr.execute(query=query)
                if self.picking_code == 'outgoing':
                    # for rec in self.move_id.move_line_ids:
                    #     query="select lot_id from stock_move_line where id={}".format(self.ids[0])
                    #     self._cr.execute(query=query)
                    #     lot=self._cr.fetchone()
                    #     if rec.lot_id.id==lot[0]:
                    #     # if self.lot_id.id == rec.id:
                    #         raise ValidationError("This Product is already selected in below line!")
                    # if not self.qty_done:
                    #     self.qty_done = 1
                    if not self.product_uom_qty:
                        print(self.ids[0])
                        query="""update stock_move_line set product_uom_qty=1 where id={}""".format(self.ids[0])
                        self._cr.execute(query=query)

                        # self.product_uom_qty = 1
                        self._cr.commit()
                    if self.check_lot_id_reserve_or_not(self.lot_id.id):
                        quant_quantity_zero_or_not=self.env['stock.quant'].search([('lot_id','=',previous_lot_details.id),('location_id','=',self.location_id.id)])
                        if quant_quantity_zero_or_not.quantity>0 and quant_quantity_zero_or_not.reserved_quantity>0:
                            stock_picking = self.env['stock.quant']
                            stock_picking._update_reserved_quantity(self.product_id, self.location_id, -1, previous_lot_details,
                                                                    None, None, True)

                        # if self.lot_id:
                        # lot_get_id = self.env['stock.quant'].sudo().search(
                        #     [('lot_id', '=', self.lot_id.id), ('location_id', '=', self.location_id.id),
                        #      ('reserved_quantity', '=', 1)]).id
                        # query = """update stock_quant set reserved_quantity = 0 where id = {}""".format(lot_get_id)
                        # self._cr.execute(query=query)
                        #
                        #
                        #
                        # query = """update stock_quant set reserved_quantity = 1 where id = {}""".format(lot_get_id)
                        # self._cr.execute(query=query)

                        query="""update stock_move_line set product_uom_qty=1 ,lot_id={} where id={}""".format(self.lot_id.id,self.ids[0])
                        self._cr.execute(query=query)
                        # else:
                        #     query = """update stock_move_line set product_uom_qty=1 ,lot_id=null where id={}""".format(
                        #          self.ids[0])
                        #     self._cr.execute(query=query)





                    else:
                        stock_picking = self.env['stock.quant']
                        get_quant_data = self.env['stock.quant'].search(
                            [('lot_id', '=', previous_lot_details.id), ('location_id', '=', self.location_id.id),
                             ('product_id', '=', self.product_id.id)])
                        if get_quant_data.reserved_quantity == 1 :
                            stock_picking._update_reserved_quantity(self.product_id, self.location_id, -1, previous_lot_details,
                                                                    None, None, True)
                        query = """update stock_move_line set product_uom_qty=1 ,lot_id={} where id={}""".format(
                            self.lot_id.id, self.ids[0])
                        self._cr.execute(query=query)
                        query = """update stock_quant set reserved_quantity=1 where lot_id = {} and location_id = {}""".format(
                            self.lot_id.id, self.location_id.id)
                        self._cr.execute(query=query)

                        # query = """update stock_quant set reserved_quantity=0 where lot_id={}""".format(self.replica_lot_id)
                        # self._cr.execute(query=query)
                        # query="""update stock_move_line set replica_lot_id={} where id={}""".format(self.lot_id.id,self.ids[0])
                        # self._cr.execute(query=query)


                message = None
                if self.lot_name or self.lot_id:
                    move_lines_to_check = self._get_similar_move_lines() - self
                    if self.lot_name:
                        counter = Counter([line.lot_name for line in move_lines_to_check])
                        if counter.get(self.lot_name) and counter[self.lot_name] > 1:
                            message = _(
                                'You cannot use the same serial number twice. Please correct the serial numbers encoded.')
                        if self.check_lot_id_reserve_or_not(self.lot_name):
                            raise ValidationError('this serial is already reserved by some one')
                            message = _(
                                'this lot id is reserved')

                    elif self.lot_id:
                        counter = Counter([line.lot_id.id for line in move_lines_to_check])
                        if counter.get(self.lot_id.id) and counter[self.lot_id.id] > 1:
                            raise ValidationError(_(
                                'You cannot use the same serial number twice. Please correct the serial numbers encoded.'))



                if message:
                    res['warning'] = {'title': _('Warning'), 'message': message}
            return res

        else:
            if self.product_id.tracking == 'serial':
                if self.picking_code == 'incoming':
                    if self.return_lot_ids:
                        return_list = list()
                        for return_lot in self.return_lot_ids:
                            return_list.append(return_lot.ids[0])
                        if self.lot_id.id not in return_list:
                            raise ValidationError('Please Select a Serial that you have Sold to that Customer !')
                        elif self.lot_id.id in return_list:
                            raise ValidationError('You have already selected this Serial !')
                    if not self.qty_done:
                        self.qty_done = 1

    def create(self, vals_list):

        # if not isinstance(vals_list, list):
        #     return super(ModelName, self).create(vals_list)
        # print('stock move line before (create) : ', vals_list)
        # for val in vals_list:
        #     val['product_uom_qty'] = 1
        # print('stock move line before (create) : ', vals_list)
        # active=self.env.context.get('active_model')
        # if len(vals_list)>0 and self.env.context.get('active_model')=='sale.order':
        #     for val in vals_list:
        #         val['replica_lot_id'] = val['lot_id']
        return super(ModelName, self).create(vals_list)

    def write(self, vals):
        print('stock move line (write) : ', vals)
        return super(ModelName, self).write(vals)
