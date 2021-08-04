from odoo import api, fields, models
import datetime


class RouteDistributions(models.Model):
    _name = 'salesman.route_distributions'
    _description = 'RouteDistributions'

    route_distribution_date = fields.Date(string="Date", default=datetime.datetime.now())
    route_distribution_line = fields.One2many('salesman.route_distributions_line', 'route_distribution')


class RouteDistributionsLine(models.Model):
    _name = 'salesman.route_distributions_line'
    _description = 'RouteDistributionsLine'

    @api.onchange('routes')
    def _shop_ids(self):
        print(self)
        route = self.env['salesman.route'].search([('id', 'in', self.routes.ids)])
        # print(routes.shops)
        shop_list = list()
        for shop in route.shops:
            shop_list.append(shop.id)
        # return [('id', 'in', shop_list)]

        for rec in self:
            print(rec.routes)
            if rec.routes:
                rec.shops = shop_list
            else:
                rec.shops = [(5, 0, 0)]
        # return {'domain': {'shops': [('id', 'in', shop_list)]}}

    salesman = fields.Many2one('hr.employee', string='Sales Man')
    routes = fields.Many2many('salesman.route', 'salesman_route_and_route_dst_rel', stering='Routes')
    routes_ids = fields.Char(related='routes.route_id')
    shops = fields.Many2many('res.partner', 'shop_and_rout_dst_rel', string='Shops'
                             )
    route_distribution = fields.Many2one('salesman.route_distributions', )
