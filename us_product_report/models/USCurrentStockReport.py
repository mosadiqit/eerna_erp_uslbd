import xlsxwriter
import base64
from odoo import fields, models, api
from io import BytesIO
from datetime import datetime
from pytz import timezone
import pytz

class USCurrentStockReport(models.Model):
    _name = "us.report.current.stock"

    product_ids = fields.Many2many('product.product', 'us_report_current_stock_product_rel', 'us_report_current_stock_id',
                                   'product_id', 'Products')
    group_ids = fields.Many2many('product.group', 'us_report_current_stock_group_rel', 'us_report_current_stock_id',
                                 'group_id', 'Group')
    brand_ids = fields.Many2many('product.brand', 'us_report_current_stock_brand_rel', 'us_report_current_stock_id',
                                 'brand_id', 'Brand')
    model_ids = fields.Many2many('product.model', 'us_report_current_stock_model_rel', 'us_report_current_stock_id',
                                 'model_id', 'Model')
    branch_ids = fields.Many2many('res.branch', 'us_report_current_stock_branch_rel', 'us_report_current_stock_id',
                                    'branch_id', 'Branch')
    location_ids = fields.Many2many('stock.location', 'us_report_current_stock_location_rel', 'us_report_current_stock_id',
                                    'location_id', 'Location')

    def get_current_stock_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'product_ids': self.product_ids.id,
                'group_ids': self.group_ids.id,
                'brand_ids': self.brand_ids.id,
                'model_ids': self.model_ids.id,
                'branch_ids': self.branch_ids.id,
                'location_ids': self.location_ids.id,
            },
        }

        return self.env.ref('us_product_report.product_current_stock_report').report_action(
            self, data=data)


class CurrentStockReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.us_product_report.product_current_stock_report_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        product_ids = data['form']['product_ids']
        group_ids = data['form']['group_ids']
        brand_ids = data['form']['brand_ids']
        model_ids = data['form']['model_ids']
        branch_ids = data['form']['branch_ids']
        location_ids = data['form']['location_ids']

        query = """
                    select sq.product_id, pt.name as product_name, pg.name as product_group_name, pm.name as product_model_name, sum(sq.quantity) as sale_qant, sl.complete_name as location_name
                        from stock_quant sq
                        inner join product_product as pp on pp.id = sq.product_id
                        inner join product_template as pt on pp.product_tmpl_id = pt.id
                        inner join stock_location sl on sl.id = sq.location_id
                        left join product_group as pg on pg.id = sq.product_group_id
                        left join product_model as pm on pm.id = pt.product_model_id
                        where sl.name = 'Stock' and sl.usage = 'internal' """

        if product_ids:
            query += """ 
                     and sq.product_id = {}
                    """.format(product_ids)
        if group_ids:
            query += """ 
                     and sq.product_group_id = {}
                    """.format(group_ids)
        if brand_ids:
            query += """ 
                     and sq.brand_id = {}
                    """.format(brand_ids)
        if model_ids:
            query += """ 
                     and sq.product_model_id = {}
                    """.format(model_ids)
        if branch_ids:
            query += """ 
                     and sl.branch_id = {}
                    """.format(branch_ids)
        if location_ids:
            query += """ 
                     and sq.location_id = {}
                    """.format(location_ids)

        query += " group by sl.complete_name, sq.product_id, pt.name, pg.name, pm.name"

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()

        current_stock = dict()

        for collection in query_result:
            if collection[5] not in current_stock.keys():
                current_stock[collection[5]] = dict()
            if collection[2] in current_stock[collection[5]].keys():
                current_stock[collection[5]][collection[2]].append(collection)
            else:
                current_stock[collection[5]][collection[2]] = list()
                current_stock[collection[5]][collection[2]].append(collection)

        return {
            'group_id': group_ids,
            'location_id': location_ids,
            'current_stocks': current_stock,
            'username': self.env.user.name,
        }

