from odoo import http
from odoo.http import request, Response
from odoo.exceptions import AccessError
from json import dumps
from .. import main
import datetime
import json

# For Serializing the create dates
def mytimeconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

class ProductReplaceApis(http.Controller):
    @main.validate_token
    @http.route('/replace_product_list', auth='none', type='http')
    def fetch_all_replaces(self, **payload):
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
            replaces = request.env['product.replace'].search([], limit=limit, offset=offset)
            replace_list = []
            for replace in replaces:
                name = replace.name
                status = replace.state
                date = json.dumps(replace.create_date, default=mytimeconverter)
                store = replace.partner_id.name if replace.partner_id.name else ""
                products = replace.replace_lines
                product_list = []
                for product in products:
                    p_id = product.product_id.id
                    p_name = product.product_id.name if product.product_id.name else ""
                    p_qty = product.qty_replace
                    p_img = str(product.product_id.image_1920) if product.product_id.image_1920 else ""
                    vals = {
                        'id' : p_id,
                        'product_name' : p_name,
                        'quantity' : p_qty,
                        'product_image' : p_img,
                    }
                    product_list.append(vals)
                data = {
                    'name' : name,
                    'status' : status,
                    'datetime' : date,
                    'store' : store,
                    'products' : product_list,
                }
                replace_list.append(data)

            response = {
                'success' : True,
                'message' : "",
            }
            response['replaces'] = replace_list

            return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=200)

        except AccessError as e:
            return invalid_response("Access error", "Error: %s" % e.name)