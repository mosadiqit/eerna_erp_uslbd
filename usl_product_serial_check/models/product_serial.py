from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductSerialReserved(models.Model):
    _name = 'product.serial.reserved'

    lot_id = fields.Many2one('stock.production.lot',string="Serial Number")
    serial_status = fields.One2many('product.serial.reserved.line','product_serial')

    @api.onchange('lot_id')
    def get_lot_details(self):
        if self.lot_id:
            # stock_production_lot = self.env['stock.production.lot'].search([('product_id','=',self.product_id.id)])
            stock_quant_id = self.env['stock.quant'].search([('lot_id','=',self.lot_id.id),('reserved_quantity','=',1)])
            print(stock_quant_id)

            for rec in self:
                lines = list()
                if stock_quant_id:
                    if len(rec.serial_status) >= 1:
                        rec.serial_status = [(5, 0, 0)]
                        for line in stock_quant_id:
                            vals = {
                                'location_id': line.location_id.id,
                                'product_id':line.product_id.id,
                                'lot_id': line.lot_id.id,
                                'reserved_status': True
                            }
                            lines.append((0, 0, vals))
                        rec.serial_status = lines
                    else:
                        for line in stock_quant_id:
                            vals = {
                                'location_id': line.location_id.id,
                                'product_id':line.product_id.id,
                                'lot_id': line.lot_id.id,
                                'reserved_status': True
                            }
                            lines.append((0, 0, vals))
                        rec.serial_status = lines
                else:
                    rec.serial_status = [(5,0,0)]



class SerialLineReserved(models.Model):
    _name = 'product.serial.reserved.line'

    location_id = fields.Many2one('stock.location',string="Location")
    lot_id = fields.Many2one('stock.production.lot',string="Serial Number")
    product_id = fields.Many2one('product.product',string="Product")
    reserved_status = fields.Boolean(string="Status")
    product_serial = fields.Many2one('product.serial.reserved')