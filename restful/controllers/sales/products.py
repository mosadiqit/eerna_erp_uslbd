from odoo.addons.restful.common import invalid_response, valid_response
from odoo.exceptions import AccessError
from odoo.http import request, Response
import werkzeug.wrappers
from json import dumps
from odoo import http
from .. import main
import datetime
import base64
import json


# For Serializing the create dates
def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

class ProductsAPI(http.Controller):
    @main.validate_token
    @http.route('/products', auth='none', type='http')
    def fetch_all_products(self, **payload):
        try:
            page_no = payload.get('page_no')  # '5'
            if page_no:
                page_no = int(page_no)

            limit = payload.get('limit')
            if limit:
                limit = int(limit)

            offset = 0
            if page_no and limit:
                offset = page_no * limit
            usr = request.env.user
            usr_location_id = usr.context_default_warehouse_id.lot_stock_id.id

            all_products = request.env['product.product'].search([('tracking', '=', 'none')], offset=offset, limit=limit)
            count = len(all_products)
            data = []
            for item in all_products:
                # print(item)
                p_id = item.id
                p_name = item.product_tmpl_id.name if item.product_tmpl_id.name else ""
                p_unit = item.product_tmpl_id.uom_id.name if item.product_tmpl_id.uom_id.name else ""
                p_price = item.product_tmpl_id.list_price
                p_cat_id = item.product_tmpl_id.categ_id.id
                p_cat_name = item.product_tmpl_id.categ_id.name if item.product_tmpl_id.categ_id.name else ""
                p_image = str(item.image_1920) if item.image_1920 else ""
                stock_available = 0
                stocks = request.env['stock.quant'].search([('product_id', '=', p_id), ('location_id', '=', usr_location_id)])

# quantity calculated without Reverse_quantity
#                 if stocks:
#                     for stock in stocks:
#                         if stock.location_id.usage == 'internal':
#                             stock_available += stock.quantity

# quantitu calculated without Reverse_quantity
                if stocks:
                    stock_qty = 0
                    stock_resrv = 0
                    for stock in stocks:
                        stock_qty += stock.quantity
                        stock_resrv += stock.reserved_quantity
                    # print('stocck_qty = ', stock_qty, stock_resrv)
                    stock_available = stock_qty - stock_resrv
                vals = {
                    'id': p_id,
                    'product_name': p_name,
                    'product_unit' : p_unit,
                    'stock_available': stock_available,
                    'product_price': p_price,
                    'product_category_id' : p_cat_id,
                    'product_category_name' : p_cat_name,
                    'product_image': p_image
                }
                data.append(vals)
            response = dict()
            response['count'] = count
            response['success'] = True
            response['message'] = ""
            response['products'] = data
            return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=200)

        except AccessError as e:
            return invalid_response("Access error", "Error: %s" % e.name)

