from odoo import api, fields, models, _


class CurrentStockWithSerial(models.TransientModel):
    _name = 'current.stock.serial'
    # _rec_name = 'name'
    _description = 'Model for all stock information with serial no'

    product_ids = fields.Many2many('product.product',string="Product")
    group_ids = fields.Many2many('product.group','current_stock_pgroup_rel',string='Group')
    brand_ids = fields.Many2many('product.brand','current_stock_pbrand_rel',string='Brand')
    categ_ids = fields.Many2many('product.category','current_stock_pcateg_rel',string='Category')
    location_ids = fields.Many2many('stock.location','current_stock_plocation_rel',string="Location")

    def get_serial(self, DATA):
        return DATA.split(',')

    @api.onchange('location_ids')
    def _get_user_location(self):
        location_id = self.env['stock.location'].search([('branch_id', '=', self.env.user.branch_ids.ids)])
        if self.user_has_groups('stock.group_stock_manager'):
            m_location_id = self.env['stock.location'].search(
                [('usage', '=', 'internal'), ('branch_id', '=', self.env.user.branch_ids.ids)])
            # return [('id','in',m_location_id.ids)]
            return {'domain': {'location_ids': [('id', 'in', m_location_id.ids)]}}
            # self.location_ids = m_location_id
        elif self.user_has_groups('stock.group_stock_user'):
            return {'domain': {'location_ids': [('id', 'in', location_id.ids)]}}

    def get_report(self):
        data = self.read()[0]
        product_ids = data['product_ids']
        group_ids = data['group_ids']
        brand_ids = data['brand_ids']
        categ_ids = data['categ_ids']
        location_ids = data['location_ids']
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'product_ids':product_ids,'group_ids':group_ids,'brand_ids':brand_ids,'categ_ids':categ_ids,'location_ids':location_ids
            },
        }

        return self.env.ref('inventory_report.current_stock_serial_report').report_action(self, data=data)


class CurrentStockSerialReport(models.AbstractModel):
    _name = 'report.inventory_report.current_stock_serial_report_view'


    def check_reserved_or_not(self,serial):
        stock_quant_check = self.env['stock.quant'].search([('lot_id','in',self.env['stock.production.lot'].search([('name','in',serial)]).ids),('reserved_quantity','=',1)])
        lot_id_list = list()
        for val in stock_quant_check:
            lot_id_list.append(val.lot_id.id)
        stock_production_lot_val = self.env['stock.production.lot'].search([('id','in',lot_id_list)])
        lot_name = list()
        for name in stock_production_lot_val:
            lot_name.append(name.display_name)
        return lot_name


    def _get_report_values(self, docids, data=None):
        product_ids = data['form']['product_ids']
        group_ids = data['form']['group_ids']
        brand_ids = data['form']['brand_ids']
        categ_ids = data['form']['categ_ids']
        location_ids = data['form']['location_ids']


        where_product_ids = "1=1"
        where_group_ids = "1=1"
        where_brand_ids = "1=1"
        where_categ_ids = "1=1"
        where_location_ids = "1=1"

        if product_ids:
            where_product_ids = "pp.id in %s" % str(tuple(product_ids)).replace(',)', ')')
        if group_ids:
            where_group_ids = "pgroup.id in %s" % str(tuple(group_ids)).replace(',)', ')')
        if brand_ids:
            where_brand_ids = "pbrand.id in %s" % str(tuple(brand_ids)).replace(',)', ')')
        if categ_ids:
            where_categ_ids = "categ.id in %s" % str(tuple(categ_ids)).replace(',)', ')')
        if location_ids:
            where_location_ids = "sl.id in %s" % str(tuple(location_ids)).replace(',)', ')')

        query = """select pt.name as product, sl.complete_name, pgroup.name as group, pbrand.name as brand, categ.name as category,  sum(sq.quantity) as quantity,string_agg(spl.name,',') as serial_num
                    from stock_quant sq 
                        left join product_product pp on pp.id = sq.product_id
                        left join product_template pt on pt.id = pp.product_tmpl_id
                        left join stock_production_lot spl on spl.id = sq.lot_id
                        left join stock_location sl on sl.id = sq.location_id
                        LEFT JOIN product_category categ on categ.id=pt.categ_id
                        LEFT JOIN product_group pgroup on pgroup.id=pt.group_id
                        LEFT JOIN product_brand pbrand on pbrand.id=pt.brand_id
                        LEFT JOIN product_model pmodel on pmodel.id=pt.product_model_id
                        where sq.quantity > 0 and {} and {} and {} and {} and {}
                        group by pt.name,sq.quantity,categ.name,pbrand.name,pgroup.name, sl.complete_name""".format(where_location_ids,where_product_ids,where_group_ids,where_brand_ids,where_categ_ids)
        print(query)
        self._cr.execute(query=query)
        current_stock = self._cr.fetchall()
        stock_serial_dict = dict()
        stock_location_dict = dict()
        stock_group_dict = dict()
        stock_category_dict = dict()

        # for res in current_stock:
        #     val = {
        #         'product':res[0],
        #         'stock':res[1],
        #         'group':res[2],
        #         'brand':res[3],
        #         'category':res[4],
        #         'quantity':res[5],
        #         'serial':str(res[6]).split(',') if res[6] else None
        #     }
        #     stock_serial_dict.append(val)

        for res in current_stock:
            if res[1] not in stock_serial_dict.keys():
                stock_serial_dict[res[1]] = dict()
            if res[2] not in stock_serial_dict[res[1]].keys():
                stock_serial_dict[res[1]][res[2]] = dict()
            if res[3] not in stock_serial_dict[res[1]][res[2]].keys():
                stock_serial_dict[res[1]][res[2]][res[3]] = dict()
            if res[4] not in stock_serial_dict[res[1]][res[2]][res[3]].keys():
                stock_serial_dict[res[1]][res[2]][res[3]][res[4]] = list()
                stock_serial_dict[res[1]][res[2]][res[3]][res[4]].append(list(res))
            else:
                # stock_serial_dict[res[1]][res[2]][res[3]][res[4]] = list()
                stock_serial_dict[res[1]][res[2]][res[3]][res[4]].append(list(res))


        for val in stock_serial_dict.keys():
            for next_val in stock_serial_dict[val]:
                for pre_val in stock_serial_dict[val][next_val]:
                    for last_val in stock_serial_dict[val][next_val][pre_val]:
                        for final in stock_serial_dict[val][next_val][pre_val][last_val]:
                            if final[6] is not None:
                                final[6] = final[6].split(',')
                                # final.append(self.check_reserved_or_not(final[6]))
                            else:
                                final[6] = None
                                # final.append(None)
            print('Hello..')

        print(stock_serial_dict)
        print('hello_world')
        return {
            'value': stock_serial_dict
        }