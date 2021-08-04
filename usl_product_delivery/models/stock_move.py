import random

from odoo import fields, models, api
from collections import Counter

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero


class inheritStockMove(models.Model):
    _inherit = 'stock.move'


    barcode=fields.Char(string="Barcode")
    test_field=fields.Integer()
    lot_or_serial=fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        check_company=True)
    add_btn_trigger=fields.Char()
    clear_btn_trigger=fields.Char()
    barcode_scan_btn_trigger=fields.Char()
    barcode_flag=fields.Boolean(default=False,store=False)
    manual_add_btn_trigger = fields.Char()
    manual_add_flag = fields.Boolean(default=False,store=False)
    clear_selected_btn_trigger=fields.Char()


    @api.onchange('barcode_scan_btn_trigger')
    def get_field_value(self):
        self.barcode_flag=True
        self.manual_add_flag=False



    def write(self,vals):
        if 'move_line_ids' in vals:
            move_lines=vals.get('move_line_ids')
            if isinstance(move_lines, list):
                index_array = []
                for idx,single_move_line in enumerate(move_lines):
                    if single_move_line[0]==2 and single_move_line[2]==False:
                        query=self.env['stock.move.line'].search([('id','=',single_move_line[1])])
                        if not query:
                            index_array.append(idx)
                if len(index_array)>0:
                    del move_lines[index_array[0]:]

        super(inheritStockMove, self).write(vals)

    @api.onchange('manual_add_btn_trigger')
    def show_manually_add(self):
        self.barcode_flag=False
        self.manual_add_flag=True

    @api.onchange('clear_selected_btn_trigger')
    def delete_selected_values(self):
        self.barcode_flag=self.barcode_flag
        self.manual_add_flag=self.manual_add_flag
        # self.barcode_flag=False
        # self.manual_add_flag=True
        move_lines=self.env['stock.move.line']
        del_ids = []
        del_virtuals=[]
        for index,rec in enumerate(self.move_line_ids):
            print(rec.id)

            if rec.ids:
                if rec.checkbox==True:
                    del_ids.append(rec.id)

            else:
                # self.move_line_ids._cr.commit()
                if rec.checkbox==True:
                    del_virtuals.append(rec.id)

        if del_ids:
            for delete in del_ids:
                for rec in self.move_line_ids:
                    if delete == rec.id:
                        move_lines+=self.move_line_ids.search([('id','=',rec.ids[0])])
                        # self.env['stock.move.line'].search([('id','=',rec.ids[0])]).sudo().unlink()
                        self.move_line_ids-=rec
                        rec.unlink()

                    # move_lines.unlink()
                    # move_lines=[(5,0,0)]
                        # self.move_line_ids=[(5,0,0)]

        # if del_virtuals:
        #     for delete in del_virtuals:
        #         for rec in move_lines:
        #             if delete == rec.id:
        #                 self.move_line_ids=move_lines
        #                 self.move_line_ids-=rec
        # self.move_line_ids=self.
        # view = self.env.ref('usl_product_delivery.view_stock_move_operations_for_delivery')
        # return {
        #     # 'context': self.env.context,
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'stock.move',
        #     'res_id': self.id,
        #     'views': [(view.id, 'form')],
        #     'view_id': view.id,
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        #     'context': dict(
        #         # self.env.context,
        #         default_barcode_flag=True,
        #         default_manual_add_flag=False,
        #     ),
        # }




    @api.onchange('barcode_scan_btn_trigger')
    def show_barcode_field(self):
        if self.barcode_scan_btn_trigger:
            self.barcode_flag=True
            self.manual_add_flag=False





    def set_lines(self):
        lot_id=self.env['stock.production.lot'].search([('name','=',self.barcode)])
        if not lot_id:
            raise ValidationError(_("This lot/serial does not exists in system!!!"))


        else:
            match_lot_product=self.env['stock.quant'].search([('lot_id','=',lot_id.id),('product_id','=',self.product_id.id)])
            if not match_lot_product:
                raise ValidationError(_("Selected product and lot/serial doesn't match!!!"))

            else:
                if self.product_uom_qty < len(self.move_line_ids) + 1:
                    raise ValidationError(_("You can not assign more lot/serial from your initial demand quantity!!!"))

                for rec in self.move_line_ids:
                    if lot_id.id == rec.lot_id.id:
                        raise ValidationError(
                            _("Already same lot/serial is use in below line!!!"))
                if lot_id:
                    lot_get_id = self.env['stock.quant'].sudo().search(
                        [('lot_id', '=', lot_id.id), ('location_id', '=', self.location_id.id),
                         ('reserved_quantity', '=', 1)])
                    if lot_get_id:
                        if lot_get_id.write_uid.id != self.env.user.id:
                            get_ref = self.env['stock.move.line'].search(
                                [('lot_id', '=', lot_id.id), ('location_id', '=', self.location_id.id)],
                                limit=1)
                            if get_ref:
                                get_who_reserved = get_ref.write_uid.name
                                reference = get_ref.reference
                                raise ValidationError(
                                    _("This product reserved by: '" + get_who_reserved + "',in delivery number: '" + reference + "'"))

                line_array = []
                line_array1=[]
                quantity = 0
                if self.product_id.tracking == 'serial':
                    quantity = 1
                else:
                    quantity = self.product_uom_qty

                val = (0, 0, {
                    'location_id': self.location_id.id,
                    'lot_id': lot_id.id,
                    'product_uom_qty': quantity,
                    'picking_id': self.picking_id.id,
                    'product_uom_id': lot_id.product_uom_id.id,
                    'product_id': self.product_id.id,
                    'reference': self.reference,
                    'move_id': self.ids[0],
                    # 'product_qty':quantity

                })
                val1 = {
                    'location_id': self.location_id.id,
                    'lot_id': lot_id.id,
                    'product_uom_qty': quantity,
                    'picking_id': self.picking_id.id,
                    'product_uom_id': lot_id.product_uom_id.id,
                    'product_id': self.product_id.id,
                    'reference': self.reference,
                    'move_id': self.ids[0],
                    # 'product_qty': quantity
                }
                line_array.append(val)
                line_array1.append(val1)

                self.write({'move_line_ids': line_array,'barcode':''})
                # self.move_line_ids+=self.env['stock.move.line'].create(line_array1)
                for rec in self.move_line_ids:
                    quant_id = self.env['stock.quant'].sudo().search(
                        [('lot_id', '=', rec.lot_id.id), ('location_id', '=', rec.location_id.id)])
                    quant_id.write({'reserved_quantity': rec.product_uom_qty})

                self.barcode_flag = True
                view = self.env.ref('usl_product_delivery.view_stock_move_operations_for_delivery')
                return {
                    # 'context': self.env.context,
                    'name': _('Detailed Operations'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.move',
                    'res_id': self.id,
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': dict(
                        self.env.context,
                        default_barcode_flag=True,
                        default_manual_add_flag=False,
                    ),
                }



    @api.onchange('clear_btn_trigger')
    def clear_all_line(self):
        if len(self.move_line_ids.ids) > 0:
            self.move_line_ids.unlink()
            self.move_line_ids=[(5,0,0)]

        # else:
        #     for rec in self:
        #         rec.write({'move_line_ids': [(5, 0, 0)]})


    def set_line_value(self):
        if  self.product_uom_qty<len(self.move_line_ids)+1:
            raise ValidationError(_("You can not assign more lot/serial from your initial demand quantity!!!"))
        for rec in self.move_line_ids:
            if self.lot_or_serial.id==rec.lot_id.id:
                raise ValidationError(_("Already same lot/serial is use in below line!!!"))
        if self.lot_or_serial:
            lot_get_id = self.env['stock.quant'].sudo().search(
                [('lot_id', '=', self.lot_or_serial.id), ('location_id', '=', self.location_id.id), ('reserved_quantity', '=', 1)])
            if lot_get_id:
                if lot_get_id.write_uid.id!=self.env.user.id:
                    get_ref = self.env['stock.move.line'].search(
                        [('lot_id', '=', self.lot_or_serial.id), ('location_id', '=', self.location_id.id)], limit=1)
                    if get_ref:
                        get_who_reserved = get_ref.write_uid.name
                        reference = get_ref.reference
                        raise ValidationError(
                            _("This product reserved by: '" + get_who_reserved + "',in delivery number: '" + reference + "'"))
        else:
            raise ValidationError(
                _("Lot/Serial is mandatory for add a new line!!!"))

        line_array=[]
        line_array1=[]
        quantity=0
        if self.product_id.tracking=='serial':
            quantity=1
        else:
            quantity=self.product_uom_qty
        val=(0,0,{
            'location_id':self.location_id.id,
            'lot_id':self.lot_or_serial.id,
            'product_uom_qty':quantity,
            'picking_id':self.picking_id.id,
            'product_uom_id':self.lot_or_serial.product_uom_id.id,
            'product_id': self.product_id.id,
            'reference':self.reference,
            'move_id':self.ids[0],
            # 'product_qty':quantity


        })
        val1={
            'location_id': self.location_id.id,
            'lot_id': self.lot_or_serial.id,
            'product_uom_qty': quantity,
            'picking_id': self.picking_id.id,
            'product_uom_id': self.lot_or_serial.product_uom_id.id,
            'product_id': self.product_id.id,
            'reference': self.reference,
            'move_id': self.ids[0],
            # 'product_qty': quantity
        }
        line_array.append(val)
        line_array1.append(val1)

        self.write({'move_line_ids':line_array})
        # self.update(self.move_line_ids =line_array)
        # self.move_line_ids+=self.env['stock.move.line'].create(line_array1)
        for rec in self.move_line_ids:
            quant_id = self.env['stock.quant'].sudo().search(
                [('lot_id', '=', rec.lot_id.id), ('location_id', '=', rec.location_id.id)])
            quant_id.write({'reserved_quantity': rec.product_uom_qty})

        query="""update stock_move set lot_or_serial=null where id={}""".format(self.ids[0])
        self._cr.execute(query=query)
        self._cr.commit()

        view = self.env.ref('usl_product_delivery.view_stock_move_operations_for_delivery')
        return {
            # 'context': self.env.context,
            'name': _('Detailed Operations'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'res_id': self.id,
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': dict(
                self.env.context,
                default_manual_add_flag=True,
                default_barcode_flag=False,

            ),
        }
        # return {"domain": {"move_line_ids": [("id", "in", self.move_line_ids.ids)]}}
        # self.move_line_ids=self.move_line_ids


    def custom_save(self):
        self.manual_add_flag=False
        self.barcode_flag=False
        for rec in self.move_line_ids:
            quant_id = self.env['stock.quant'].sudo().search(
                [('lot_id', '=', rec.lot_id.id), ('location_id', '=', rec.location_id.id)])
            quant_id.write({'reserved_quantity': rec.product_uom_qty})
            rec.write({'checkbox':False})
        self.write({})

    def action_show_details(self):
        if self.picking_code=="outgoing":
            self.ensure_one()
            get_undone_lot=self.env['stock.quant'].search([('product_id','=',self.product_id.id),('location_id','=',self.location_id.id),('company_id','=',self.company_id.id),('quantity','!=',0)]).lot_id

            if self.picking_id.picking_type_id.show_reserved:
                view = self.env.ref('usl_product_delivery.view_stock_move_operations_for_delivery')
            else:
                view = self.env.ref('stock.view_stock_move_nosuggest_operations')

            picking_type_id = self.picking_type_id or self.picking_id.picking_type_id

            # self.move_line_ids.unlink()
            return {
                'name': _('Detailed Operations'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.move',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': self.id,
                'context': dict(
                    self.env.context,
                    show_owner=self.picking_type_id.code != 'incoming',
                    show_lots_m2o=self.has_tracking != 'none' and (
                            picking_type_id.use_existing_lots or self.state == 'done' or self.origin_returned_move_id.id),
                    # able to create lots, whatever the value of ` use_create_lots`.
                    show_lots_text=self.has_tracking != 'none' and picking_type_id.use_create_lots and not picking_type_id.use_existing_lots and self.state != 'done' and not self.origin_returned_move_id.id,
                    show_source_location=self.picking_type_id.code != 'incoming',
                    show_destination_location=self.picking_type_id.code != 'outgoing',
                    show_package=not self.location_id.usage == 'supplier',
                    show_reserved_quantity=self.state != 'done' and not self.picking_id.immediate_transfer and self.picking_type_id.code != 'incoming',
                    show_lot_or_serial=get_undone_lot.ids,
                    default_barcode_flag=False,
                    default_manual_add_flag=False,

                ),
        }
        else:
            return super(inheritStockMove, self).action_show_details()


class inheritStockMoveline(models.Model):
    _inherit = 'stock.move.line'

    checkbox = fields.Boolean()
    # delete_function_fld = fields.Char("X")

    # @api.onchange('checkbox')
    # def set_flag(self):
    #     print('********')
    #     self=(1,self.ids[0],{'checkbox':self.checkbox})




