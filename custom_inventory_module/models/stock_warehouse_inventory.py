from odoo import api, fields, models, _

class StockWareHouseInheritForReturn(models.Model):
    _inherit = 'stock.warehouse'

    return_type_id = fields.Many2one('stock.picking.type', string="Return Operation Type")

    def _get_sequence_values(self):
        sequence_values = super(StockWareHouseInheritForReturn, self)._get_sequence_values()
        sequence_values.update({
            'return_type_id': {
                'name': self.name + ' ' + _('Picking Return'),
                'prefix': self.code + '/RETURN/',
                'padding': 5,
                'company_id': self.company_id.id,
            }
        })
        return sequence_values

    def _get_picking_type_update_values(self):
        picking_type_update_values = super(StockWareHouseInheritForReturn, self)._get_picking_type_update_values()
        picking_type_update_values.update({
            'return_type_id': {'default_location_src_id': self.lot_stock_id.id}
        })
        return picking_type_update_values

    def _get_picking_type_create_values(self, max_sequence):
        picking_type_create_values, max_sequence = super(StockWareHouseInheritForReturn, self)._get_picking_type_create_values(max_sequence)
        picking_type_create_values.update({
            'return_type_id': {
                'name': _('Return'),
                'code': 'incoming',
                'default_location_src_id': self.lot_stock_id.id,
                'default_location_dest_id': self.env.ref('stock.stock_location_customers').id,
                'sequence': max_sequence + 2,
                'sequence_code': 'RETURN',
                'company_id': self.company_id.id,
            }
        })
        return picking_type_create_values, max_sequence + 3

    # def _get_picking_type_create_values(self, max_sequence):
    #     """ When a warehouse is created this method return the values needed in
    #     order to create the new picking types for this warehouse. Every picking
    #     type are created at the same time than the warehouse howver they are
    #     activated or archived depending the delivery_steps or reception_steps.
    #     """
    #     input_loc, output_loc = self._get_input_output_locations(self.reception_steps, self.delivery_steps)
    #     return {
    #         'in_type_id': {
    #             'name': _('Receipts'),
    #             'code': 'incoming',
    #             'use_create_lots': True,
    #             'use_existing_lots': False,
    #             'default_location_src_id': False,
    #             'sequence': max_sequence + 1,
    #             'barcode': self.code.replace(" ", "").upper() + "-RECEIPTS",
    #             'show_reserved': False,
    #             'sequence_code': 'IN',
    #             'company_id': self.company_id.id,
    #         }, 'out_type_id': {
    #             'name': _('Delivery Orders'),
    #             'code': 'outgoing',
    #             'use_create_lots': False,
    #             'use_existing_lots': True,
    #             'default_location_dest_id': False,
    #             'sequence': max_sequence + 5,
    #             'barcode': self.code.replace(" ", "").upper() + "-DELIVERY",
    #             'sequence_code': 'OUT',
    #             'company_id': self.company_id.id,
    #         }, 'pack_type_id': {
    #             'name': _('Pack'),
    #             'code': 'internal',
    #             'use_create_lots': False,
    #             'use_existing_lots': True,
    #             'default_location_src_id': self.wh_pack_stock_loc_id.id,
    #             'default_location_dest_id': output_loc.id,
    #             'sequence': max_sequence + 4,
    #             'barcode': self.code.replace(" ", "").upper() + "-PACK",
    #             'sequence_code': 'PACK',
    #             'company_id': self.company_id.id,
    #         }, 'pick_type_id': {
    #             'name': _('Pick'),
    #             'code': 'internal',
    #             'use_create_lots': False,
    #             'use_existing_lots': True,
    #             'default_location_src_id': self.lot_stock_id.id,
    #             'sequence': max_sequence + 3,
    #             'barcode': self.code.replace(" ", "").upper() + "-PICK",
    #             'sequence_code': 'PICK',
    #             'company_id': self.company_id.id,
    #         }, 'int_type_id': {
    #             'name': _('Internal Transfers'),
    #             'code': 'internal',
    #             'use_create_lots': False,
    #             'use_existing_lots': True,
    #             'default_location_src_id': self.lot_stock_id.id,
    #             'default_location_dest_id': self.lot_stock_id.id,
    #             'active': self.reception_steps != 'one_step' or self.delivery_steps != 'ship_only' or self.user_has_groups('stock.group_stock_multi_locations'),
    #             'sequence': max_sequence + 2,
    #             'barcode': self.code.replace(" ", "").upper() + "-INTERNAL",
    #             'sequence_code': 'INT',
    #             'company_id': self.company_id.id,
    #         },
    #                'int_type_id': {
    #                    'name': _('Internal Return'),
    #                    'code': 'internal',
    #                    'use_create_lots': False,
    #                    'use_existing_lots': True,
    #                    'default_location_src_id': self.lot_stock_id.id,
    #                    'default_location_dest_id': self.lot_stock_id.id,
    #                    'active': self.reception_steps != 'one_step' or self.delivery_steps != 'ship_only' or self.user_has_groups(
    #                        'stock.group_stock_multi_locations'),
    #                    'sequence': max_sequence + 5,
    #                    'barcode': self.code.replace(" ", "").upper() + "-RETURN",
    #                    'sequence_code': 'RETURN',
    #                    'company_id': self.company_id.id,
    #                },
    #     }, max_sequence + 6
    #
    # def _get_sequence_values(self):
    #     """ Each picking type is created with a sequence. This method returns
    #     the sequence values associated to each picking type.
    #     """
    #     return {
    #         'in_type_id': {
    #             'name': self.name + ' ' + _('Sequence in'),
    #             'prefix': self.code + '/IN/', 'padding': 5,
    #             'company_id': self.company_id.id,
    #         },
    #         'out_type_id': {
    #             'name': self.name + ' ' + _('Sequence out'),
    #             'prefix': self.code + '/OUT/', 'padding': 5,
    #             'company_id': self.company_id.id,
    #         },
    #         'pack_type_id': {
    #             'name': self.name + ' ' + _('Sequence packing'),
    #             'prefix': self.code + '/PACK/', 'padding': 5,
    #             'company_id': self.company_id.id,
    #         },
    #         'pick_type_id': {
    #             'name': self.name + ' ' + _('Sequence picking'),
    #             'prefix': self.code + '/PICK/', 'padding': 5,
    #             'company_id': self.company_id.id,
    #         },
    #         'int_type_id': {
    #             'name': self.name + ' ' + _('Sequence internal'),
    #             'prefix': self.code + '/INT/', 'padding': 5,
    #             'company_id': self.company_id.id,
    #         },
    #         'int_type_id': {
    #             'name': self.name + ' ' + _('Sequence return'),
    #             'prefix': self.code + '/Return/', 'padding': 5,
    #             'company_id': self.company_id.id,
    #         },
    #     }
