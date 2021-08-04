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

class CategoryWiseProductsAPI(http.Controller):
    @main.validate_token
    @http.route('/products_category', auth='none', type='http')
    def fetch_all_category(self, **payload):
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
            usr_default_loc = usr.context_default_warehouse_id.lot_stock_id.id

            categories = request.env['product.category'].sudo().search([], limit=limit, offset=offset)
            product_list = list()

            # stock_num = request.env['stock.quant'].search([('location_id', '=', 54)])
            # stock_products_ids = list()
            # for item in stock_num:
            #     stock_products_ids.append(item.product_id.product_tmpl_id.id)
            # print(stock_num, stock_products_ids)

            for category in categories:
                data = {}
                data['category_id'] = category.id
                data['category_name'] = category.complete_name

                products = request.env['product.template'].sudo().search([('categ_id', '=', category.id), ('tracking', '=', 'none')])
                product_in_categ = list()
                for product in products:
                    stock_available = 0
                    stocks = request.env['stock.quant'].search([('product_id', '=', product.product_variant_id.id), ('location_id', '=', usr_default_loc)])
                    # print('stocks = ',stocks, p_id)
# STOCK CALCULATED WITHOUT RESERVE QUANTITY
                    # if stocks:
                    #     for stock in stocks:
                    #         # print('stock = ',stock.location_id.usage)
                    #         if stock.location_id.usage == 'internal':
                    #             stock_available += stock.quantity
# STOCK calculated including reserve quantity
                    if stocks:
                        stock_qty = 0
                        stock_resrv = 0
                        for stock in stocks:
                            stock_qty += stock.quantity
                            stock_resrv += stock.reserved_quantity
                        print('stocck_qty = ', stock_qty, stock_resrv)
                        stock_available = stock_qty - stock_resrv

                    vals = {
                        'id' : product.product_variant_id.id,
                        'product_name' : product.name,
                        'product_unit' : product.uom_id.name,
                        'stock_available' :stock_available,
                        'product_price' : product.list_price,
                        'category_id' : category.id,
                        'category_name' : category.complete_name,
                        'product_image' : str(product.product_variant_id.image_1920),
                    }
                    product_in_categ.append(vals)
                data['products'] = product_in_categ
                product_list.append(data)
            response = dict()
            response['success'] = True
            response['message'] = ''
            response['products'] = product_list
            return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=200)
        except AccessError as e:
            return invalid_response("Access error", "Error: %s" % e.name)