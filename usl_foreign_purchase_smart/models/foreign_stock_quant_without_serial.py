from odoo import api, fields, models


class ForeignStockQuant(models.Model):
    _name = 'foreign.stock.quant.without.serial'
    # _rec_name = 'name'
    _description = 'New Description'



    invoice_id = fields.Integer(string="Invoice Id")
    foreign_purchase_id = fields.Integer(string="Foreign PO")
    name = fields.Char(string="Name")
    product_id = fields.Integer(string='Product')
    price = fields.Float(string="Price")
    # product_tmpl_id = fields.Many2one(
    #     'product.template', string='Product Template',
    #     related='product_id.product_tmpl_id', readonly=False)
    # product_uom_id = fields.Many2one(
    #     'uom.uom', 'Unit of Measure',
    #     readonly=True)
    company_id = fields.Many2one(related='location_id.company_id', string='Company', store=True, readonly=True)
    location_id = fields.Many2one(
        'stock.location', 'Location',
        auto_join=True, ondelete='restrict', readonly=True,index=True, check_company=True)
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        ondelete='restrict', readonly=True, check_company=True)
    # package_id = fields.Many2one(
    #     'stock.quant.package', 'Package',
    #     domain="[('location_id', '=', location_id)]",
    #     help='The package containing this quant', readonly=True, ondelete='restrict', check_company=True)
    owner_id = fields.Many2one(
        'res.partner', 'Owner',
        help='This is the owner of the quant', readonly=True, check_company=True)
    quantity = fields.Float(
        'Quantity',
        help='Quantity of products in this quant, in the default unit of measure of the product',
        readonly=True)

    in_date = fields.Datetime('Incoming Date', readonly=True)
    # tracking = fields.Selection(related='product_id.tracking', readonly=True)
    # on_hand = fields.Boolean('On Hand', store=False, search='_search_on_hand')
