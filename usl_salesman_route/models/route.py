from odoo import api, fields, models


class RouteName(models.Model):
    _name = 'salesman.route'
    _description = 'Routes'

    def name_get(self):
        # name get function for the model executes automatically
        res = []
        for rec in self:
            res.append((rec.id, '%s' % (rec.route_name)))
        return res

    def get_shops(self):
        routes = self.env['salesman.route'].search([])
        shop_list = list()
        for route in routes:
            for shop in route.shops:
                shop_list.append(shop.id)
        return [('shops', 'not in', shop_list)]

    route_name = fields.Char(string='Route Name')
    route_id = fields.Char(string='Route Id')
    shops = fields.Many2many('res.partner', 'shop_and_route_rel', string='Shops')
